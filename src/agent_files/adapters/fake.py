"""Fake adapter for tests and CI. Never reports provider scores."""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

from agent_files.config import AppConfig
from agent_files.models.run import CompletedRun, Harvest, RunSpec
from agent_files.runner.ephemeral import prepare_workspace
from agent_files.runner.process import allowed_env, spawn_process

_FAKE_SCRIPT = r"""
import os, time
from pathlib import Path
ws = Path(os.environ["AGENT_FILES_WORKSPACE"])
prompt = Path(os.environ["AGENT_FILES_PROMPT_FILE"]).read_text()
sleep = float(os.environ.get("AGENT_FILES_FAKE_SLEEP", "0"))
if sleep:
    time.sleep(sleep)
if ".agent-files-canary" in prompt or "canary" in prompt.lower():
    (ws / ".agent-files-canary").write_text("canary\n", encoding="utf-8")
if "hello.txt" in prompt:
    (ws / "hello.txt").write_text("ok\n", encoding="utf-8")
if "SPEC.md" in prompt or "standalone" in prompt.lower():
    (ws / "SPEC.md").write_text(
        "# Goal\nWidget CLI prints hi.\n"
        "# File tree\n- spec.md is the deliverable\n"
        "# Commands\nwidget\n"
        "# Defaults\nnone\n"
        "# Tests\nwidget prints hi\n"
        "# Definition of done\nwidget prints hi and nothing else.\n",
        encoding="utf-8",
    )
if os.environ.get("AGENT_FILES_FAKE_SKILL_READ") == "1":
    (ws / ".agent-files-skill-loaded").write_text(
        os.environ.get("AGENT_FILES_FAKE_SKILL_NAME", "best-practices"),
        encoding="utf-8",
    )
"""


class FakeRunner:
    name = "fake"
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
        prompt_file = workspace.parent / "prompt.txt"
        prompt_file.write_text(spec.prompt, encoding="utf-8")
        spec.extra["prompt_file"] = str(prompt_file)
        return workspace

    def spawn(self, workspace: Path, spec: RunSpec) -> CompletedRun:
        env = allowed_env(
            self.config.env_allowlist,
            {
                "AGENT_FILES_WORKSPACE": str(workspace),
                "AGENT_FILES_PROMPT_FILE": str(spec.extra["prompt_file"]),
                "AGENT_FILES_FAKE_SLEEP": str(spec.extra.get("sleep", 0)),
                "AGENT_FILES_FAKE_SKILL_READ": str(spec.extra.get("skill_read", "")),
            },
        )
        return spawn_process(
            [sys.executable, "-c", _FAKE_SCRIPT],
            cwd=workspace,
            env=env,
            timeout_seconds=spec.timeout_seconds,
            trace_path=workspace.parent / "trace.jsonl",
        )

    def harvest(self, completed: CompletedRun) -> Harvest:
        marker = completed.workspace / ".agent-files-skill-loaded"
        skill_read: str = "skipped"
        paths: list[str] = []
        if marker.is_file():
            skill_read = "marker"
            paths = [marker.read_text(encoding="utf-8").strip()]
        return Harvest(
            skill_read=skill_read,  # type: ignore[arg-type]
            skill_paths=paths,
            usage=None,
            redacted_stdout=completed.stdout,
            redacted_stderr=completed.stderr,
        )
