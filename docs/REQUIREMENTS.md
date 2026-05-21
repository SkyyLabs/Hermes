# Requirements

| ID | Requirement | Design |
| --- | --- | --- |
| R-001 | The repository shall include Phase 0 docs, configs, schemas, memory, resources, state, logs, scripts, source, and tests. | D-001, D-013, D-023 |
| R-002 | The backend shall target Python 3.10 or newer with a `src` layout. | D-005, D-006 |
| R-003 | Settings shall combine safe defaults, YAML config, and `.env` or environment overrides with environment priority. | D-007, D-008, D-009, D-010 |
| R-004 | Runtime path handling shall use `pathlib.Path`, create required directories, and reject escaped resolved paths. | D-011, D-012 |
| R-005 | Safety classification shall distinguish safe, confirmation-required, blocked, and unknown actions. | D-015, D-016, D-017 |
| R-006 | Logging helpers shall write deterministic JSONL event, action, performance, and error records. | D-018 |
| R-007 | The Phase 0 CLI shall load settings, ensure paths, and support help, classification, and exit only. | D-019, D-020 |
| R-008 | Cloud features shall remain disabled and isolated to documented future directories. | D-002, D-003, D-004 |
| R-009 | Future chat, voice, RAG, memory, integrations, and Swift work shall be documented without fake implementations. | D-020, D-021, D-022, D-024, D-025 |
