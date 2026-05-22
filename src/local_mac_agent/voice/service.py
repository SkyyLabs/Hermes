from __future__ import annotations

import subprocess
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from time import monotonic
from typing import Any, Protocol
from wave import open as open_wave

from local_mac_agent.chat.service import DEFAULT_CONVERSATION_ID
from local_mac_agent.settings import VoiceSettings
from local_mac_agent.timing import elapsed_ms, format_latency_report


class ChatResponder(Protocol):
    def chat(self, message: str, conversation_id: str = DEFAULT_CONVERSATION_ID) -> str: ...


class Microphone(Protocol):
    def frames(self) -> Iterator[bytes]: ...


class SpeechToText(Protocol):
    def transcribe(self, audio: bytes) -> str: ...


class TextToSpeech(Protocol):
    def speak(self, text: str) -> None: ...


class WakeWordDetector(Protocol):
    def detected(self, audio: bytes) -> bool: ...


class VoiceActivityDetector(Protocol):
    def contains_speech(self, audio: bytes) -> bool: ...


@dataclass(frozen=True)
class VoiceTurn:
    transcript: str
    response: str
    timings: dict[str, float]


class SoundDeviceMicrophone:
    """Real macOS microphone capture boundary backed by sounddevice."""

    def __init__(self, settings: VoiceSettings) -> None:
        self.sample_rate = settings.sample_rate
        self.frame_samples = int(settings.sample_rate * settings.frame_ms / 1000)

    def frames(self) -> Iterator[bytes]:
        try:
            import sounddevice
        except ImportError as exc:
            raise RuntimeError("Voice listening requires the sounddevice package.") from exc

        try:
            with sounddevice.RawInputStream(
                samplerate=self.sample_rate,
                blocksize=self.frame_samples,
                channels=1,
                dtype="int16",
            ) as stream:
                while True:
                    frame, _ = stream.read(self.frame_samples)
                    yield bytes(frame)
        except sounddevice.PortAudioError as exc:
            raise RuntimeError(
                "Microphone capture failed. Check macOS microphone permission and input device."
            ) from exc


class OpenWakeWordDetector:
    """Wake-word boundary using openWakeWord's built-in Hey Mycroft model."""

    def __init__(self, settings: VoiceSettings) -> None:
        try:
            from openwakeword.model import Model
        except ImportError as exc:
            raise RuntimeError("Wake-word listening requires the openwakeword package.") from exc

        self.wake_word = settings.wake_word
        self.threshold = settings.wake_threshold
        try:
            self.model = Model(
                wakeword_models=[settings.wake_word],
                inference_framework="onnx",
            )
        except Exception as exc:
            raise RuntimeError(
                "Could not load openWakeWord ONNX models. Download the built-in models before listening."
            ) from exc

    def detected(self, audio: bytes) -> bool:
        try:
            import numpy as np
        except ImportError as exc:
            raise RuntimeError("Wake-word listening requires numpy.") from exc

        scores = self.model.predict(np.frombuffer(audio, dtype=np.int16))
        return float(scores.get(self.wake_word, 0.0)) >= self.threshold


class WhisperSpeechToText:
    """Local Whisper STT boundary for captured 16 kHz PCM utterances."""

    def __init__(self, settings: VoiceSettings) -> None:
        self.settings = settings
        self.model = None

    def prepare(self) -> None:
        self._load_model()

    def transcribe(self, audio: bytes) -> str:
        model = self._load_model()
        with NamedTemporaryFile(suffix=".wav") as audio_file:
            _write_wav(audio_file.name, audio, self.settings.sample_rate)
            result = model.transcribe(audio_file.name, fp16=False)
        text = str(result.get("text", "")).strip()
        if not text:
            raise RuntimeError("Whisper did not produce a transcript.")
        return text

    def _load_model(self) -> Any:
        try:
            import whisper
        except ImportError as exc:
            raise RuntimeError("Voice transcription requires the openai-whisper package.") from exc

        if self.model is None:
            self.model = whisper.load_model(self.settings.whisper_model)
        return self.model


class MacOSTextToSpeech:
    """macOS speech output boundary backed by the system `say` command."""

    def __init__(self, settings: VoiceSettings) -> None:
        self.voice = settings.tts_voice
        self.rate = settings.tts_rate

    def speak(self, text: str) -> None:
        command = ["say"]
        if self.voice:
            command.extend(["-v", self.voice])
        if self.rate:
            command.extend(["-r", str(self.rate)])
        command.append(text)
        try:
            subprocess.run(command, check=True)
        except FileNotFoundError as exc:
            raise RuntimeError("macOS TTS requires the system `say` command.") from exc
        except subprocess.CalledProcessError as exc:
            raise RuntimeError("macOS TTS failed.") from exc


