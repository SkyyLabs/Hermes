# LocalMacAgent

LocalMacAgent is a local-first, voice-first, chat-native assistant project for macOS.
Phase 0 provides the repository foundation. Phase 1 adds a local text chat loop
with persisted JSONL conversation history, compact core-memory context, and a
real local Ollama backend by default.

Future phases will add voice, commands, RAG, memory routing, screen context, app
integrations, optional cloud-safe workflows, and a Swift native shell. Those
features are documented but not implemented yet.

## Development

Use Python 3.10 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
./scripts/run_tests.sh
./scripts/run_dev.sh
```

The development CLI currently supports `help`, `chat <message>`,
`classify <action>`, and `exit`.

```text
> chat hello
Local placeholder response: received 'hello' with 1 recent turn(s) in context.
```

Configuration defaults live in `configs/`; local overrides can be placed in `.env`.
The default model config uses Ollama at `http://127.0.0.1:11434` with `gemma3`.
Start Ollama and pull the configured local model before using chat, or set
`LOCAL_MAC_AGENT_MODEL__MODEL_NAME` in `.env` to another local Ollama model.
Set `LOCAL_MAC_AGENT_MODEL__PROVIDER=placeholder` only when a deterministic test
or development response is preferred over real model output.
