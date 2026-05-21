# Chat

Phase 1 implements a local text chat loop. A `chat <message>` CLI input is stored
as a user turn in `state/conversations.jsonl`, combined with recent local history
and the curated Markdown files in `memory/`, passed to a deterministic local
placeholder LLM, then stored again as an assistant turn.

Chat writes an event record to `logs/events.jsonl` and a context delta to
`state/context_deltas.jsonl`. The context uses core memory files only:
`core.md`, `projects.md`, `preferences.md`, `working_context.md`, and
`memory_map.md`.

The placeholder LLM does not call cloud APIs and does not require Ollama. Voice,
command automation, RAG, memory routing, screen context, workers, and app
integrations remain later phases.
