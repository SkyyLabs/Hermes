from __future__ import annotations

import subprocess
from array import array
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from time import monotonic
from typing import Any, Protocol
from wave import open as open_wave

from local_mac_agent.chat.service import DEFAULT_CONVERSATION_ID
from local_mac_agent.settings import VoiceSettings


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


@dataclass(frozen=True)
class VoiceTurn:
    transcript: str
    response: str


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


class VoiceService:
    """Coordinate wake detection, STT, chat routing, TTS, and session timing."""

    def __init__(
        self,
        chat_service: ChatResponder,
        settings: VoiceSettings,
        microphone: Microphone | None = None,
        wake_detector: WakeWordDetector | None = None,
        stt: SpeechToText | None = None,
        tts: TextToSpeech | None = None,
        clock=monotonic,
    ) -> None:
        self.chat_service = chat_service
        self.settings = settings
        self.microphone = microphone or SoundDeviceMicrophone(settings)
        self.wake_detector = wake_detector
        self.stt = stt or WhisperSpeechToText(settings)
        self.tts = tts or MacOSTextToSpeech(settings)
        self.clock = clock

    def process_transcript(
        self, transcript: str, conversation_id: str = DEFAULT_CONVERSATION_ID
    ) -> str:
        response = self.chat_service.chat(transcript, conversation_id=conversation_id)
        self.tts.speak(response)
        return response

    def listen_forever(self, conversation_id: str = DEFAULT_CONVERSATION_ID) -> None:
        detector = self.wake_detector or OpenWakeWordDetector(self.settings)
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
            if not _has_speech(frame, self.settings.speech_threshold):
                continue
            turn = self._process_audio(
                _capture_utterance(frame, frames, self.settings),
                conversation_id,
            )
            if turn.transcript:
                active_until = self.clock() + self.settings.active_listening_seconds

    def _process_audio(self, audio: bytes, conversation_id: str) -> VoiceTurn:
        transcript = self.stt.transcribe(audio)
        response = self.process_transcript(transcript, conversation_id)
        return VoiceTurn(transcript=transcript, response=response)


def _capture_utterance(first_frame: bytes, frames: Iterator[bytes], settings: VoiceSettings) -> bytes:
    captured = [first_frame]
    frame_seconds = settings.frame_ms / 1000
    silence = 0.0
    elapsed = frame_seconds
    for frame in frames:
        captured.append(frame)
        elapsed += frame_seconds
        if _has_speech(frame, settings.speech_threshold):
            silence = 0.0
        else:
            silence += frame_seconds
        if silence >= settings.utterance_silence_seconds:
            break
        if elapsed >= settings.max_utterance_seconds:
            break
    return b"".join(captured)


def _has_speech(audio: bytes, threshold: int) -> bool:
    samples = array("h")
    samples.frombytes(audio)
    if not samples:
        return False
    return max(abs(sample) for sample in samples) >= threshold


def _write_wav(path: str | Path, audio: bytes, sample_rate: int) -> None:
    with open_wave(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(audio)
