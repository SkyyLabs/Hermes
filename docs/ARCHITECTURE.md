# Architecture

Phase 0 keeps the backend narrow:

- `settings.py` validates safe defaults, YAML defaults, and environment overrides.
- `paths.py` defines runtime directories and path containment helpers.
- `safety.py` classifies actions before later command execution layers exist.
- `logging_utils.py` writes deterministic JSONL records for later observability.
- `main.py` provides a small development CLI.

Future architecture grows from chat and voice input toward command routing,
retrieval, memory, context, workers, integrations, cloud-safe workflows, and a
Swift shell without pretending those layers already exist.
