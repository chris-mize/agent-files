"""Skill-read marker grader."""

from __future__ import annotations

from pathlib import Path

from agent_files.models.evalfile import GraderSpec
from agent_files.models.run import GradeResult


def grade_marker(
    workspace: Path,
    spec: GraderSpec,
    **_: object,
) -> GradeResult:
    opts = spec.options()
    rel = str(opts.get("path", ".agent-files-skill-loaded"))
    path = workspace / rel
    if not path.is_file():
        return GradeResult(type="marker", passed=False, detail="missing marker")
    expected = opts.get("equals")
    if expected is not None and path.read_text(encoding="utf-8").strip() != str(expected):
        return GradeResult(type="marker", passed=False, detail="marker mismatch")
    return GradeResult(type="marker", passed=True, detail=rel)
