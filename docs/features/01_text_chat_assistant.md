# Feature 01: Text Chat Assistant

## Implemented

- `chat <message>` CLI turns using a stable default conversation ID
- Local JSONL storage for user and assistant turns
- Recent local history retrieval for compact context
- Core memory loading from the five existing Markdown memory files
- Deterministic placeholder local LLM responses
- Chat event logs and per-turn context delta records

## Limitations

The current LLM is a deterministic placeholder. Conversation selection, real
local model integration, voice, command routing, RAG, memory routing, screen
context, workers, cloud-safe mode, and app integrations remain future phases.
