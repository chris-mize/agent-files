"""Codex CLI adapter (argv from docs/spike-adapters.md)."""

from __future__ import annotations

import os
import shutil
import uuid
from pathlib import Path

from agent_files.config import AppConfig
from agent_files.models.run import CompletedRun, Harvest, RunSpec
from agent_files.runner.ephemeral import prepare_workspace
from agent_files.runner.process import allowed_env, spawn_process


class CodexRunner:
    name = "codex"
    emits_tool_trace = True

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
        home = workspace.parent / "codex-home"
        home.mkdir(parents=True, exist_ok=True)
        auth_src = Path.home() / ".codex" / "auth.json"
        auth_dest = home / "auth.json"
        if auth_src.is_file() and not auth_dest.exists():
            os.symlink(auth_src, auth_dest)
        skills = home / "skills"
        plugin_skills = (spec.plugin_dir / "skills") if spec.plugin_dir else None
        if plugin_skills is not None and plugin_skills.is_dir() and not skills.exists():
            os.symlink(plugin_skills, skills)
        spec.extra["codex_home"] = str(home)
        return workspace

    def spawn(self, workspace: Path, spec: RunSpec) -> CompletedRun:
        binary = shutil.which("codex")
        if binary is None:
            raise FileNotFoundError("codex not on PATH")
        argv = [
            binary,
            "exec",
            "--json",
            "--approve-for-me",
            "--ephemeral",
            "-C",
            str(workspace),
            "--skip-git-repo-check",
            spec.prompt,
        ]
        if spec.model:
            argv.insert(-1, spec.model)
            argv.insert(-1, "-m")
        return spawn_process(
            argv,
            cwd=workspace,
            env=allowed_env(
                self.config.env_allowlist,
                {"CODEX_HOME": str(spec.extra["codex_home"])},
            ),
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
