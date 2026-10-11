#!/usr/bin/env python3
"""Run local structural smoke checks for one actor-critic-mode host."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


COMMON_REFERENCES = (
    "protocol.md",
    "routing.md",
    "evaluation.md",
    "research-ledger.md",
)


def require(path: Path, text: str) -> None:
    if not path.exists():
        raise AssertionError(f"missing {path}")
    if text and text not in path.read_text(encoding="utf-8"):
        raise AssertionError(f"{text!r} missing from {path}")


def check_skill(skill: Path, host: str) -> None:
    text = skill.joinpath("SKILL.md").read_text(encoding="utf-8")
    if not re.search(r"\A---\n.*\n---", text, re.DOTALL):
        raise AssertionError(f"invalid frontmatter in {skill / 'SKILL.md'}")
    require(skill / "SKILL.md", "name: actor-critic-mode")
    require(skill / "SKILL.md", "references/protocol.md")
    for reference in COMMON_REFERENCES:
        require(skill / "references" / reference, "")
    require(skill / "scripts" / "evaluate_runs.py", "")
    require(skill / "scripts" / "capability_probe.py", "")
    require(skill / "scripts" / "smoke_protocol.py", "")
    if host == "cursor":
        require(skill / "SKILL.md", "disable-model-invocation: true")
        for role in (
            Path.home() / ".cursor/agents/actor-critic-generator.md",
            Path.home() / ".cursor/agents/actor-critic-critic.md",
        ):
            require(role, "name:")
            require(role, "model:")
            require(role, "readonly:")
    elif host == "codex":
        require(skill / "agents/openai.yaml", "allow_implicit_invocation: false")
        for role in (
            Path.home() / ".codex/agents/actor_critic_generator.toml",
            Path.home() / ".codex/agents/actor_critic_critic.toml",
        ):
            require(role, "name =")
            require(role, "model =")
            require(role, "sandbox_mode =")
    else:
        require(skill / "SKILL.md", "disable-model-invocation: true")


def check_bounded_loop() -> None:
    max_revisions = 2
    revision_count = 0
    verdicts = ("REVISE", "REVISE", "REVISE")
    for verdict in verdicts:
        if verdict != "REVISE":
            break
        if revision_count >= max_revisions:
            break
        revision_count += 1
    assert revision_count == max_revisions


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", choices=("claude", "codex", "cursor"), required=True)
    args = parser.parse_args()
    skill_dirs = {
        "claude": (".claude/skills",),
        "codex": (".agents/skills", ".codex/skills"),
        "cursor": (".cursor/skills",),
    }
    skill = None
    for skill_dir in skill_dirs[args.host]:
        candidate = Path.home() / skill_dir / "actor-critic-mode"
        if candidate.is_dir():
            skill = candidate
            break
    if skill is None:
        skill = Path.home() / skill_dirs[args.host][0] / "actor-critic-mode"
    check_skill(skill, args.host)
    check_bounded_loop()
    result = subprocess.run(
        [sys.executable, str(skill / "scripts/evaluate_runs.py"), "--self-test"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise AssertionError(result.stderr or result.stdout)
    probe = subprocess.run(
        [sys.executable, str(skill / "scripts/capability_probe.py"), "--self-test"],
        check=False,
        capture_output=True,
        text=True,
    )
    if probe.returncode:
        raise AssertionError(probe.stderr or probe.stdout)
    print(f"{args.host} protocol smoke: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
