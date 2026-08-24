"""Outcome graders."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from agent_files.models.evalfile import GraderSpec
from agent_files.models.run import GradeResult

_HEADING = re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)


def _text(workspace: Path, rel: str) -> str | None:
    path = workspace / rel
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8")


def grade_file_content(
    workspace: Path,
    spec: GraderSpec,
    **_: object,
) -> GradeResult:
    opts = spec.options()
    rel = str(opts["path"])
    path = workspace / rel
    if not path.is_file():
        return GradeResult(type="file_content", passed=False, detail=f"missing {rel}")
    expected = opts.get("equals")
    if expected is not None and path.read_text(encoding="utf-8") != expected:
        return GradeResult(type="file_content", passed=False, detail="content mismatch")
    return GradeResult(type="file_content", passed=True, detail=rel)


def grade_test_cmd(
    workspace: Path,
    spec: GraderSpec,
    **_: object,
) -> GradeResult:
    opts = spec.options()
    cmd = opts["cmd"]
    cwd = workspace / str(opts.get("cwd", "."))
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)
    passed = result.returncode == 0
    return GradeResult(
        type="test_cmd",
        passed=passed,
        detail=result.stderr[-400:] if not passed else "ok",
    )


def grade_grep_product(
    workspace: Path,
    spec: GraderSpec,
    **_: object,
) -> GradeResult:
    return _grep(workspace, spec, "grep_product", present=True)


def grade_grep_present(
    workspace: Path,
    spec: GraderSpec,
    **_: object,
) -> GradeResult:
    return _grep(workspace, spec, "grep_present", present=True)


def grade_grep_absent(
    workspace: Path,
    spec: GraderSpec,
    **_: object,
) -> GradeResult:
    return _grep(workspace, spec, "grep_absent", present=False)


def _grep(workspace: Path, spec: GraderSpec, name: str, *, present: bool) -> GradeResult:
    opts = spec.options()
    rel = str(opts["path"])
    text = _text(workspace, rel)
    if text is None:
        return GradeResult(type=name, passed=False, detail=f"missing {rel}")
    needles = opts.get("needles") or opts.get("patterns") or []
    flags = re.IGNORECASE if opts.get("ignore_case", name == "grep_absent") else 0
    missing: list[str] = []
    found: list[str] = []
    for needle in needles:
        if re.search(re.escape(str(needle)), text, flags):
            found.append(str(needle))
        else:
            missing.append(str(needle))
    if present:
        ok = not missing
        detail = "ok" if ok else f"missing {missing}"
    else:
        ok = not found
        detail = "ok" if ok else f"present {found}"
    return GradeResult(type=name, passed=ok, detail=detail)


def grade_grep_headings(
    workspace: Path,
    spec: GraderSpec,
    **_: object,
) -> GradeResult:
    opts = spec.options()
    rel = str(opts["path"])
    text = _text(workspace, rel)
    if text is None:
        return GradeResult(type="grep_headings", passed=False, detail=f"missing {rel}")
    found = {m.group(2).strip() for m in _HEADING.finditer(text)}
    required = {str(h) for h in opts.get("headings", [])}
    missing = sorted(required - found)
    extra = sorted(found - required) if opts.get("exact", True) else []
    # Require the named headings; extra headings are allowed unless exact extras matter.
    ok = not missing
    detail = "ok" if ok else f"missing headings {missing} extra={extra}"
    return GradeResult(type="grep_headings", passed=ok, detail=detail)
