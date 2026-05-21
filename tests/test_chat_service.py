import json
from pathlib import Path

from local_mac_agent.chat.context import CORE_MEMORY_FILES
from local_mac_agent.chat.llm import DefaultLocalLLM
from local_mac_agent.chat.service import ChatService
from local_mac_agent.paths import RuntimePaths


def _create_paths(tmp_path: Path) -> RuntimePaths:
    paths = RuntimePaths(tmp_path)
    paths.ensure_directories()
    for file_name in CORE_MEMORY_FILES:
        (paths.memory / file_name).write_text(f"{file_name} content", encoding="utf-8")
    return paths


def test_chat_service_persists_turns_logs_and_context_delta(tmp_path: Path) -> None:
    paths = _create_paths(tmp_path)
    service = ChatService(paths, llm=DefaultLocalLLM())

    response = service.chat("hello")

    turns = service.conversation_store.get_recent_turns("default")
    log_record = json.loads((paths.logs / "events.jsonl").read_text(encoding="utf-8"))
    delta_record = json.loads(
        (paths.state / "context_deltas.jsonl").read_text(encoding="utf-8")
    )
    assert response.startswith("Local placeholder response:")
    assert [turn["role"] for turn in turns] == ["user", "assistant"]
    assert turns[0]["content"] == "hello"
    assert turns[1]["content"] == response
    assert log_record["event"] == "chat_turn"
    assert delta_record["source"] == "chat_turn"


def test_default_chat_service_stays_local(tmp_path: Path, monkeypatch) -> None:
    paths = _create_paths(tmp_path)

    def fail(*args, **kwargs):
        raise AssertionError("cloud or network access was attempted")

    monkeypatch.setattr("socket.create_connection", fail)

    response = ChatService(paths, llm=DefaultLocalLLM()).chat("stay local")

    assert "stay local" in response
