import json
from pathlib import Path

from local_mac_agent.logging_utils import (
    write_action,
    write_error,
    write_event,
    write_performance,
)


TIMESTAMP = "2026-05-21T12:00:00+00:00"


def test_jsonl_helpers_write_typed_records(tmp_path: Path) -> None:
    log_file = tmp_path / "logs" / "events.jsonl"

    write_event(log_file, "startup", {"phase": 0}, TIMESTAMP)
    write_action(log_file, "read", "safe", timestamp=TIMESTAMP)
    write_performance(log_file, "settings_load", 2.5, TIMESTAMP)
    write_error(log_file, "ValueError", "bad config", TIMESTAMP)

    records = [json.loads(line) for line in log_file.read_text(encoding="utf-8").splitlines()]
    assert [record["record_type"] for record in records] == [
        "event",
        "action",
        "performance",
        "error",
    ]
    assert records[0] == {
        "details": {"phase": 0},
        "event": "startup",
        "record_type": "event",
        "timestamp": TIMESTAMP,
    }
    assert records[1]["classification"] == "safe"
    assert records[2]["duration_ms"] == 2.5
    assert records[3]["message"] == "bad config"
