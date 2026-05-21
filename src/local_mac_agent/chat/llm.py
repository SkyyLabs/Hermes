from __future__ import annotations

import json
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from local_mac_agent.chat.context import ChatContext
from local_mac_agent.settings import ModelSettings


class LocalLLM(Protocol):
    def respond(self, message: str, context: ChatContext) -> str: ...


class OllamaLocalLLM:
    def __init__(
        self,
        model_name: str,
        base_url: str = "http://127.0.0.1:11434",
        local_only: bool = True,
    ) -> None:
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        if local_only and not _is_loopback_url(self.base_url):
            raise ValueError("Ollama local-only mode requires a loopback base URL.")
        if local_only and model_name.strip().lower().endswith("-cloud"):
            raise ValueError("Ollama local-only mode does not allow cloud model names.")

    def respond(self, message: str, context: ChatContext) -> str:
        messages = [{"role": "system", "content": context["prompt"]}]
        messages.extend(
            {
                "role": turn["role"],
                "content": turn["content"],
            }
            for turn in _history_before_current_message(message, context)
        )
        messages.append({"role": "user", "content": message})

        request = Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(
                {"model": self.model_name, "messages": messages, "stream": False}
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=120) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise RuntimeError(f"Ollama chat request failed with HTTP {exc.code}.") from exc
        except URLError as exc:
            raise RuntimeError(
                "No LLM configured. Start Ollama and pull the configured model."
            ) from exc

        content = payload.get("message", {}).get("content")
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("Ollama chat response did not contain assistant content.")
        return content.strip()


def build_local_llm(settings: ModelSettings) -> LocalLLM:
    provider = settings.provider.strip().lower()
    if provider == "ollama":
        return OllamaLocalLLM(
            settings.model_name,
            base_url=settings.base_url,
            local_only=settings.local_only,
        )
    raise ValueError(f"No LLM configured for provider: {settings.provider}")


def _is_loopback_url(base_url: str) -> bool:
    parsed = urlparse(base_url)
    return parsed.scheme in {"http", "https"} and parsed.hostname in {
        "127.0.0.1",
        "::1",
        "localhost",
    }


def _history_before_current_message(message: str, context: ChatContext):
    recent_turns = context["recent_turns"]
    if recent_turns and recent_turns[-1]["role"] == "user":
        if recent_turns[-1]["content"] == message:
            return recent_turns[:-1]
    return recent_turns
