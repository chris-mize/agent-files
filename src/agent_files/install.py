"""Install artifacts using destinations from docs/spike-adapters.md."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from agent_files.repo import find_repo_root

OWN_ORIGIN = "chris-mize/agent-files"


class InstallError(RuntimeError):
    pass


def _parse_spike_toml(text: str) -> dict[str, str]:
    fence = re.search(r"```toml\n(.*?)```", text, re.DOTALL)
    if not fence:
        raise InstallError("no toml destinations in docs/spike-adapters.md")
    dest: dict[str, str] = {}
    section = None
    for line in fence.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1]
            continue
        if "=" in line and section == "destinations":
            key, value = line.split("=", 1)
            dest[key.strip()] = value.strip().strip('"')
    return dest


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
        raise InstallError(
            f"refusing to write {dest} (resolved {resolved}); origin {origin} is not {OWN_ORIGIN}"
        )


def install(
    *,
    dry_run: bool = False,
    uninstall: bool = False,
    repo: Path | None = None,
) -> list[str]:
    root = repo or find_repo_root()
    spike = (root / "docs" / "spike-adapters.md").read_text(encoding="utf-8")
    destinations = _parse_spike_toml(spike)
    actions: list[str] = []
    manifest_path = Path.home() / ".agent-files-install-manifest.json"
    if uninstall:
        if not manifest_path.is_file():
            raise InstallError("no install manifest")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for item in manifest.get("copied", []):
            path = Path(item["dest"])
            if path.exists() and not dry_run:
                shutil.rmtree(path) if path.is_dir() else path.unlink()
            actions.append(f"remove {path}")
        if not dry_run:
            manifest_path.unlink()
        return actions
    copied: list[dict[str, str]] = []
    skill_root = root / "skills"
    for _name, raw in destinations.items():
        dest = Path(raw).expanduser()
        refuse_if_foreign(dest)
        dest.mkdir(parents=True, exist_ok=True)
        for skill in skill_root.iterdir():
            if not skill.is_dir() or skill.name.startswith("_"):
                continue
            target = dest / skill.name
            refuse_if_foreign(target)
            actions.append(f"{skill} -> {target}")
            if not dry_run:
                if target.exists():
                    shutil.rmtree(target)
                shutil.copytree(skill, target)
                copied.append({"src": str(skill), "dest": str(target)})
    if not dry_run:
        manifest_path.write_text(
            json.dumps(
                {"copied": copied, "installed_at": datetime.now(UTC).isoformat()},
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    return actions


def smoke(repo: Path | None = None) -> list[str]:
    root = repo or find_repo_root()
    spike = (root / "docs" / "spike-adapters.md").read_text(encoding="utf-8")
    destinations = _parse_spike_toml(spike)
    found: list[str] = []
    wanted = {"best-practices", "improve-against-evals"}
    for raw in destinations.values():
        dest = Path(raw).expanduser()
        if not dest.is_dir():
            continue
        names = {p.name for p in dest.iterdir() if p.is_dir()}
        found.extend(sorted(wanted & names))
    if not found:
        raise InstallError(
            "host smoke failed: neither improve-against-evals nor best-practices listed in skill dirs"
        )
    return found


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
