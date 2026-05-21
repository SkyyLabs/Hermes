from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict

from local_mac_agent.chat.conversation_store import ConversationStore, ConversationTurn


CORE_MEMORY_FILES = (
    "core.md",
    "projects.md",
    "preferences.md",
    "working_context.md",
    "memory_map.md",
)
PLACEHOLDER_REPLY_PREFIX = "Local placeholder response:"
MEMORY_DRAFT_MARKERS = ("Memory Entries", "`core.md`", "`working_context.md`")


class ChatContext(TypedDict):
    memory: dict[str, str]
    recent_turns: list[ConversationTurn]
    prompt: str


class ChatContextBuilder:
    def __init__(
        self,
        memory_dir: Path,
        conversation_store: ConversationStore,
        context_delta_path: Path,
    ) -> None:
        self.memory_dir = memory_dir
        self.conversation_store = conversation_store
        self.context_delta_path = context_delta_path

    def build(self, conversation_id: str, limit: int = 10) -> ChatContext:
        memory = {
            file_name: (self.memory_dir / file_name).read_text(encoding="utf-8")
            for file_name in CORE_MEMORY_FILES
        }
        recent_turns = [
            turn
            for turn in self.conversation_store.get_recent_turns(conversation_id, limit)
            if not _is_legacy_non_chat_assistant_turn(turn)
        ]
        memory_sections = "\n\n".join(
            f"[{file_name}]\n{content.strip()}" for file_name, content in memory.items()
        )
        prompt = f"""You are LocalMacAgent, a local chat assistant.
Answer the final user message directly and conversationally.
The memory files below are background context only. Do not draft, rewrite,
analyze, or update memory files unless the user explicitly asks for that.
Do not describe system internals or roadmap phases unless the user asks.

Memory context:
{memory_sections}""".strip()
        return {"memory": memory, "recent_turns": recent_turns, "prompt": prompt}

    def write_delta(self, conversation_id: str, context: ChatContext) -> dict[str, object]:
        delta: dict[str, object] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "conversation_id": conversation_id,
            "source": "chat_turn",
            "memory_files": list(context["memory"].keys()),
            "recent_turn_count": len(context["recent_turns"]),
        }
        self.context_delta_path.parent.mkdir(parents=True, exist_ok=True)
        with self.context_delta_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(delta, sort_keys=True, separators=(",", ":")))
            handle.write("\n")
        return delta


def _is_legacy_non_chat_assistant_turn(turn: ConversationTurn) -> bool:
    if turn["role"] != "assistant":
        return False
    content = turn["content"]
    if content.startswith(PLACEHOLDER_REPLY_PREFIX):
        return True
    return all(marker in content for marker in MEMORY_DRAFT_MARKERS)
