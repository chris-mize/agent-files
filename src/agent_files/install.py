"""Install artifacts using destinations from docs/spike-adapters.md."""

from __future__ import annotations

import filecmp
import json
import os
import re
import shutil
import subprocess
import tomllib
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, TypedDict

from agent_files.repo import find_repo_root

OWN_ORIGIN = "chris-mize/agent-files"
BACKUP_SUFFIX = ".agent-files-backup"


class InstallError(RuntimeError):
    pass


class InstructionRecord(TypedDict):
    dest: str
    previous_kind: Literal["absent", "symlink", "backup"]
    previous: str | None


@dataclass(frozen=True)
class InstallConfig:
    skill_destinations: list[Path]
    skill_create: list[Path]
    instructions_file: Path
    instruction_links: list[Path]


def _paths(raw: list[str]) -> list[Path]:
    return [Path(item).expanduser() for item in raw]


def _parse_spike_toml(text: str) -> InstallConfig:
    fence = re.search(r"```toml\n(.*?)```", text, re.DOTALL)
    if not fence:
        raise InstallError("no toml destinations in docs/spike-adapters.md")
    data: dict[str, Any] = tomllib.loads(fence.group(1))
    try:
        instructions = data["instructions"]
        return InstallConfig(
            skill_destinations=_paths(data["skills"]["destinations"]),
            skill_create=_paths(data["skills"].get("create", [])),
            instructions_file=Path(instructions["file"]).expanduser(),
            instruction_links=_paths(instructions["links"]),
        )
    except KeyError as exc:
        raise InstallError(f"docs/spike-adapters.md toml is missing {exc}") from exc


def _load_config(root: Path) -> InstallConfig:
    return _parse_spike_toml((root / "docs" / "spike-adapters.md").read_text(encoding="utf-8"))


def git_origin(path: Path) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    top = result.stdout.strip()
    origin = subprocess.run(
        ["git", "-C", top, "remote", "get-url", "origin"],
        capture_output=True,
        text=True,
        check=False,
    )
    if origin.returncode != 0:
        return None
    return origin.stdout.strip()


def origin_allowed(origin: str | None) -> bool:
    if origin is None:
        return True
    normalized = origin.replace(":", "/").replace(".git", "")
    return OWN_ORIGIN in normalized


def refuse_if_foreign(dest: Path) -> None:
    resolved = dest.resolve()
    origin = git_origin(resolved if resolved.is_dir() else resolved.parent)
    if not origin_allowed(origin):
        raise InstallError(f"refusing to write {dest} (resolved {resolved}); origin {origin} is not {OWN_ORIGIN}")


def _unused(path: Path) -> Path:
    candidate, n = path, 1
    while candidate.exists() or candidate.is_symlink():
        candidate = path.with_name(f"{path.name}-{n}")
        n += 1
    return candidate


def _backup_path(dest: Path) -> Path:
    """Instruction files back up beside themselves; skill folders back up outside every skill directory,
    where a host would otherwise discover the backup as a duplicate skill."""
    if dest.is_dir():
        flat = str(dest.relative_to(Path.home()) if dest.is_relative_to(Path.home()) else dest).replace("/", "_")
        return _unused(Path.home() / ".agent-files-backups" / flat.lstrip("._"))
    return _unused(dest.with_name(dest.name + BACKUP_SUFFIX))


def _plan_displacement(dest: Path) -> InstructionRecord:
    if dest.is_symlink():
        return {"dest": str(dest), "previous_kind": "symlink", "previous": os.readlink(dest)}
    if dest.exists():
        refuse_if_foreign(dest)
        return {"dest": str(dest), "previous_kind": "backup", "previous": str(_backup_path(dest))}
    return {"dest": str(dest), "previous_kind": "absent", "previous": None}


def _tree_entries(root: Path) -> dict[Path, tuple[str, bytes | str | None]]:
    entries: dict[Path, tuple[str, bytes | str | None]] = {}
    for p in root.rglob("*"):
        if "__pycache__" in p.parts or p.suffix in {".pyc", ".pyo"}:
            continue
        if p.is_symlink():
            entries[p.relative_to(root)] = ("link", os.readlink(p))
        elif p.is_dir():
            entries[p.relative_to(root)] = ("dir", None)
        else:
            entries[p.relative_to(root)] = ("file", p.read_bytes())
    return entries


