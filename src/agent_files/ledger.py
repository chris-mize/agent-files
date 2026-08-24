"""JSONL run ledger and quota reservation."""

from __future__ import annotations

import fcntl
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ValidationError

from agent_files.config import AppConfig

CostState = Literal["subscription_quota", "metered", "unknown", "reserved"]


class LedgerEntry(BaseModel):
    run_id: str
    comparison_key: str
    variant_key: str
    cost_state: CostState
    reserved_runs: int = 0
    actual_spawns: int = 0
    review_path: str | None = None
    started_at: str
    finished_at: str | None = None
    eval_id: int | None = None
    adapter: str | None = None
    model: str | None = None
    passed: bool | None = None
    skill_read: str | None = None
    artifact: str | None = None


class QuotaError(Exception):
    def __init__(self, message: str, exit_code: int = 2) -> None:
        super().__init__(message)
        self.exit_code = exit_code


def ledger_path(config: AppConfig) -> Path:
    return config.cache_path() / "ledger.jsonl"


def _lock_path(path: Path) -> Path:
    return path.with_suffix(path.suffix + ".lock")


def _parse_line(line: str) -> LedgerEntry | None:
    line = line.strip()
    if not line:
        return None
    return LedgerEntry.model_validate_json(line)


def read_ledger(path: Path, *, strict: bool) -> list[LedgerEntry]:
    if not path.is_file():
        if strict:
            raise QuotaError(f"ledger missing: {path}")
        return []
    entries: list[LedgerEntry] = []
    try:
        for raw in path.read_text(encoding="utf-8").splitlines():
            parsed = _parse_line(raw)
            if parsed is not None:
                entries.append(parsed)
    except (OSError, ValidationError, json.JSONDecodeError) as exc:
        if strict:
            raise QuotaError(f"ledger unreadable: {path}") from exc
        raise
    return entries


def append_entry(path: Path, entry: LedgerEntry) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = _lock_path(path)
    lock.touch(exist_ok=True)
    with lock.open("a+", encoding="utf-8") as lock_fh:
        fcntl.flock(lock_fh.fileno(), fcntl.LOCK_EX)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(entry.model_dump_json() + "\n")


def today_spawn_count(entries: list[LedgerEntry], *, now: datetime | None = None) -> int:
    day = (now or datetime.now(UTC)).date().isoformat()
    total = 0
    for entry in entries:
        started = entry.started_at[:10]
        if started == day:
            total += max(entry.actual_spawns, entry.reserved_runs)
    return total


def reserve(
    config: AppConfig,
    *,
    n: int,
    interactive: bool,
    run_id: str,
    cursor_api_key: bool,
    max_usd: float | None,
    cost_state: CostState,
    ledger: Path | None = None,
) -> None:
    if cost_state == "unknown" and max_usd is not None:
        raise QuotaError("cost_state unknown with --max-usd")
    if cursor_api_key and max_usd is not None and cost_state != "metered":
        raise QuotaError("CURSOR_API_KEY present but usage is not metered")
    if not interactive and n > config.max_runs_per_invocation:
        raise QuotaError(
            f"non-interactive run {n} exceeds max_runs_per_invocation "
            f"{config.max_runs_per_invocation}"
        )
    if n > config.max_runs_per_invocation:
        raise QuotaError(
            f"requested {n} runs exceeds max_runs_per_invocation "
            f"{config.max_runs_per_invocation}"
        )
    path = ledger or ledger_path(config)
    strict = path.is_file()
    entries = read_ledger(path, strict=strict)
    used = today_spawn_count(entries)
    if used + n > config.max_runs_per_day:
        raise QuotaError(
            f"quota reserve {n} would exceed max_runs_per_day "
            f"{config.max_runs_per_day} (already {used})"
        )
    append_entry(
        path,
        LedgerEntry(
            run_id=run_id,
            comparison_key="reserve",
            variant_key="reserve",
            cost_state="reserved",
            reserved_runs=n,
            actual_spawns=0,
            started_at=datetime.now(UTC).isoformat(),
        ),
    )


def record_spawn(path: Path, **kwargs: Any) -> None:
    kwargs.setdefault("started_at", datetime.now(UTC).isoformat())
    kwargs.setdefault("finished_at", datetime.now(UTC).isoformat())
    append_entry(path, LedgerEntry.model_validate(kwargs))


record_spawn = record_spawn
read_ledger = read_ledger
