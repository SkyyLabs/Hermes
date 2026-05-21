from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict


class ConversationTurn(TypedDict):
    timestamp: str
    conversation_id: str
    role: str
    content: str


class ConversationStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def append_turn(
        self,
        conversation_id: str,
        role: str,
        content: str,
        timestamp: str | None = None,
    ) -> ConversationTurn:
        turn: ConversationTurn = {
            "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(turn, sort_keys=True, separators=(",", ":")))
            handle.write("\n")
        return turn

    def get_recent_turns(
        self, conversation_id: str, limit: int = 10
    ) -> list[ConversationTurn]:
        if limit <= 0 or not self.path.exists():
            return []

        turns: list[ConversationTurn] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            turn = json.loads(line)
            if turn.get("conversation_id") == conversation_id:
                turns.append(turn)
        return turns[-limit:]
