# Safety

LocalMacAgent starts with explicit action categories. Read-like actions are safe,
dangerous actions require confirmation, blocked actions remain blocked by default,
and unknown actions require confirmation.

Cloud APIs are disabled in Phase 0. Future integrations must preserve user intent,
permission boundaries, visible indicators for observation, and the cloud resource
isolation rules.
