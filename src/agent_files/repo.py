"""Locate the agent-files repository root."""

from __future__ import annotations

from pathlib import Path


def find_repo_root(start: Path | None = None) -> Path:
    here = (start or Path.cwd()).resolve()
    for candidate in [here, *here.parents]:
        if (candidate / "agent-files.toml").is_file() and (
            candidate / "pyproject.toml"
        ).is_file():
            return candidate
    msg = "Could not find agent-files.toml above the current directory"
    raise FileNotFoundError(msg)
