#!/usr/bin/env python3
"""Install canonical cmize-skills directories into a host skills directory."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path


TARGET_DESTINATIONS = {
    "claude": Path("~/.claude/skills"),
    "codex": Path("~/.agents/skills"),
    "cursor": Path("~/.cursor/skills"),
}
SKILL_DEPENDENCIES = {
    "auto-review": ("adversarial-review",),
}


class InstallationError(RuntimeError):
    """Raised when an install would be unsafe or cannot be completed."""


@dataclass(frozen=True)
class InstallItem:
    source: Path
    destination: Path


def available_skills(source_root: Path) -> list[str]:
    skills_root = source_root / "skills"
    if not skills_root.is_dir():
        raise InstallationError(f"missing skill directory: {skills_root}")
    return sorted(
        path.name
        for path in skills_root.iterdir()
        if path.is_dir() and (path / "SKILL.md").is_file()
    )


def selected_skills(source_root: Path, requested: list[str] | None) -> list[str]:
    available = available_skills(source_root)
    if not requested:
        return available
    names: list[str] = []
    for value in requested:
        for name in value.split(","):
            name = name.strip()
            if name and name not in names:
                names.append(name)
    unknown = sorted(set(names) - set(available))
    if unknown:
        raise InstallationError(
            f"unknown skill(s): {', '.join(unknown)}; available: {', '.join(available)}"
        )
    resolved: list[str] = []

    def add_with_dependencies(name: str) -> None:
        for dependency in SKILL_DEPENDENCIES.get(name, ()):
            if dependency not in available:
                raise InstallationError(
                    f"skill {name!r} requires missing dependency {dependency!r}"
                )
            add_with_dependencies(dependency)
        if name not in resolved:
            resolved.append(name)

    for name in names:
        add_with_dependencies(name)
    return resolved


def build_plan(
    source_root: Path,
    destination: Path,
    requested: list[str] | None = None,
) -> list[InstallItem]:
    source_root = source_root.expanduser().resolve()
    destination = destination.expanduser().resolve()
    if not source_root.is_dir():
        raise InstallationError(f"source plugin root does not exist: {source_root}")
    if (
        destination == source_root
        or destination in source_root.parents
        or source_root in destination.parents
    ):
        raise InstallationError(
            "destination must be outside the plugin root and its parent directories"
        )
    names = selected_skills(source_root, requested)
    return [
        InstallItem(source_root / "skills" / name, destination / name)
        for name in names
    ]


def _remove_existing(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)
    else:
        raise InstallationError(f"cannot remove unsupported destination: {path}")


def execute_plan(
    plan: list[InstallItem],
    *,
    dry_run: bool = False,
    symlink: bool = False,
    replace: bool = False,
) -> list[str]:
    """Execute an already validated plan and return human-readable actions."""

    actions: list[str] = []
    for item in plan:
        if item.destination.exists() or item.destination.is_symlink():
            if replace:
                action = "replace"
            else:
                action = "refuse-existing"
        else:
            action = "symlink" if symlink else "copy"
        verb = "DRY-RUN" if dry_run else "INSTALL"
        actions.append(f"{verb} {action}: {item.source} -> {item.destination}")

    if dry_run:
        return actions

    existing = [
        item.destination
        for item in plan
        if (item.destination.exists() or item.destination.is_symlink()) and not replace
    ]
    if existing:
        formatted = ", ".join(str(path) for path in existing)
        raise InstallationError(
            f"refusing to overwrite existing skill(s): {formatted}; use --replace explicitly"
        )

    if plan:
        plan[0].destination.parent.mkdir(parents=True, exist_ok=True)
    for item in plan:
        item.destination.parent.mkdir(parents=True, exist_ok=True)
        if item.destination.exists() or item.destination.is_symlink():
            _remove_existing(item.destination)
        if symlink:
            os.symlink(str(item.source), str(item.destination), target_is_directory=True)
        else:
            shutil.copytree(item.source, item.destination, symlinks=True)
    return actions


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target",
        choices=sorted(TARGET_DESTINATIONS),
        required=True,
        help="host whose default personal skills directory should be used",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "src",
        help="canonical plugin root (default: repository src/)",
    )
    parser.add_argument(
        "--destination",
        type=Path,
        help="explicit skills directory; overrides the target default",
    )
    parser.add_argument(
        "--skills",
        nargs="+",
        help="selected skill names; comma-separated values are also accepted",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="show actions without creating or changing files",
    )
    parser.add_argument(
        "--symlink",
        action="store_true",
        help="symlink skill directories instead of copying them",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="allow replacement of existing destination skill directories",
    )
    args = parser.parse_args(argv)

    source = args.source.expanduser().resolve()
    destination = (
        args.destination
        if args.destination is not None
        else TARGET_DESTINATIONS[args.target]
    )
    try:
        plan = build_plan(source, destination, args.skills)
        actions = execute_plan(
            plan,
            dry_run=args.dry_run,
            symlink=args.symlink,
            replace=args.replace,
        )
    except (InstallationError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    for action in actions:
        print(action)
    if not plan:
        print("No skills selected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
