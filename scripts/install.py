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
from pathlib import Path, PurePosixPath


MANIFEST_NAME = ".cmize-skills-manifest.json"
MANIFEST_SCHEMA_VERSION = 2
SUPPORTED_MANIFEST_SCHEMAS = {1, MANIFEST_SCHEMA_VERSION}
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
class ManagedFile:
    path: str
    kind: str
    digest: str


@dataclass(frozen=True)
class ManagedEntry:
    name: str
    path: str
    digest: str
    files: tuple[ManagedFile, ...] = ()


@dataclass(frozen=True)
class Removal:
    kind: str
    path: Path


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


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    if path.is_symlink():
        digest.update(b"symlink\0")
        digest.update(os.readlink(path).encode("utf-8"))
    elif path.is_file():
        digest.update(b"file\0")
        digest.update(path.read_bytes())
    else:
        raise InstallationError(f"cannot fingerprint unsupported file: {path}")
    return digest.hexdigest()


def managed_files(path: Path) -> tuple[ManagedFile, ...]:
    """Return the files a copied skill contributes, never directories."""

    if path.is_symlink():
        return ()
    if not path.is_dir():
        raise InstallationError(f"cannot inventory missing skill tree: {path}")
    files: list[ManagedFile] = []
    for child in sorted(path.rglob("*"), key=lambda value: str(value.relative_to(path))):
        if child.is_symlink():
            kind = "symlink"
        elif child.is_file():
            kind = "file"
        else:
            continue
        files.append(
            ManagedFile(
                path=child.relative_to(path).as_posix(),
                kind=kind,
                digest=file_digest(child),
            )
        )
    return tuple(files)


def _validate_relative_file_path(value: object, manifest_path_value: Path) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise InstallationError(
            f"manifest contains an invalid file path: {manifest_path_value}"
        )
    relative = PurePosixPath(value)
    if (
        relative.is_absolute()
        or str(relative) != value
        or any(part in {"", ".", ".."} for part in relative.parts)
    ):
        raise InstallationError(
            f"manifest contains an invalid file path: {manifest_path_value}"
        )
    return value


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
    schema_version = data.get("schema_version")
    if schema_version not in SUPPORTED_MANIFEST_SCHEMAS:
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
        if schema_version >= MANIFEST_SCHEMA_VERSION and "files" not in entry:
            raise InstallationError(f"manifest is missing its file inventory: {path}")
        files = entry.get("files", [])
        if not isinstance(files, list):
            raise InstallationError(f"manifest contains an invalid file list: {path}")
        seen_files: set[str] = set()
        for file_entry in files:
            if not isinstance(file_entry, dict):
                raise InstallationError(f"manifest contains an invalid file entry: {path}")
            file_path = _validate_relative_file_path(file_entry.get("path"), path)
            kind = file_entry.get("kind")
            file_digest_value = file_entry.get("digest")
            if (
                kind not in {"file", "symlink"}
                or not isinstance(file_digest_value, str)
                or not file_digest_value
                or file_path in seen_files
            ):
                raise InstallationError(f"manifest contains an invalid file entry: {path}")
            seen_files.add(file_path)
        seen.add(name)
    return data


