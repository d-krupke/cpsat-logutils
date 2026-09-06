"""Shared helpers for the cpsat_logutils tests: locate the repository's example logs.

``example_logs/`` holds a handful of logs from recent OR-Tools releases;
``example_logs/archive/`` holds older ones (9.3 ... 9.10) and redundant parameter
variants. The parser must handle both, so the fixtures below cover the archive as
well - it is the only coverage of the older log formats.
"""

from __future__ import annotations

from pathlib import Path

import pytest

EXAMPLE_DIR = Path(__file__).resolve().parents[1] / "example_logs"
ARCHIVE_DIR = EXAMPLE_DIR / "archive"


def example_paths() -> list[Path]:
    """Every example log, the archived ones included."""
    return sorted(EXAMPLE_DIR.glob("*.txt")) + sorted(ARCHIVE_DIR.glob("*.txt"))


def read_example(name: str) -> str:
    path = EXAMPLE_DIR / name
    if not path.is_file():
        path = ARCHIVE_DIR / name
    return path.read_text()


@pytest.fixture(params=example_paths(), ids=lambda p: p.name)
def example_log(request: pytest.FixtureRequest) -> tuple[str, str]:
    path: Path = request.param
    return path.name, path.read_text()
