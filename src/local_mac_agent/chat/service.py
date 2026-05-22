from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from time import monotonic

from local_mac_agent.chat.context import ChatContextBuilder
from local_mac_agent.chat.conversation_store import ConversationStore
from local_mac_agent.chat.llm import LocalLLM, OllamaLocalLLM
from local_mac_agent.logging_utils import write_event
from local_mac_agent.paths import RuntimePaths
from local_mac_agent.timing import elapsed_ms


DEFAULT_CONVERSATION_ID = "default"


@dataclass(frozen=True)
class ChatTurn:
    response: str
    timings: dict[str, float]


class ChatService:
    def __init__(
        self,
        paths: RuntimePaths,
        llm: LocalLLM | None = None,
        conversation_store: ConversationStore | None = None,
        context_builder: ChatContextBuilder | None = None,
        log_path: Path | None = None,
        clock=monotonic,
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
        self.llm = llm or OllamaLocalLLM("gemma3")
        self.log_path = log_path or paths.logs / "events.jsonl"
        self.clock = clock
        self._turn_lock = Lock()

    def chat(self, message: str, conversation_id: str = DEFAULT_CONVERSATION_ID) -> str:
        return self.chat_turn(message, conversation_id).response

    def chat_turn(
        self, message: str, conversation_id: str = DEFAULT_CONVERSATION_ID
    ) -> ChatTurn:
        with self._turn_lock:
            total_start = self.clock()

            step_start = self.clock()
            self.conversation_store.append_turn(conversation_id, "user", message)
            timings = {
                "store_user": elapsed_ms(step_start, self.clock()),
            }

            step_start = self.clock()
            context = self.context_builder.build(conversation_id)
            timings["build_context"] = elapsed_ms(step_start, self.clock())

            step_start = self.clock()
            response = self.llm.respond(message, context)
            timings["llm"] = elapsed_ms(step_start, self.clock())

            step_start = self.clock()
            self.conversation_store.append_turn(conversation_id, "assistant", response)
            timings["store_assistant"] = elapsed_ms(step_start, self.clock())

            step_start = self.clock()
            write_event(
                self.log_path,
                "chat_turn",
                {
                    "conversation_id": conversation_id,
                    "recent_turn_count": len(context["recent_turns"]),
                },
            )
            timings["log_event"] = elapsed_ms(step_start, self.clock())

            step_start = self.clock()
            self.context_builder.write_delta(conversation_id, context)
            timings["context_delta"] = elapsed_ms(step_start, self.clock())
            timings["total"] = elapsed_ms(total_start, self.clock())
            return ChatTurn(response=response, timings=timings)
