from __future__ import annotations

from pathlib import Path

from local_mac_agent.chat.service import ChatService
from local_mac_agent.paths import RuntimePaths
from local_mac_agent.safety import SafetyGuard
from local_mac_agent.settings import load_settings


HELP_TEXT = """LocalMacAgent commands:
  help                 Show this help.
  chat <message>       Add a local text chat turn.
  classify <action>    Classify an action with the safety guard.
  exit                 Exit the development CLI.

Future commands are documented but not implemented yet: voice, command, rag,
memory, screen, workers, integrations.
"""


def main() -> None:
    project_root = Path.cwd()
    settings = load_settings(project_root)
    paths = RuntimePaths(project_root)
    paths.ensure_directories()
    guard = SafetyGuard()
    chat_service = ChatService(paths)

    print(f"{settings.app.name} local CLI")
    print(HELP_TEXT)
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
                print(chat_service.chat(message))
            else:
                print("Usage: chat <message>")
            continue
        print("Unknown command. Use `help` for available commands.")


if __name__ == "__main__":
    main()
