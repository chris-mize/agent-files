"""Cursor CLI adapter (argv from docs/spike-adapters.md)."""

from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

from agent_files.config import AppConfig
from agent_files.models.run import CompletedRun, Harvest, RunSpec
from agent_files.runner.ephemeral import prepare_workspace
from agent_files.runner.process import allowed_env, spawn_process


class CursorRunner:
    name = "cursor"
    emits_tool_trace = True

    def __init__(self, config: AppConfig, repo: Path) -> None:
        self.config = config
        self.repo = repo
        self.cli_version = "missing"
        binary = shutil.which("cursor-agent")
        if binary:
            completed = spawn_process(
                [binary, "--version"],
                cwd=repo,
                env=allowed_env(["PATH", "HOME", "USER", "LANG", "TERM"]),
                timeout_seconds=30,
            )
            self.cli_version = (completed.stdout or completed.stderr).strip() or "unknown"

    def prepare(self, spec: RunSpec) -> Path:
        run_id = str(uuid.uuid4())
        workspace, plugin, ids = prepare_workspace(
            self.config, spec, self.repo, run_id
        )
        spec.plugin_dir = plugin
        spec.extra["run_id"] = run_id
        spec.extra["fixture_ids"] = ids
        spec.extra["cli_version"] = self.cli_version
        return workspace

    def spawn(self, workspace: Path, spec: RunSpec) -> CompletedRun:
        binary = shutil.which("cursor-agent")
        if binary is None:
            raise FileNotFoundError("cursor-agent not on PATH")
        argv = [
            binary,
            "-p",
            "--output-format",
            "stream-json",
            "--trust",
            "--sandbox",
            "enabled",
            "--workspace",
            str(workspace),
            "--plugin-dir",
            str(spec.plugin_dir or workspace.parent / "plugin"),
            "--model",
            spec.model,
            spec.prompt,
        ]
        return spawn_process(
            argv,
            cwd=workspace,
            env=allowed_env(self.config.env_allowlist),
            timeout_seconds=spec.timeout_seconds,
            trace_path=workspace.parent / "trace.jsonl",
        )

    def harvest(self, completed: CompletedRun) -> Harvest:
        paths: list[str] = []
        for line in completed.stdout.splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            tool = event.get("tool_call") or {}
            read = tool.get("readToolCall") or {}
            path = (read.get("args") or {}).get("path") or ""
            if path:
                paths.append(str(path))
        skill_read = "skipped"
        if any("SKILL.md" in path or "/skills/" in path for path in paths):
            skill_read = "observed"
        marker = completed.workspace / ".agent-files-skill-loaded"
        if skill_read == "skipped" and marker.is_file():
            skill_read = "marker"
        return Harvest(
            skill_read=skill_read,  # type: ignore[arg-type]
            skill_paths=paths,
            usage=None,
            redacted_stdout=completed.stdout,
            redacted_stderr=completed.stderr,
        )
