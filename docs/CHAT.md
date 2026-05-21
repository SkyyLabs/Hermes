# Chat

Phase 1 implements a local text chat loop. A plain typed CLI message is stored as
a user turn in `state/conversations.jsonl`, combined with recent local history
and the curated Markdown files in `memory/`, passed to the configured local model,
then stored again as an assistant turn.

Chat writes an event record to `logs/events.jsonl` and a context delta to
`state/context_deltas.jsonl`. The context uses core memory files only:
`core.md`, `projects.md`, `preferences.md`, `working_context.md`, and
`memory_map.md`. Those files are background context for chat replies; the model
is instructed not to draft or update memory from ordinary conversation.

The default provider is Ollama on a loopback URL with `gemma3` configured in
`configs/model.yaml`. Ollama must be running locally and the configured model must
be available. If no supported LLM is configured or Ollama is unavailable, chat
reports that configuration failure instead of generating a synthetic reply.

The Ollama adapter rejects remote base URLs and explicit Ollama cloud model names
while `local_only` is true. Voice, command automation, RAG, memory routing,
screen context, workers, and app integrations remain later phases.
Voice transcripts reuse the same default conversation ID as typed chat turns so
text and audio history carry forward together.
