"""Size ratchet grader."""

from __future__ import annotations

from pathlib import Path

from agent_files.models.evalfile import GraderSpec
from agent_files.models.run import GradeResult


def grade_size_ratchet(
    workspace: Path,
    spec: GraderSpec,
    *,
    overlay: Path | None = None,
    baseline_bytes: int | None = None,
    **_: object,
) -> GradeResult:
    opts = spec.options()
    target = overlay
    if target is None:
        rel = opts.get("path", "AGENTS.md")
        target = workspace / str(rel)
    if target is None or not target.is_file():
        return GradeResult(type="size_ratchet", passed=False, detail="no overlay file")
    size = target.stat().st_size
    limit = opts.get("max_bytes", baseline_bytes)
    if limit is None:
        return GradeResult(type="size_ratchet", passed=True, detail=f"{size} bytes")
    passed = size <= int(limit)
    return GradeResult(
        type="size_ratchet",
        passed=passed,
        detail=f"{size} <= {limit}" if passed else f"{size} > {limit}",
    )
