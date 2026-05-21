from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class RuntimePaths:
    root: Path
    configs: Path = field(init=False)
    memory: Path = field(init=False)
    state: Path = field(init=False)
    logs: Path = field(init=False)
    resources: Path = field(init=False)
    raw_resources: Path = field(init=False)
    custom_resources: Path = field(init=False)
    cloud_resources: Path = field(init=False)

    def __post_init__(self) -> None:
        root = self.root.expanduser().resolve()
        object.__setattr__(self, "root", root)
        object.__setattr__(self, "configs", root / "configs")
        object.__setattr__(self, "memory", root / "memory")
        object.__setattr__(self, "state", root / "state")
        object.__setattr__(self, "logs", root / "logs")
        resources = root / "resources"
        object.__setattr__(self, "resources", resources)
        object.__setattr__(self, "raw_resources", resources / "raw")
        object.__setattr__(self, "custom_resources", resources / "custom")
        object.__setattr__(self, "cloud_resources", resources / "cloud_resources")

    def ensure_directories(self) -> None:
        for path in (
            self.configs,
            self.memory,
            self.state,
            self.logs,
            self.resources,
            self.raw_resources,
            self.custom_resources,
            self.cloud_resources,
        ):
            path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def is_inside(path: Path, parent: Path) -> bool:
        try:
            path.expanduser().resolve().relative_to(parent.expanduser().resolve())
        except ValueError:
            return False
        return True

    def resolve_inside(self, path: Path | str, parent: Path | None = None) -> Path:
        base = (parent or self.root).expanduser().resolve()
        candidate = Path(path).expanduser()
        resolved = (base / candidate).resolve() if not candidate.is_absolute() else candidate.resolve()
        if not self.is_inside(resolved, base):
            raise ValueError(f"Path escapes runtime directory: {path}")
        return resolved
