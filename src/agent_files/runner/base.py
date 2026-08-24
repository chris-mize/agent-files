"""Runner protocol."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from agent_files.models.run import CompletedRun, Harvest, RunSpec


class Runner(Protocol):
    name: str
    emits_tool_trace: bool

    def prepare(self, spec: RunSpec) -> Path: ...

    def spawn(self, workspace: Path, spec: RunSpec) -> CompletedRun: ...

    def harvest(self, completed: CompletedRun) -> Harvest: ...
