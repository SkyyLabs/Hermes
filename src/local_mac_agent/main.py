from __future__ import annotations

from threading import Thread
from pathlib import Path

from local_mac_agent.chat.llm import build_local_llm
from local_mac_agent.chat.service import ChatService
from local_mac_agent.paths import RuntimePaths
from local_mac_agent.safety import SafetyGuard
from local_mac_agent.settings import load_settings
from local_mac_agent.timing import format_latency_report
from local_mac_agent.voice.service import VoiceService


HELP_TEXT = """LocalMacAgent commands:
  help                 Show this help.
  <message>            Send a typed chat turn.
  voice transcript <text>
                       Route a voice transcript through chat and speak it.
  classify <action>    Classify an action with the safety guard.
  exit                 Exit the development CLI.

Wake listening for Hey Mycroft starts when the CLI starts.
Future commands are documented but not implemented yet: command, rag, memory,
screen, workers, integrations.
"""


def main() -> None:
    project_root = Path.cwd()
    settings = load_settings(project_root)
    paths = RuntimePaths(project_root)
    paths.ensure_directories()
    guard = SafetyGuard()
    try:
        llm = build_local_llm(settings.model)
    except ValueError as exc:
        print(exc)
        return
    chat_service = ChatService(paths, llm=llm)
    voice_service = VoiceService(chat_service, settings.voice)

    print(f"{settings.app.name} local CLI")
    print(HELP_TEXT)
    _start_wake_listener(voice_service)
    while True:
        try:
            command = input("> ").strip()
        except EOFError:
            print()
            return
        if not command:
            continue
        if command == "exit":
            return
        if command == "help":
            print(HELP_TEXT)
            continue
        if command.startswith("classify "):
            action = command.removeprefix("classify ").strip()
            if action:
                print(f"{action}: {guard.classify_action(action)}")
            else:
                print("Usage: classify <action>")
            continue
        if command.startswith("chat "):
            message = command.removeprefix("chat ").strip()
            if message:
                _print_chat_reply(chat_service, message)
            else:
                print("Usage: chat <message>")
            continue
        if command.startswith("voice transcript "):
            transcript = command.removeprefix("voice transcript ").strip()
            if transcript:
                try:
                    turn = voice_service.process_transcript_turn(transcript)
                    print(turn.response)
                    print(format_latency_report("voice transcript", turn.timings))
                except RuntimeError as exc:
                    print(f"Voice failed: {exc}")
            else:
                print("Usage: voice transcript <text>")
            continue
        _print_chat_reply(chat_service, command)


def _start_wake_listener(voice_service: VoiceService) -> None:
    def listen() -> None:
        try:
            voice_service.listen_forever()
        except RuntimeError as exc:
            print(f"\nWake listening unavailable: {exc}")

    Thread(target=listen, name="wake-listener", daemon=True).start()


def _print_chat_reply(chat_service: ChatService, message: str) -> None:
    try:
        turn = chat_service.chat_turn(message)
        print(turn.response)
        print(format_latency_report("chat", turn.timings))
    except RuntimeError as exc:
        print(f"Chat failed: {exc}")


if __name__ == "__main__":
    main()
