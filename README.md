# LocalMacAgent

LocalMacAgent is a local-first, voice-first, chat-native assistant project for macOS.
Phase 0 provides the repository foundation only: configuration loading, runtime
paths, safety classification, deterministic JSONL logging helpers, docs, and tests.

Future phases will add chat, voice, commands, RAG, memory routing, context, app
integrations, optional cloud-safe workflows, and a Swift native shell. Those
features are documented but not implemented yet.

## Development

Use Python 3.10 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./scripts/run_tests.sh
./scripts/run_dev.sh
```

The development CLI currently supports `help`, `classify <action>`, and `exit`.
Configuration defaults live in `configs/`; local overrides can be placed in `.env`.
