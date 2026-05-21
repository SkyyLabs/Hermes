from __future__ import annotations

from local_mac_agent.chat.context import ChatContext


class DefaultLocalLLM:
    """Deterministic local placeholder used until a real local model is added."""

    def respond(self, message: str, context: ChatContext) -> str:
        history_count = len(context["recent_turns"])
        return (
            "Local placeholder response: "
            f"received '{message}' with {history_count} recent turn(s) in context."
        )
