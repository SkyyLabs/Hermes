import json
from io import BytesIO

import pytest

from local_mac_agent.chat.llm import OllamaLocalLLM, build_local_llm
from local_mac_agent.settings import ModelSettings


class _Response:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = BytesIO(json.dumps(payload).encode("utf-8"))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def read(self) -> bytes:
        return self.payload.read()


def test_ollama_llm_posts_current_message_after_history(monkeypatch) -> None:
    requests = []

    def fake_urlopen(request, timeout):
        requests.append((request, timeout))
        return _Response({"message": {"content": "Ready."}})

    monkeypatch.setattr("local_mac_agent.chat.llm.urlopen", fake_urlopen)
    llm = OllamaLocalLLM("gemma3")
    context = {
        "memory": {"core.md": "local"},
        "prompt": "Local context",
        "recent_turns": [
            {
                "timestamp": "2026-05-21T12:00:00+00:00",
                "conversation_id": "default",
                "role": "user",
                "content": "hello",
            }
        ],
    }

    response = llm.respond("hello", context)

    payload = json.loads(requests[0][0].data.decode("utf-8"))
    assert response == "Ready."
    assert requests[0][0].full_url == "http://127.0.0.1:11434/api/chat"
    assert requests[0][1] == 120
    assert payload["model"] == "gemma3"
    assert payload["stream"] is False
    assert payload["messages"][0] == {"role": "system", "content": "Local context"}
    assert payload["messages"][1:] == [{"role": "user", "content": "hello"}]


def test_ollama_llm_keeps_prior_history_before_current_message(monkeypatch) -> None:
    requests = []

    def fake_urlopen(request, timeout):
        requests.append(request)
        return _Response({"message": {"content": "Five."}})

    monkeypatch.setattr("local_mac_agent.chat.llm.urlopen", fake_urlopen)
    llm = OllamaLocalLLM("gemma3")
    context = {
        "memory": {},
        "prompt": "Local context",
        "recent_turns": [
            {
                "timestamp": "2026-05-21T12:00:00+00:00",
                "conversation_id": "default",
                "role": "user",
                "content": "hows life",
            },
            {
                "timestamp": "2026-05-21T12:00:01+00:00",
                "conversation_id": "default",
                "role": "assistant",
                "content": "Doing well.",
            },
            {
                "timestamp": "2026-05-21T12:00:02+00:00",
                "conversation_id": "default",
                "role": "user",
                "content": "whats 3 + 2",
            },
        ],
    }

    llm.respond("whats 3 + 2", context)

    payload = json.loads(requests[0].data.decode("utf-8"))
    assert payload["messages"][1:] == [
        {"role": "user", "content": "hows life"},
        {"role": "assistant", "content": "Doing well."},
        {"role": "user", "content": "whats 3 + 2"},
    ]


def test_ollama_local_only_rejects_remote_base_url() -> None:
    with pytest.raises(ValueError):
        OllamaLocalLLM("gemma3", "https://example.com")


def test_ollama_local_only_rejects_cloud_model_name() -> None:
    with pytest.raises(ValueError):
        OllamaLocalLLM("gpt-oss:120b-cloud")


def test_model_settings_require_ollama_provider() -> None:
    assert isinstance(build_local_llm(ModelSettings()), OllamaLocalLLM)
    with pytest.raises(ValueError, match="No LLM configured"):
        build_local_llm(ModelSettings(provider="placeholder"))
