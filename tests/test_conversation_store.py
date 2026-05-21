from pathlib import Path

from local_mac_agent.chat.conversation_store import ConversationStore


def test_append_turn_and_get_recent_turns(tmp_path: Path) -> None:
    store = ConversationStore(tmp_path / "state" / "conversations.jsonl")

    store.append_turn("default", "user", "hello", "2026-05-21T12:00:00+00:00")
    store.append_turn("other", "user", "skip", "2026-05-21T12:00:01+00:00")
    store.append_turn("default", "assistant", "hi", "2026-05-21T12:00:02+00:00")

    turns = store.get_recent_turns("default")

    assert [turn["role"] for turn in turns] == ["user", "assistant"]
    assert [turn["content"] for turn in turns] == ["hello", "hi"]


def test_recent_turn_limit_preserves_order(tmp_path: Path) -> None:
    store = ConversationStore(tmp_path / "conversations.jsonl")
    for index in range(3):
        store.append_turn("default", "user", f"message {index}")

    turns = store.get_recent_turns("default", limit=2)

    assert [turn["content"] for turn in turns] == ["message 1", "message 2"]
