# Agent Instructions

- Build LocalMacAgent phase by phase.
- Do not create placeholder source files or source folders for future phases.
- Run tests after each implemented task and update docs after each implemented feature.
- Every requirement references design decisions. Every task references requirements.
- Keep behavior local-first by default.
- Keep cloud APIs disabled by default.
- Future cloud APIs may only read from `resources/cloud_resources/allowed_inputs/`
  and write to `resources/cloud_resources/allowed_outputs/`.
- Require confirmation for dangerous actions and keep blocked actions blocked by
  default.
- Do not fake integrations or claim unimplemented features work.
- Keep code clean, readable, typed, and minimal.
