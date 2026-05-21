from array import array

from local_mac_agent.main import HELP_TEXT
from local_mac_agent.settings import VoiceSettings
from local_mac_agent.voice.service import VoiceService, _capture_utterance


def _frame(value: int, samples: int = 16) -> bytes:
    return array("h", [value] * samples).tobytes()


class _Chat:
    def __init__(self) -> None:
        self.turns = []

    def chat(self, message: str, conversation_id: str = "default") -> str:
        self.turns.append((message, conversation_id))
        return f"reply:{message}"


class _TTS:
    def __init__(self) -> None:
        self.spoken = []

    def speak(self, text: str) -> None:
        self.spoken.append(text)


class _STT:
    def __init__(self, transcripts: list[str]) -> None:
        self.transcripts = transcripts
        self.audio = []

    def transcribe(self, audio: bytes) -> str:
        self.audio.append(audio)
        return self.transcripts.pop(0)


class _Wake:
    def __init__(self, values: list[bool]) -> None:
        self.values = values
        self.seen = []

    def detected(self, audio: bytes) -> bool:
        self.seen.append(audio)
        return self.values.pop(0) if self.values else False


class _Microphone:
    def __init__(self, frames: list[bytes]) -> None:
        self._frames = frames
        self.accessed = False

    def frames(self):
        self.accessed = True
        yield from self._frames


class _Clock:
    def __init__(self, values: list[float]) -> None:
        self.values = values

    def __call__(self) -> float:
        return self.values.pop(0)


def test_transcript_routes_to_chat_and_tts_with_conversation_id() -> None:
    chat = _Chat()
    tts = _TTS()
    service = VoiceService(chat, VoiceSettings(), tts=tts)

    response = service.process_transcript("hello", conversation_id="voice-1")

    assert response == "reply:hello"
    assert chat.turns == [("hello", "voice-1")]
    assert tts.spoken == ["reply:hello"]


def test_capture_utterance_stops_after_trailing_silence() -> None:
    settings = VoiceSettings(frame_ms=100, utterance_silence_seconds=0.2)
    audio = _capture_utterance(
        _frame(1000),
        iter([_frame(900), _frame(0), _frame(0), _frame(800)]),
        settings,
    )

    assert audio == b"".join([_frame(1000), _frame(900), _frame(0), _frame(0)])


def test_listener_uses_microphone_wake_stt_and_active_follow_up() -> None:
    settings = VoiceSettings(
        frame_ms=100,
        utterance_silence_seconds=0.1,
        active_listening_seconds=3.0,
    )
    microphone = _Microphone(
        [
            _frame(0),
            _frame(0),
            _frame(1200),
            _frame(0),
            _frame(1100),
            _frame(0),
        ]
    )
    wake = _Wake([True])
    stt = _STT(["first", "follow up"])
    chat = _Chat()
    tts = _TTS()
    service = VoiceService(
        chat,
        settings,
        microphone=microphone,
        wake_detector=wake,
        stt=stt,
        tts=tts,
        clock=_Clock([0.0, 0.1, 0.2, 0.3, 0.4, 0.5]),
    )

    service.listen_forever(conversation_id="voice-2")

    assert microphone.accessed is True
    assert len(wake.seen) == 1
    assert len(stt.audio) == 2
    assert chat.turns == [("first", "voice-2"), ("follow up", "voice-2")]
    assert tts.spoken == ["reply:first", "reply:follow up"]


def test_listener_returns_to_wake_after_active_silence_timeout() -> None:
    settings = VoiceSettings(active_listening_seconds=1.0)
    microphone = _Microphone([_frame(0), _frame(0), _frame(0)])
    wake = _Wake([True, False])
    service = VoiceService(
        _Chat(),
        settings,
        microphone=microphone,
        wake_detector=wake,
        stt=_STT([]),
        tts=_TTS(),
        clock=_Clock([0.0, 2.0]),
    )

    service.listen_forever()

    assert len(wake.seen) == 2


def test_cli_help_keeps_chat_classify_and_voice_commands() -> None:
    assert "chat <message>" in HELP_TEXT
    assert "voice transcript <text>" in HELP_TEXT
    assert "voice listen" in HELP_TEXT
    assert "classify <action>" in HELP_TEXT
