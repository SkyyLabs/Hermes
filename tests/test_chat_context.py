import json
from pathlib import Path

from local_mac_agent.chat.context import CORE_MEMORY_FILES, ChatContextBuilder
from local_mac_agent.chat.conversation_store import ConversationStore


def _write_memory_files(memory_dir: Path) -> None:
    memory_dir.mkdir()
    for file_name in CORE_MEMORY_FILES:
        (memory_dir / file_name).write_text(f"{file_name} memory", encoding="utf-8")


def test_context_loads_core_memory_and_writes_delta(tmp_path: Path) -> None:
    memory_dir = tmp_path / "memory"
    _write_memory_files(memory_dir)
    store = ConversationStore(tmp_path / "state" / "conversations.jsonl")
    store.append_turn("default", "user", "hello")
    builder = ChatContextBuilder(
        memory_dir,
        store,
        tmp_path / "state" / "context_deltas.jsonl",
    )

    context = builder.build("default")
    delta = builder.write_delta("default", context)

    assert "core.md memory" in context["prompt"]
    assert context["memory"]["core.md"] == "core.md memory"
    assert context["recent_turns"][0]["content"] == "hello"
    persisted = json.loads(builder.context_delta_path.read_text(encoding="utf-8"))
    assert persisted["conversation_id"] == "default"
    assert persisted["recent_turn_count"] == 1
    assert delta["memory_files"] == list(CORE_MEMORY_FILES)
