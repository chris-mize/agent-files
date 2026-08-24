"""Comparison and variant keys."""

from __future__ import annotations

import hashlib
import json
import platform
from pathlib import Path


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes()) if path.is_file() else "missing"


def sha256_tree(root: Path) -> str:
    hasher = hashlib.sha256()
    if not root.exists():
        return hasher.hexdigest()
    paths = sorted(p for p in root.rglob("*") if p.is_file())
    for path in paths:
        rel = path.relative_to(root).as_posix().encode()
        hasher.update(rel)
        hasher.update(b"\0")
        hasher.update(path.read_bytes())
        hasher.update(b"\0")
    return hasher.hexdigest()


def dir_name_hash(path: Path) -> str:
    if not path.is_dir():
        return sha256_bytes(b"missing")
    names = sorted(p.name.encode() for p in path.iterdir())
    return sha256_bytes(b"\n".join(names))


def effective_config_hash() -> str:
    home = Path.home()
    payload = {
        "cursor": dir_name_hash(home / ".cursor"),
        "codex": dir_name_hash(home / ".codex"),
    }
    return sha256_bytes(json.dumps(payload, sort_keys=True).encode())


def comparison_key(
    *,
    fixture_hash: str,
    adapter: str,
    cli_version: str,
    model: str,
    uv_lock_hash: str,
    os_name: str | None = None,
    config_hash: str | None = None,
) -> str:
    payload = {
        "fixture_hash": fixture_hash,
        "adapter": adapter,
        "cli_version": cli_version,
        "model": model,
        "uv_lock": uv_lock_hash,
        "os": os_name or f"{platform.system()}-{platform.release()}",
        "effective_config_hash": config_hash or effective_config_hash(),
    }
    return sha256_bytes(json.dumps(payload, sort_keys=True).encode())


def variant_key(*, overlay_hash: str, eval_id: int, repeat_index: int) -> str:
    payload = {
        "overlay_hash": overlay_hash,
        "eval_id": eval_id,
        "repeat_index": repeat_index,
    }
    return sha256_bytes(json.dumps(payload, sort_keys=True).encode())


def uv_lock_hash(repo: Path) -> str:
    return sha256_file(repo / "uv.lock")
