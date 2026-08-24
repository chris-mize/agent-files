"""Leak grader: fixture-unique strings must not appear in overlay prompts."""

from __future__ import annotations

from pathlib import Path

from agent_files.models.evalfile import GraderSpec
from agent_files.models.run import GradeResult


def unique_lines(fixture_dir: Path) -> list[str]:
    counts: dict[str, int] = {}
    if not fixture_dir.is_dir():
        return []
    for path in fixture_dir.rglob("*"):
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            text = line.strip()
            if len(text) < 12:
                continue
            counts[text] = counts.get(text, 0) + 1
    return [line for line, n in counts.items() if n == 1]


def grade_leak(
    workspace: Path,
    spec: GraderSpec,
    *,
    overlay: Path | None = None,
    fixture_dir: Path | None = None,
    **_: object,
) -> GradeResult:
    opts = spec.options()
    overlay_path = overlay
    if overlay_path is None:
        rel = opts.get("overlay", "AGENTS.md")
        overlay_path = workspace / str(rel)
    if overlay_path is None or not overlay_path.is_file():
        return GradeResult(type="leak", passed=True, detail="no overlay")
    fixtures = fixture_dir
    if fixtures is None and opts.get("fixture"):
        fixtures = workspace / str(opts["fixture"])
    if fixtures is None:
        return GradeResult(type="leak", passed=True, detail="no fixture dir")
    blob = overlay_path.read_text(encoding="utf-8")
    leaked = [line for line in unique_lines(fixtures) if line in blob]
    passed = not leaked
    return GradeResult(
        type="leak",
        passed=passed,
        detail="ok" if passed else f"leaked {leaked[:3]}",
    )
