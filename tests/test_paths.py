from pathlib import Path

import pytest

from local_mac_agent.paths import RuntimePaths


def test_ensure_directories_creates_runtime_paths(tmp_path: Path) -> None:
    paths = RuntimePaths(tmp_path)

    paths.ensure_directories()

    assert paths.logs.is_dir()
    assert paths.raw_resources.is_dir()
    assert paths.custom_resources.is_dir()
    assert paths.cloud_resources.is_dir()


def test_resolve_inside_accepts_local_paths(tmp_path: Path) -> None:
    paths = RuntimePaths(tmp_path)

    resolved = paths.resolve_inside("resources/raw/note.md")

    assert resolved == tmp_path / "resources" / "raw" / "note.md"
    assert RuntimePaths.is_inside(resolved, tmp_path)


def test_resolve_inside_rejects_escape(tmp_path: Path) -> None:
    paths = RuntimePaths(tmp_path)

    with pytest.raises(ValueError):
        paths.resolve_inside("../outside.txt")
