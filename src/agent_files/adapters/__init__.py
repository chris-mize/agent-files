"""Adapter factory."""

from __future__ import annotations

import shutil
from pathlib import Path

from agent_files.adapters.claude import ClaudeRunner
from agent_files.adapters.codex import CodexRunner
from agent_files.adapters.cursor import CursorRunner
from agent_files.adapters.fake import FakeRunner
from agent_files.config import AppConfig
from agent_files.runner.base import Runner


class AdapterSkip(Exception):
    def __init__(self, name: str, reason: str) -> None:
        super().__init__(f"{name}: {reason}")
        self.name = name
        self.reason = reason


def get_runner(name: str, config: AppConfig, repo: Path) -> Runner:
    if name == "fake":
        return FakeRunner(config, repo)
    if name == "cursor":
        return CursorRunner(config, repo)
    if name == "codex":
        return CodexRunner(config, repo)
    if name == "claude":
        if shutil.which("claude") is None:
            raise AdapterSkip("claude", "binary not on PATH")
        return ClaudeRunner(config, repo)
    raise AdapterSkip(name, "unknown adapter")
