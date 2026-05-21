from __future__ import annotations

from pathlib import Path

from local_mac_agent.chat.context import ChatContextBuilder
from local_mac_agent.chat.conversation_store import ConversationStore
from local_mac_agent.chat.llm import DefaultLocalLLM
from local_mac_agent.logging_utils import write_event
from local_mac_agent.paths import RuntimePaths


DEFAULT_CONVERSATION_ID = "default"


class ChatService:
    def __init__(
        self,
        paths: RuntimePaths,
        llm: DefaultLocalLLM | None = None,
        conversation_store: ConversationStore | None = None,
        context_builder: ChatContextBuilder | None = None,
        log_path: Path | None = None,
    ) -> None:
        self.paths = paths
        self.conversation_store = conversation_store or ConversationStore(
            paths.state / "conversations.jsonl"
        )
        self.context_builder = context_builder or ChatContextBuilder(
            paths.memory,
            self.conversation_store,
            paths.state / "context_deltas.jsonl",
        )
        self.llm = llm or DefaultLocalLLM()
        self.log_path = log_path or paths.logs / "events.jsonl"

    def chat(self, message: str, conversation_id: str = DEFAULT_CONVERSATION_ID) -> str:
        self.conversation_store.append_turn(conversation_id, "user", message)
        context = self.context_builder.build(conversation_id)
        response = self.llm.respond(message, context)
        self.conversation_store.append_turn(conversation_id, "assistant", response)
        write_event(
            self.log_path,
            "chat_turn",
            {
                "conversation_id": conversation_id,
                "recent_turn_count": len(context["recent_turns"]),
            },
        )
        self.context_builder.write_delta(conversation_id, context)
        return response
