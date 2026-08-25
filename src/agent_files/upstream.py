"""Compare provenance hashes to original import paths."""

from __future__ import annotations

import json
from pathlib import Path

from agent_files.repo import find_repo_root
from agent_files.runner.keys import sha256_file, sha256_tree


def sha256_any(path: Path) -> str:
    if path.is_dir():
        return sha256_tree(path)
    return sha256_file(path)


def diff_upstream(repo: Path | None = None) -> list[str]:
    root = repo or find_repo_root()
    provenance = json.loads((root / "artifacts" / "provenance.json").read_text())
    items = provenance if isinstance(provenance, list) else provenance.get("items", [])
    lines: list[str] = []
    for row in items:
        src = Path(row["source_path"]).expanduser()
        dst = root / row["path"]
        if not src.exists():
            lines.append(f"missing source {src}")
            continue
        current = sha256_any(src)
        recorded = str(row.get("sha256", "")).removeprefix("sha256:")
        if current != recorded:
            lines.append(f"changed {row['path']}: source now {current}")
        elif dst.exists() and sha256_any(dst) != current:
            lines.append(f"drift {row['path']}: repo copy differs from source")
    return lines