def _same_tree(a: Path, b: Path) -> bool:
    return not b.is_symlink() and b.is_dir() and _tree_entries(a) == _tree_entries(b)


def _remove(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def _clear(record: InstructionRecord) -> None:
    """Empty a recorded destination so the repo copy can be written.

    The record may come from an earlier run that stopped partway, so the filesystem decides what dest holds:
    while a recorded backup is not on disk, dest is still the original and moves there; otherwise dest is
    ours, or a symlink, and is removed. A symlink is never written through.
    """
    dest = Path(record["dest"])
    backup = Path(record["previous"]) if record["previous_kind"] == "backup" and record["previous"] else None
    if backup is not None and not backup.exists() and dest.exists() and not dest.is_symlink():
        backup.parent.mkdir(parents=True, exist_ok=True)
        dest.rename(backup)
    else:
        _remove(dest)


def _restore(record: InstructionRecord) -> str | None:
    """Undo one install record. Returns a reason when the original cannot be restored, leaving dest alone."""
    dest = Path(record["dest"])
    kind, previous = record.get("previous_kind", "absent"), record.get("previous")
    if kind == "backup" and (previous is None or not Path(previous).exists()):
        return f"backup {previous} is missing"
    if not dest.parent.is_dir():
        return f"{dest.parent} no longer exists" if kind == "backup" else None
    _remove(dest)
    if kind == "symlink" and previous is not None:
        os.symlink(previous, dest)
    elif kind == "backup" and previous is not None:
        Path(previous).rename(dest)
    return None


class _Manifest:
    def __init__(self, path: Path) -> None:
        self.path = path
        data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
        self.exists = bool(data)
        self.copied: dict[str, InstructionRecord] = {
            r["dest"]: {
                "dest": r["dest"],
                "previous_kind": r.get("previous_kind", "absent"),
                "previous": r.get("previous"),
            }
            for r in data.get("copied", [])
        }
        self.instructions: dict[str, InstructionRecord] = {r["dest"]: r for r in data.get("instructions", [])}

    def save(self) -> None:
        payload = {
            "copied": list(self.copied.values()),
            "instructions": list(self.instructions.values()),
            "installed_at": datetime.now(UTC).isoformat(),
        }
        tmp = self.path.with_name(self.path.name + ".tmp")
        tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        tmp.replace(self.path)


def _install_instructions(root: Path, config: InstallConfig, manifest: _Manifest, *, dry_run: bool) -> list[str]:
    """Record how to restore each destination in the manifest before touching it."""
    src = root / "agents" / "AGENTS.md"
    home_file = config.instructions_file
    actions: list[str] = []

    def replace(dest: Path, write: Callable[[], None], label: str) -> None:
        record = manifest.instructions.get(str(dest)) or _plan_displacement(dest)
        actions.append(f"{label} (was {record['previous_kind']}: {record['previous']})")
        if dry_run:
            return
        manifest.instructions[str(dest)] = record
        manifest.save()
        _clear(record)
        write()

    if home_file.is_file() and not home_file.is_symlink() and filecmp.cmp(src, home_file, shallow=False):
        actions.append(f"unchanged {home_file}")
    else:

        def write_home() -> None:
            home_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, home_file)

        replace(home_file, write_home, f"{src} -> {home_file}")

    for link in config.instruction_links:
        if not link.parent.is_dir():
            actions.append(f"skip {link} ({link.parent} does not exist)")
        elif link.is_symlink() and Path(os.readlink(link)).expanduser() == home_file:
            actions.append(f"unchanged {link} -> {home_file}")
        else:
            replace(link, lambda link=link: link.symlink_to(home_file), f"link {link} -> {home_file}")
    return actions


def _uninstall(
    records: dict[str, InstructionRecord], manifest: _Manifest, dry_run: bool, keys: list[str] | None = None
) -> list[str]:
    actions: list[str] = []
    for dest in reversed(list(records) if keys is None else keys):
        record = records[dest]
        actions.append(f"restore {dest} ({record['previous_kind']}: {record['previous']})")
        if dry_run:
            continue
        problem = _restore(record)
        if problem:
            actions[-1] = f"leave {dest} ({problem})"
            continue
        del records[dest]
        manifest.save()
    return actions


