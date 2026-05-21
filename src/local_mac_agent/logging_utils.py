from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _timestamp(timestamp: str | None) -> str:
    return timestamp or datetime.now(timezone.utc).isoformat()


def _write_record(path: Path, record: dict[str, Any]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")))
        handle.write("\n")
    return record


def write_event(
    path: Path, event: str, details: dict[str, Any] | None = None, timestamp: str | None = None
) -> dict[str, Any]:
    return _write_record(
        path,
        {
            "details": details or {},
            "event": event,
            "record_type": "event",
            "timestamp": _timestamp(timestamp),
        },
    )


def write_action(
    path: Path,
    action: str,
    classification: str,
    details: dict[str, Any] | None = None,
    timestamp: str | None = None,
) -> dict[str, Any]:
    return _write_record(
        path,
        {
            "action": action,
            "classification": classification,
            "details": details or {},
            "record_type": "action",
            "timestamp": _timestamp(timestamp),
        },
    )


def write_performance(
    path: Path,
    operation: str,
    duration_ms: float,
    timestamp: str | None = None,
) -> dict[str, Any]:
    return _write_record(
        path,
        {
            "duration_ms": duration_ms,
            "operation": operation,
            "record_type": "performance",
            "timestamp": _timestamp(timestamp),
        },
    )


def write_error(
    path: Path,
    error_type: str,
    message: str,
    timestamp: str | None = None,
) -> dict[str, Any]:
    return _write_record(
        path,
        {
            "error_type": error_type,
            "message": message,
            "record_type": "error",
            "timestamp": _timestamp(timestamp),
        },
    )
