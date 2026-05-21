# Design

| ID | Decision |
| --- | --- |
| D-001 | Build LocalMacAgent phase by phase with tests and docs. |
| D-002 | Default to local-first operation on macOS. |
| D-003 | Keep optional cloud APIs disabled until cloud-safe mode exists. |
| D-004 | Isolate future cloud inputs and outputs under `resources/cloud_resources/`. |
| D-005 | Use Python 3.10 or newer for backend phases. |
| D-006 | Use a `src` package layout. |
| D-007 | Use YAML configs for reviewed project defaults. |
| D-008 | Use `.env` for local environment overrides. |
| D-009 | Prefer environment values over YAML values over safe defaults. |
| D-010 | Use Pydantic Settings for typed runtime configuration. |
| D-011 | Use `pathlib.Path` for filesystem paths. |
| D-012 | Resolve runtime paths inside explicit parent directories. |
| D-013 | Track state, logs, resources, schemas, memory, and docs distinctly. |
| D-014 | Keep curated memory files human-readable. |
| D-015 | Treat safe actions as a small explicit allowlist. |
| D-016 | Require confirmation for dangerous or unknown actions. |
| D-017 | Block credential export and security-bypass behavior by default. |
| D-018 | Use deterministic JSONL records for foundation logging. |
| D-019 | Keep Phase 0 CLI minimal and development-oriented. |
| D-020 | Document chat before implementing chat. |
| D-021 | Document voice before implementing voice. |
| D-022 | Document RAG resource boundaries before retrieval exists. |
| D-023 | Trace design to requirements, tasks, tests, and feature docs. |
| D-024 | Do not fake external integrations. |
| D-025 | Reserve a future Swift native shell without scaffolding it now. |
