"""Load agent-files.toml."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from agent_files.repo import find_repo_root


class GradersConfig(BaseModel):
    always_on_size_ratchet: bool = True


class ReviewConfig(BaseModel):
    required_for_freeze: bool = True
    required_for_keep: bool = True
    required_for_prune_approve: bool = True


class AppConfig(BaseModel):
    schema_version: Literal[1] = 1
    default_adapter: str = "cursor"
    models: list[str] | dict[str, list[str]] = Field(default_factory=list)
    codex_reasoning_effort: Literal["none", "minimal", "low", "medium", "high", "xhigh", "max", "ultra"] | None = None
    timeout_seconds: int = 300
    max_runs_per_invocation: int = 20
    max_runs_per_day: int = 50
    min_repeats_for_smoke: int = 3
    min_repeats_for_keep: int = 5
    improve_max_iterations: int = 3
    cache_dir: str = "~/.cache/agent-files"
    env_allowlist: list[str] = Field(
        default_factory=lambda: [
            "PATH",
            "HOME",
            "USER",
            "LANG",
            "TERM",
            "CURSOR_API_KEY",
        ]
    )
    graders: GradersConfig = Field(default_factory=GradersConfig)
    review: ReviewConfig = Field(default_factory=ReviewConfig)

    def models_for(self, adapter: str) -> list[str]:
        if isinstance(self.models, dict):
            return self.models.get(adapter, [])
        return self.models

    def cache_path(self) -> Path:
        return Path(self.cache_dir).expanduser().resolve()


def load_config(root: Path | None = None) -> AppConfig:
    repo = root or find_repo_root()
    path = repo / "agent-files.toml"
    with path.open("rb") as fh:
        data = tomllib.load(fh)
    return AppConfig.model_validate(data)
