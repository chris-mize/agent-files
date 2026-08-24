"""Grader registry."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from agent_files.grade.leak import grade_leak
from agent_files.grade.marker import grade_marker
from agent_files.grade.outcome import (
    grade_file_content,
    grade_grep_absent,
    grade_grep_headings,
    grade_grep_present,
    grade_grep_product,
    grade_test_cmd,
)
from agent_files.grade.size import grade_size_ratchet
from agent_files.models.evalfile import EvalItem
from agent_files.models.run import GradeResult

GraderFn = Callable[..., GradeResult]

REGISTRY: dict[str, GraderFn] = {
    "file_content": grade_file_content,
    "test_cmd": grade_test_cmd,
    "grep_product": grade_grep_product,
    "grep_headings": grade_grep_headings,
    "grep_absent": grade_grep_absent,
    "grep_present": grade_grep_present,
    "size_ratchet": grade_size_ratchet,
    "leak": grade_leak,
    "marker": grade_marker,
}


def run_graders(
    workspace: Path,
    item: EvalItem,
    *,
    overlay: Path | None = None,
    baseline_bytes: int | None = None,
    fixture_dir: Path | None = None,
) -> list[GradeResult]:
    results: list[GradeResult] = []
    for spec in item.graders:
        fn = REGISTRY.get(spec.type)
        if fn is None:
            results.append(
                GradeResult(
                    type=spec.type, passed=False, detail=f"unknown grader {spec.type}"
                )
            )
            continue
        results.append(
            fn(
                workspace,
                spec,
                overlay=overlay,
                baseline_bytes=baseline_bytes,
                fixture_dir=fixture_dir,
            )
        )
    return results
