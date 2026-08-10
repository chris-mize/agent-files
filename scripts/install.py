#!/usr/bin/env python3
"""Install canonical cmize-skills directories into a host skills directory."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from dataclasses import dataclass
from pathlib import Path


MANIFEST_NAME = ".cmize-skills-manifest.json"
MANIFEST_SCHEMA_VERSION = 1
BUNDLE_NAME = "cmize-skills"
BUNDLE_VERSION = "0.1.0"
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


@dataclass(frozen=True)
class ManagedEntry:
    name: str
    path: str
    digest: str


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
    if requested is None:
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


def tree_digest(path: Path) -> str:
    """Hash a skill tree, including relative paths and symlink targets."""

    digest = hashlib.sha256()
    if path.is_symlink():
        digest.update(b"symlink\0")
        digest.update(os.readlink(path).encode("utf-8"))
        return digest.hexdigest()
    if not path.is_dir():
        raise InstallationError(f"cannot fingerprint missing skill tree: {path}")
    for child in sorted(path.rglob("*"), key=lambda value: str(value.relative_to(path))):
        relative = child.relative_to(path).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        if child.is_symlink():
            digest.update(b"symlink\0")
            digest.update(os.readlink(child).encode("utf-8"))
        elif child.is_file():
            digest.update(b"file\0")
            digest.update(child.read_bytes())
        elif not child.is_dir():
            raise InstallationError(f"cannot fingerprint unsupported path: {child}")
    return digest.hexdigest()


def manifest_path(destination: Path) -> Path:
    return destination.expanduser().resolve() / MANIFEST_NAME


def _load_manifest(destination: Path) -> dict:
    path = manifest_path(destination)
    if not path.is_file():
        raise InstallationError(
            f"no {MANIFEST_NAME} found in {destination}; "
            "the destination is not an authoritative cmize-skills install"
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InstallationError(f"cannot read install manifest {path}: {exc}") from exc
    if not isinstance(data, dict) or data.get("bundle") != BUNDLE_NAME:
        raise InstallationError(f"manifest is not owned by {BUNDLE_NAME}: {path}")
    if data.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        raise InstallationError(f"unsupported manifest schema: {path}")
    if data.get("mode") not in {"copy", "symlink"}:
        raise InstallationError(f"manifest has an invalid installation mode: {path}")
    if data.get("destination") != str(destination.expanduser().resolve()):
        raise InstallationError(f"manifest destination does not match {destination}")
    managed = data.get("managed_skills")
    if not isinstance(managed, list) or not managed:
        raise InstallationError(f"manifest has no managed skills: {path}")
    seen: set[str] = set()
    for entry in managed:
        if not isinstance(entry, dict):
            raise InstallationError(f"manifest contains an invalid skill entry: {path}")
        name = entry.get("name")
        relative_path = entry.get("path")
        digest = entry.get("digest")
        if (
            not isinstance(name, str)
            or Path(name).name != name
            or name in {"", ".", ".."}
            or not isinstance(relative_path, str)
            or relative_path != name
            or name in seen
            or not isinstance(digest, str)
            or not digest
        ):
            raise InstallationError(f"manifest contains an invalid skill entry: {path}")
        seen.add(name)
    return data


def _manifest_entries(data: dict) -> dict[str, ManagedEntry]:
    return {
        entry["name"]: ManagedEntry(
            name=entry["name"],
            path=entry["path"],
            digest=entry["digest"],
        )
        for entry in data["managed_skills"]
    }


def _write_manifest(path: Path, data: dict) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def build_manifest(
    source_root: Path,
    destination: Path,
    target: str,
    plan: list[InstallItem],
    symlink: bool,
    existing: dict[str, ManagedEntry] | None = None,
) -> dict:
    entries = dict(existing or {})
    for item in plan:
        entries[item.source.name] = ManagedEntry(
            name=item.source.name,
            path=item.destination.name,
            digest=tree_digest(item.destination),
        )
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "bundle": BUNDLE_NAME,
        "bundle_version": BUNDLE_VERSION,
        "target": target,
        "destination": str(destination.expanduser().resolve()),
        "source_root": str(source_root),
        "source_skills_digest": tree_digest(source_root / "skills"),
        "mode": "symlink" if symlink else "copy",
        "managed_skills": [
            {
                "name": entry.name,
                "path": entry.path,
                "digest": entry.digest,
            }
            for entry in sorted(entries.values(), key=lambda value: value.name)
        ],
        "updated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }


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
    operation: str = "INSTALL",
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
        verb = "DRY-RUN" if dry_run else operation
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


def _check_managed_entries(
    destination: Path,
    entries: dict[str, ManagedEntry],
    names: list[str],
    *,
    force: bool,
) -> None:
    for name in names:
        entry = entries[name]
        path = destination / entry.path
        if not (path.exists() or path.is_symlink()):
            continue
        if tree_digest(path) != entry.digest and not force:
            raise InstallationError(
                f"managed skill {name!r} was modified; use --replace or --force "
                "only after reviewing the change"
            )


def update_install(
    source_root: Path,
    destination: Path,
    target: str,
    requested: list[str] | None,
    *,
    select_all: bool,
    dry_run: bool,
    symlink: bool,
    replace: bool,
) -> list[str]:
    data = _load_manifest(destination)
    if data.get("target") != target:
        raise InstallationError(
            f"manifest target is {data.get('target')!r}, not {target!r}"
        )
    existing = _manifest_entries(data)
    explicit_selection = requested is not None
    stored_mode = data["mode"]
    if stored_mode == "symlink" and not symlink:
        symlink = True
    if (
        explicit_selection
        and not select_all
        and ("symlink" if symlink else "copy") != stored_mode
    ):
        raise InstallationError(
            "changing installation mode for only some skills is unsafe; "
            "use --all or reinstall the destination"
        )
    available = set(available_skills(source_root))
    stale_names: set[str] = set()
    if requested is None and not select_all:
        requested = [name for name in existing if name in available]
        stale_names = set(existing) - set(requested)
    elif select_all:
        stale_names = set(existing) - available
    names = selected_skills(source_root, requested) if not select_all else None
    plan = build_plan(source_root, destination, names)
    selected_names = [item.source.name for item in plan]
    foreign = [
        item.destination
        for item in plan
        if (
            item.source.name not in existing
            and (item.destination.exists() or item.destination.is_symlink())
        )
    ]
    if foreign:
        formatted = ", ".join(str(path) for path in foreign)
        raise InstallationError(
            f"refusing to overwrite unmanaged skill(s): {formatted}; "
            "remove them or install them separately first"
        )
    _check_managed_entries(
        destination,
        existing,
        sorted(stale_names),
        force=replace,
    )
    _check_managed_entries(
        destination,
        existing,
        [name for name in selected_names if name in existing],
        force=replace,
    )
    actions = [
        f"{'DRY-RUN' if dry_run else 'UPDATE'} remove: "
        f"{destination / existing[name].path}"
        for name in sorted(stale_names)
    ]
    actions.extend(
        execute_plan(
            plan,
            dry_run=dry_run,
            symlink=symlink,
            replace=True,
            operation="UPDATE",
        )
    )
    if not dry_run:
        for name in stale_names:
            path = destination / existing[name].path
            if path.exists() or path.is_symlink():
                _remove_existing(path)
        managed = {
            name: entry
            for name, entry in existing.items()
            if name not in stale_names
        }
        _write_manifest(
            manifest_path(destination),
            build_manifest(
                source_root,
                destination,
                target,
                plan,
                symlink,
                existing=managed,
            ),
        )
    return actions


def uninstall(
    destination: Path,
    requested: list[str] | None,
    *,
    select_all: bool,
    dry_run: bool,
    force: bool,
) -> list[str]:
    destination = destination.expanduser().resolve()
    data = _load_manifest(destination)
    entries = _manifest_entries(data)
    if select_all or requested is None:
        names = sorted(entries)
    else:
        names = []
        for value in requested:
            for name in value.split(","):
                name = name.strip()
                if name and name not in names:
                    names.append(name)
        unknown = sorted(set(names) - set(entries))
        if unknown:
            raise InstallationError(
                f"skill(s) are not managed by this install: {', '.join(unknown)}"
            )
    remaining_names = set(entries) - set(names)
    blocked = sorted(
        dependent
        for dependent, dependencies in SKILL_DEPENDENCIES.items()
        if dependent in remaining_names and any(
            dependency in names for dependency in dependencies
        )
    )
    if blocked:
        raise InstallationError(
            "cannot uninstall a dependency while it is required by: "
            + ", ".join(blocked)
        )
    _check_managed_entries(destination, entries, names, force=force)
    actions: list[str] = []
    for name in names:
        path = destination / entries[name].path
        action = "missing" if not (path.exists() or path.is_symlink()) else "remove"
        actions.append(f"{'DRY-RUN' if dry_run else 'UNINSTALL'} {action}: {path}")
    if dry_run:
        return actions

    for name in names:
        path = destination / entries[name].path
        if path.exists() or path.is_symlink():
            _remove_existing(path)
    remaining = {name: entry for name, entry in entries.items() if name in remaining_names}
    if remaining:
        data["managed_skills"] = [
            {
                "name": entry.name,
                "path": entry.path,
                "digest": entry.digest,
            }
            for entry in sorted(remaining.values(), key=lambda value: value.name)
        ]
        data["updated_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        _write_manifest(manifest_path(destination), data)
    else:
        manifest_path(destination).unlink(missing_ok=True)
    return actions


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    operation = parser.add_mutually_exclusive_group()
    operation.add_argument(
        "--update",
        action="store_true",
        help="update an existing manifest-owned install",
    )
    operation.add_argument(
        "--uninstall",
        action="store_true",
        help="remove skills listed by an existing install manifest",
    )
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
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument(
        "--skills",
        nargs="+",
        help="selected skill names; comma-separated values are also accepted",
    )
    selection.add_argument(
        "--all",
        action="store_true",
        help="select every available skill (the default for a fresh install)",
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
        help="allow replacement of existing or modified managed skills",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="allow --uninstall to remove modified managed skills",
    )
    args = parser.parse_args(argv)

    source = args.source.expanduser().resolve()
    destination = (
        args.destination
        if args.destination is not None
        else TARGET_DESTINATIONS[args.target]
    )
    try:
        destination = destination.expanduser().resolve()
        if args.uninstall:
            if args.symlink or args.replace:
                parser.error("--symlink and --replace cannot be used with --uninstall")
            actions = uninstall(
                destination,
                args.skills,
                select_all=args.all,
                dry_run=args.dry_run,
                force=args.force,
            )
        elif args.update:
            if args.force:
                parser.error("--force can only be used with --uninstall")
            actions = update_install(
                source,
                destination,
                args.target,
                args.skills,
                select_all=args.all,
                dry_run=args.dry_run,
                symlink=args.symlink,
                replace=args.replace,
            )
        else:
            if args.force:
                parser.error("--force can only be used with --uninstall")
            if manifest_path(destination).exists():
                raise InstallationError(
                    f"managed install already exists at {destination}; "
                    "use --update or --uninstall"
                )
            plan = build_plan(
                source,
                destination,
                None if args.all else args.skills,
            )
            actions = execute_plan(
                plan,
                dry_run=args.dry_run,
                symlink=args.symlink,
                replace=args.replace,
            )
            if not args.dry_run:
                _write_manifest(
                    manifest_path(destination),
                    build_manifest(
                        source,
                        destination,
                        args.target,
                        plan,
                        args.symlink,
                    ),
                )
    except (InstallationError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    for action in actions:
        print(action)
    if not actions:
        print("No skills selected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