def _skill_sources(root: Path) -> list[Path]:
    return [p for p in sorted((root / "skills").iterdir()) if p.is_dir() and not p.name.startswith("_")]


def _install_skills(root: Path, config: InstallConfig, manifest: _Manifest, *, dry_run: bool) -> list[str]:
    """Copy every skill into each destination and remove copies a previous install left elsewhere."""
    actions: list[str] = []
    sources = _skill_sources(root)
    configured = {str(dest / skill.name) for dest in config.skill_destinations for skill in sources}
    for dest in config.skill_destinations:
        if dest not in config.skill_create and not dest.parent.is_dir():
            actions.append(f"skip {dest} ({dest.parent} does not exist)")
            continue
        refuse_if_foreign(dest if dest.exists() else dest.parent)
        for skill in sources:
            target = dest / skill.name
            record = manifest.copied.get(str(target))
            if record is not None and _same_tree(skill, target):
                actions.append(f"unchanged {target}")
                continue
            if record is None:
                record = _plan_displacement(target)
            actions.append(f"{skill} -> {target} (was {record['previous_kind']}: {record['previous']})")
            if dry_run:
                continue
            manifest.copied[str(target)] = record
            manifest.save()
            _clear(record)
            dest.mkdir(parents=True, exist_ok=True)
            shutil.copytree(skill, target, symlinks=True, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    stale = [dest for dest in manifest.copied if dest not in configured]
    for line in _uninstall(manifest.copied, manifest, dry_run, stale):
        actions.append(f"remove stale {line.removeprefix('restore ')}")
    return actions


def install(
    *,
    dry_run: bool = False,
    uninstall: bool = False,
    repo: Path | None = None,
) -> list[str]:
    root = repo or find_repo_root()
    config = _load_config(root)
    actions: list[str] = []
    manifest = _Manifest(Path.home() / ".agent-files-install-manifest.json")
    if uninstall:
        if not manifest.exists:
            raise InstallError("no install manifest")
        actions.extend(_uninstall(manifest.copied, manifest, dry_run))
        actions.extend(_uninstall(manifest.instructions, manifest, dry_run))
        if not dry_run and not manifest.instructions and not manifest.copied:
            manifest.path.unlink()
        return actions
    actions.extend(_install_instructions(root, config, manifest, dry_run=dry_run))
    actions.extend(_install_skills(root, config, manifest, dry_run=dry_run))
    return actions


def smoke(repo: Path | None = None) -> list[str]:
    root = repo or find_repo_root()
    config = _load_config(root)
    src = root / "agents" / "AGENTS.md"
    home_file = config.instructions_file
    problems: list[str] = []
    if home_file.is_symlink() or not home_file.is_file():
        problems.append(f"{home_file} is not a regular file")
    elif not filecmp.cmp(src, home_file, shallow=False):
        problems.append(f"{home_file} differs from {src}")
    for link in config.instruction_links:
        if link.parent.is_dir() and not (link.is_symlink() and Path(os.readlink(link)).expanduser() == home_file):
            problems.append(f"{link} is not a symlink to {home_file}")
    installed: list[str] = []
    for dest in config.skill_destinations:
        if dest not in config.skill_create and not dest.parent.is_dir():
            continue
        for skill in _skill_sources(root):
            if _same_tree(skill, dest / skill.name):
                installed.append(str(dest / skill.name))
            else:
                problems.append(f"{dest / skill.name} differs from {skill}")
    if problems:
        raise InstallError(f"not installed: {'; '.join(problems)}; run `./install.sh`")
    return installed


def main(argv: list[str] | None = None) -> None:
    import argparse

    parser = argparse.ArgumentParser(prog="agent-files-install")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--uninstall", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args(argv)
    if args.smoke:
        print(" ".join(smoke()))
        return
    for line in install(dry_run=args.dry_run, uninstall=args.uninstall):
        print(line)


if __name__ == "__main__":
    main()
