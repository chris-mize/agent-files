"""Claude Code adapter. Skip when `claude` is missing; never fake scores."""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from agent_files.config import AppConfig
from agent_files.models.run import CompletedRun, Harvest, RunSpec
from agent_files.runner.ephemeral import prepare_workspace
from agent_files.runner.process import allowed_env, spawn_process


class ClaudeRunner:
    name = "claude"
    emits_tool_trace = False

    def __init__(self, config: AppConfig, repo: Path) -> None:
        self.config = config
        self.repo = repo

    def prepare(self, spec: RunSpec) -> Path:
        run_id = str(uuid.uuid4())
        workspace, plugin, ids = prepare_workspace(
            self.config, spec, self.repo, run_id
        )
        spec.plugin_dir = plugin
        spec.extra["run_id"] = run_id
        spec.extra["fixture_ids"] = ids
        agents = self.repo / "agents" / "AGENTS.md"
        if agents.is_file():
            (workspace / "CLAUDE.md").write_text(
                agents.read_text(encoding="utf-8"), encoding="utf-8"
            )
        return workspace

    def spawn(self, workspace: Path, spec: RunSpec) -> CompletedRun:
        binary = shutil.which("claude")
        if binary is None:
            raise FileNotFoundError("claude not on PATH")
        return spawn_process(
            [binary, "-p", spec.prompt],
            cwd=workspace,
            env=allowed_env(self.config.env_allowlist),
            timeout_seconds=spec.timeout_seconds,
            trace_path=workspace.parent / "trace.jsonl",
        )

    def harvest(self, completed: CompletedRun) -> Harvest:
        marker = completed.workspace / ".agent-files-skill-loaded"
        skill_read = "marker" if marker.is_file() else "skipped"
        return Harvest(
            skill_read=skill_read,  # type: ignore[arg-type]
            skill_paths=[],
            usage=None,
            redacted_stdout=completed.stdout,
            redacted_stderr=completed.stderr,
        )
