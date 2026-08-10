"""Read release metadata from the canonical marketplace catalog."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


CANONICAL_MARKETPLACE = Path(__file__).resolve().parents[1] / ".claude-plugin" / "marketplace.json"


class MetadataError(ValueError):
    """Raised when canonical marketplace metadata is missing or invalid."""


def _read_marketplace(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MetadataError(f"cannot read canonical marketplace metadata {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise MetadataError(f"canonical marketplace metadata must be an object: {path}")
    return value


def bundle_version(repository_root: Path | None = None) -> str:
    """Return the authoritative bundle version from marketplace metadata."""

    marketplace = (
        CANONICAL_MARKETPLACE
        if repository_root is None
        else repository_root / ".claude-plugin" / "marketplace.json"
    )
    data = _read_marketplace(marketplace)
    metadata = data.get("metadata")
    version = metadata.get("version") if isinstance(metadata, dict) else None
    if not isinstance(version, str) or not version.strip():
        raise MetadataError(
            "canonical marketplace metadata.version must be a non-empty string"
        )
    return version
