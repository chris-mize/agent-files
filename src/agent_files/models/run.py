"""Run request/result contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field


class GradeResult(BaseModel):
    type: str
    passed: bool
    detail: str = ""


class RunResult(BaseModel):
    run_id: str
    eval_id: int
    adapter: str
    model: str
    comparison_key: str
    variant_key: str
    passed: bool
    status: Literal["passed", "failed", "skipped", "aborted", "error"]
    grader_results: list[GradeResult] = Field(default_factory=list)
    skill_read: Literal["observed", "marker", "skipped"] = "skipped"
    fixture_skill_ids: list[str] = Field(default_factory=list)
    cost_state: Literal["subscription_quota", "metered", "unknown"] = (
        "subscription_quota"
    )
    review_path: str | None = None
    timed_out: bool = False
    duration_ms: int = 0
    workspace: str = ""


@dataclass
class RunSpec:
    eval_id: int
    prompt: str
    adapter: str
    model: str
    timeout_seconds: int
    crowded: bool
    artifact: str
    overlay_root: Path | None
    fixture_relpaths: list[str]
    plugin_dir: Path | None
    env: dict[str, str]
    repeat_index: int = 0
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class CompletedRun:
    workspace: Path
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool
    duration_ms: int
    trace_path: Path | None
    argv: list[str]


@dataclass
class Harvest:
    skill_read: Literal["observed", "marker", "skipped"]
    skill_paths: list[str]
    usage: dict[str, Any] | None
    redacted_stdout: str
    redacted_stderr: str


GradeResult = GradeResult
RunResult = RunResult
