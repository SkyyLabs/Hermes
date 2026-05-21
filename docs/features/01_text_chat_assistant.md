# Feature 01: Text Chat Assistant

## Implemented

- Plain typed CLI turns using a stable default conversation ID
- Local JSONL storage for user and assistant turns
- Recent local history retrieval for compact context
- Core memory loading from the five existing Markdown memory files
- Loopback Ollama chat responses by default
- Clear missing-LLM failures instead of synthetic assistant responses
- Chat event logs and per-turn context delta records

## Limitations

Conversation selection, model download/management, voice, command routing, RAG,
memory routing, screen context, workers, cloud-safe mode, and app integrations
remain future phases.
