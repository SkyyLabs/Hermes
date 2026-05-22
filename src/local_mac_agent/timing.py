from __future__ import annotations

from collections.abc import Mapping


def elapsed_ms(start: float, end: float) -> float:
    return round((end - start) * 1000, 2)


def format_latency_report(operation: str, timings: Mapping[str, float]) -> str:
    parts = " | ".join(f"{name}: {duration:.2f} ms" for name, duration in timings.items())
    return f"Latency {operation} | {parts}"
