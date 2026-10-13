from __future__ import annotations

import re
from pathlib import Path

import pytest

from agent_files.repo import find_repo_root

SKILLS = find_repo_root() / "skills"
SKILL_DIRS = sorted(p for p in SKILLS.iterdir() if p.is_dir() and not p.name.startswith("_"))
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LINK_RE = re.compile(r"\]\(([^)\s]+)(?:\s+['\"][^'\"]*['\"])?\)")
MACHINE_PATH_RE = re.compile(
    r"(?:/Users/|/home/|/private/(?:var|tmp)/|/(?:tmp|var)/|"
    r"~/(?:\.codex|\.claude|\.cursor|\.agents|\.config)|"
    r"(?<![A-Za-z])[A-Za-z]:[\\/]|\\\\)"
)
IMPLICIT_INVOCATION = {
    "agent-files-sync": False,
    "auto-review": False,
    "actor-critic-mode": False,
    "reset-cursor-vscode-macos": False,
    "deep-research": True,
}


def frontmatter(text: str) -> dict[str, str]:
    lines = text.splitlines()
    assert lines and lines[0].strip() == "---", "missing opening frontmatter delimiter"
    end = lines.index("---", 1)
    values: dict[str, str] = {}
    for line in lines[1:end]:
        if not line.strip():
            continue
        key, value = line.split(":", 1)
        value = value.strip()
        assert not value.startswith((">", "|")), f"multiline frontmatter is not supported: {key}"
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[key.strip()] = value
    return values


def skill_files(skill: Path) -> list[Path]:
    return [
        p for p in skill.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix not in {".pyc", ".pyo"}
    ]


@pytest.mark.parametrize("skill", SKILL_DIRS, ids=lambda p: p.name)
def test_skill_frontmatter(skill: Path) -> None:
    text = (skill / "SKILL.md").read_text(encoding="utf-8")
    assert len(text.splitlines()) < 500
    meta = frontmatter(text)
    assert NAME_RE.fullmatch(meta.get("name", ""))
    assert meta["name"] == skill.name
    assert 0 < len(meta.get("description", "").strip()) <= 1024


@pytest.mark.parametrize("skill", SKILL_DIRS, ids=lambda p: p.name)
def test_skill_is_portable_across_machines(skill: Path) -> None:
    for path in skill_files(skill):
        contents = path.read_text(encoding="utf-8")
        assert not MACHINE_PATH_RE.search(contents), f"{path} contains a machine-specific absolute path"
        for match in LINK_RE.finditer(contents):
            target = match.group(1)
            if target.startswith(("http://", "https://", "mailto:", "#", "data:")):
                continue
            assert not target.startswith(("/", "~")), f"{path} links outside the skill: {target}"
            resolved = (path.parent / target.split("#", 1)[0].split("?", 1)[0]).resolve()
            assert resolved.is_relative_to(SKILLS.resolve()), f"{path} links outside skills/: {target}"
            assert resolved.exists(), f"{path} links to missing path: {target}"


@pytest.mark.parametrize("name,allowed", sorted(IMPLICIT_INVOCATION.items()))
def test_codex_invocation_policy(name: str, allowed: bool) -> None:
    text = (SKILLS / name / "agents" / "openai.yaml").read_text(encoding="utf-8")
    match = re.search(r"allow_implicit_invocation:\s*(true|false)\s*$", text, re.MULTILINE)
    assert match is not None and (match.group(1) == "true") == allowed