class WebRtcVoiceActivityDetector:
    """Local speech/non-speech detector backed by WebRTC VAD."""

    def __init__(self, settings: VoiceSettings) -> None:
        try:
            import webrtcvad
        except ImportError as exc:
            raise RuntimeError(
                "Voice activity detection requires the webrtcvad-wheels package."
            ) from exc

        if settings.vad_frame_ms not in {10, 20, 30}:
            raise ValueError("WebRTC VAD frames must be 10, 20, or 30 ms.")
        self.sample_rate = settings.sample_rate
        self.frame_bytes = int(
            settings.sample_rate * settings.vad_frame_ms / 1000
        ) * 2
        self.vad = webrtcvad.Vad(settings.vad_mode)

    def contains_speech(self, audio: bytes) -> bool:
        frames = []
        for start in range(0, len(audio), self.frame_bytes):
            frame = audio[start : start + self.frame_bytes]
            if len(frame) == self.frame_bytes:
                frames.append(frame)
        return any(self.vad.is_speech(frame, self.sample_rate) for frame in frames)


class VoiceService:
    """Coordinate wake detection, STT, chat routing, TTS, and session timing."""

    def __init__(
        self,
        chat_service: ChatResponder,
        settings: VoiceSettings,
        microphone: Microphone | None = None,
        wake_detector: WakeWordDetector | None = None,
        vad: VoiceActivityDetector | None = None,
        stt: SpeechToText | None = None,
        tts: TextToSpeech | None = None,
        clock=monotonic,
        timing_clock=monotonic,
    ) -> None:
        self.chat_service = chat_service
        self.settings = settings
        self.microphone = microphone or SoundDeviceMicrophone(settings)
        self.wake_detector = wake_detector
        self.vad = vad
        self.stt = stt or WhisperSpeechToText(settings)
        self.tts = tts or MacOSTextToSpeech(settings)
        self.clock = clock
        self.timing_clock = timing_clock

    def process_transcript(
        self, transcript: str, conversation_id: str = DEFAULT_CONVERSATION_ID
    ) -> str:
        return self.process_transcript_turn(transcript, conversation_id).response

    def process_transcript_turn(
        self, transcript: str, conversation_id: str = DEFAULT_CONVERSATION_ID
    ) -> VoiceTurn:
        total_start = self.timing_clock()
        chat_start = self.timing_clock()
        chat_turn = getattr(self.chat_service, "chat_turn", None)
        if chat_turn is None:
            response = self.chat_service.chat(transcript, conversation_id=conversation_id)
            timings = {"chat": elapsed_ms(chat_start, self.timing_clock())}
        else:
            result = chat_turn(transcript, conversation_id=conversation_id)
            response = result.response
            timings = {
                f"chat_{name}": duration for name, duration in result.timings.items()
            }

        tts_start = self.timing_clock()
        self.tts.speak(response)
        timings["tts"] = elapsed_ms(tts_start, self.timing_clock())
        timings["total"] = elapsed_ms(total_start, self.timing_clock())
        return VoiceTurn(transcript=transcript, response=response, timings=timings)

    def listen_forever(self, conversation_id: str = DEFAULT_CONVERSATION_ID) -> None:
        detector = self.wake_detector or OpenWakeWordDetector(self.settings)
        vad = self.vad or WebRtcVoiceActivityDetector(self.settings)
        if isinstance(self.stt, WhisperSpeechToText):
            self.stt.prepare()
        frames = self.microphone.frames()
        active_until: float | None = None
        for frame in frames:
            if active_until is None:
                if detector.detected(frame):
                    active_until = self.clock() + self.settings.active_listening_seconds
                continue
            if self.clock() > active_until:
                active_until = None
                continue
            if not vad.contains_speech(frame):
                continue
            try:
                voice_start = self.timing_clock()
                capture_start = self.timing_clock()
                audio = _capture_utterance(frame, frames, self.settings, vad)
                capture_ms = elapsed_ms(capture_start, self.timing_clock())
                turn = self._process_audio(
                    audio,
                    conversation_id,
                )
            except RuntimeError as exc:
                print(f"\nVoice turn skipped: {exc}")
                active_until = None
                continue
            timings = {
                "capture_utterance": capture_ms,
                **turn.timings,
                "total": elapsed_ms(voice_start, self.timing_clock()),
            }
            print(f"\n{format_latency_report('voice', timings)}")
            if turn.transcript:
                active_until = self.clock() + self.settings.active_listening_seconds

    def _process_audio(self, audio: bytes, conversation_id: str) -> VoiceTurn:
        turn_start = self.timing_clock()
        stt_start = self.timing_clock()
        transcript = self.stt.transcribe(audio)
        stt_ms = elapsed_ms(stt_start, self.timing_clock())
        turn = self.process_transcript_turn(transcript, conversation_id)
        return VoiceTurn(
            transcript=turn.transcript,
            response=turn.response,
            timings={
                "stt": stt_ms,
                **turn.timings,
                "total": elapsed_ms(turn_start, self.timing_clock()),
            },
        )


def _capture_utterance(
    first_frame: bytes,
    frames: Iterator[bytes],
    settings: VoiceSettings,
    vad: VoiceActivityDetector,
) -> bytes:
    captured = [first_frame]
    frame_seconds = settings.frame_ms / 1000
    silence = 0.0
    elapsed = frame_seconds
    for frame in frames:
        captured.append(frame)
        elapsed += frame_seconds
        if vad.contains_speech(frame):
            silence = 0.0
        else:
            silence += frame_seconds
        if silence >= settings.utterance_silence_seconds:
            break
        if elapsed >= settings.max_utterance_seconds:
            break
    return b"".join(captured)


def _write_wav(path: str | Path, audio: bytes, sample_rate: int) -> None:
    with open_wave(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(audio)