def _manifest_entries(data: dict) -> dict[str, ManagedEntry]:
    return {
        entry["name"]: ManagedEntry(
            name=entry["name"],
            path=entry["path"],
            digest=entry["digest"],
            files=tuple(
                ManagedFile(
                    path=file_entry["path"],
                    kind=file_entry["kind"],
                    digest=file_entry["digest"],
                )
                for file_entry in entry.get("files", [])
            ),
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


def _ensure_file_inventory(destination: Path, entry: ManagedEntry) -> ManagedEntry:
    if entry.files:
        return entry
    root = destination / entry.path
    if root.is_symlink():
        return entry
    if not (root.exists() or root.is_symlink()):
        return entry
    if tree_digest(root) != entry.digest:
        raise InstallationError(
            f"legacy manifest has no safe file inventory for modified skill "
            f"{entry.name!r}; refusing destructive operation"
        )
    return ManagedEntry(
        name=entry.name,
        path=entry.path,
        digest=entry.digest,
        files=managed_files(root),
    )


def _serialize_entry(entry: ManagedEntry) -> dict:
    return {
        "name": entry.name,
        "path": entry.path,
        "digest": entry.digest,
        "files": [
            {
                "path": managed_file.path,
                "kind": managed_file.kind,
                "digest": managed_file.digest,
            }
            for managed_file in entry.files
        ],
    }


def build_manifest(
    source_root: Path,
    destination: Path,
    target: str,
    plan: list[InstallItem],
    symlink: bool,
    existing: dict[str, ManagedEntry] | None = None,
) -> dict:
    entries = {
        name: _ensure_file_inventory(destination, entry)
        for name, entry in (existing or {}).items()
    }
    for item in plan:
        entries[item.source.name] = ManagedEntry(
            name=item.source.name,
            path=item.destination.name,
            digest=tree_digest(item.destination),
            files=managed_files(item.source),
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
            _serialize_entry(entry)
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


def _copy_tree_into(source: Path, destination: Path) -> None:
    for child in sorted(source.iterdir(), key=lambda value: value.name):
        target = destination / child.name
        if child.is_symlink():
            if target.is_symlink():
                target.unlink()
            elif target.exists():
                if target.is_dir():
                    raise InstallationError(
                        f"refusing to replace a destination directory with a symlink: "
                        f"{target}"
                    )
                target.unlink()
            os.symlink(
                os.readlink(child),
                target,
                target_is_directory=child.is_dir(),
            )
        elif child.is_dir():
            if target.is_symlink():
                raise InstallationError(
                    f"refusing to copy through a destination symlink: {target}"
                )
            if target.exists() and not target.is_dir():
                raise InstallationError(
                    f"refusing to replace a destination file with a directory: {target}"
                )
            target.mkdir(exist_ok=True)
            _copy_tree_into(child, target)
        elif child.is_file():
            if target.is_symlink() or (target.exists() and target.is_dir()):
                raise InstallationError(
                    f"refusing to copy through a destination path: {target}"
                )
            shutil.copy2(child, target)


def _copy_skill(source: Path, destination: Path, *, symlink: bool) -> None:
    if destination.is_symlink():
        destination.unlink()
    elif destination.exists() and not destination.is_dir():
        raise InstallationError(
            f"refusing to replace non-directory skill destination: {destination}"
        )
    if symlink:
        if destination.exists():
            raise InstallationError(
                "refusing to replace a skill directory with a symlink; "
                f"preserve it and remove it manually if intended: {destination}"
            )
        os.symlink(str(source), str(destination), target_is_directory=True)
    else:
        _copy_tree_into(source, destination)


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
            _copy_skill(item.source, item.destination, symlink=symlink)
        elif symlink:
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


def _plan_removals(
    destination: Path,
    entries: dict[str, ManagedEntry],
    names: list[str],
) -> list[Removal]:
    removals: list[Removal] = []
    for name in names:
        entry = entries[name]
        root = destination / entry.path
        if not (root.exists() or root.is_symlink()):
            removals.append(Removal("missing", root))
            continue
        if root.is_symlink():
            # Unlink only the pointer; never follow or remove its target.
            removals.append(Removal("symlink", root))
            continue
        if not root.is_dir():
            raise InstallationError(
                f"refusing to remove non-directory skill destination: {root}"
            )
        inventory = _ensure_file_inventory(destination, entry)
        root_real = root.resolve()
        planned_files = 0
        for managed_file in inventory.files:
            target = root / managed_file.path
            parent_real = target.parent.resolve()
            if parent_real != root_real and root_real not in parent_real.parents:
                raise InstallationError(
                    f"manifest file escapes its skill directory: {target}"
                )
            if target.is_symlink() or target.is_file():
                removals.append(Removal("file", target))
                planned_files += 1
            elif target.exists():
                raise InstallationError(
                    f"refusing to remove a directory listed as a file: {target}"
                )
        if not planned_files:
            removals.append(Removal("preserve", root))
    return removals


def _execute_removals(
    removals: list[Removal],
    *,
    dry_run: bool,
    operation: str,
) -> list[str]:
    prefix = "DRY-RUN" if dry_run else operation
    actions = [f"{prefix} {removal.kind}: {removal.path}" for removal in removals]
    if dry_run:
        return actions
    for removal in removals:
        if removal.kind == "file" or removal.kind == "symlink":
            if removal.path.is_symlink() or removal.path.is_file():
                removal.path.unlink()
            elif removal.path.exists():
                raise InstallationError(
                    f"refusing to remove a directory: {removal.path}"
                )
    return actions


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
    existing = {
        name: _ensure_file_inventory(destination, entry)
        for name, entry in _manifest_entries(data).items()
    }
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
    stale_removals = _plan_removals(
        destination,
        existing,
        sorted(stale_names),
    )
    refresh_names = [
        name
        for name in selected_names
        if name in existing and name not in stale_names
    ]
    refresh_removals = _plan_removals(destination, existing, refresh_names)
    actions = _execute_removals(
        stale_removals,
        dry_run=dry_run,
        operation="UPDATE",
    )
    actions.extend(
        _execute_removals(
            refresh_removals,
            dry_run=dry_run,
            operation="UPDATE",
        )
    )
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
    remaining = {name: entry for name, entry in entries.items() if name in remaining_names}
    normalized = {
        name: _ensure_file_inventory(destination, entry)
        for name, entry in remaining.items()
    }
    removals = _plan_removals(destination, entries, names)
    actions = _execute_removals(
        removals,
        dry_run=dry_run,
        operation="UNINSTALL",
    )
    if dry_run:
        return actions

    if remaining:
        data["schema_version"] = MANIFEST_SCHEMA_VERSION
        data["managed_skills"] = [
            _serialize_entry(entry)
            for entry in sorted(normalized.values(), key=lambda value: value.name)
        ]
        data["updated_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        _write_manifest(manifest_path(destination), data)
    else:
        manifest_path(destination).unlink(missing_ok=True)
    return actions


def uninstall_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Remove only cmize-skills files recorded by a destination manifest."
    )
    parser.add_argument(
        "--target",
        choices=sorted(TARGET_DESTINATIONS),
        required=True,
        help="host whose default personal skills directory should be used",
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
        help="managed skill names; comma-separated values are also accepted",
    )
    selection.add_argument(
        "--all",
        action="store_true",
        help="remove every skill listed in the manifest",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="show file-level actions without changing files",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="remove manifest-listed files even if a managed skill was edited",
    )
    args = parser.parse_args(argv)
    destination = (
        args.destination
        if args.destination is not None
        else TARGET_DESTINATIONS[args.target]
    )
    try:
        actions = uninstall(
            destination,
            args.skills,
            select_all=args.all,
            dry_run=args.dry_run,
            force=args.force,
        )
    except (InstallationError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    for action in actions:
        print(action)
    if not actions:
        print("No managed files selected.")
    return 0


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
