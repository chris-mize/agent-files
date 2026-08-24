"""Run evals against a Runner."""

from __future__ import annotations

import json
import os
import sys
import uuid
from pathlib import Path

from agent_files.adapters import AdapterSkip, get_runner
from agent_files.config import AppConfig, load_config
from agent_files.grade.registry import run_graders
from agent_files.ledger import QuotaError, ledger_path, record_spawn, reserve
from agent_files.models.evalfile import EvalItem, EvalState, load_evals_file
from agent_files.models.run import RunResult, RunSpec
from agent_files.repo import find_repo_root
from agent_files.runner.base import Runner
from agent_files.runner.ephemeral import repo_porcelain
from agent_files.runner.keys import (
    comparison_key,
    sha256_file,
    sha256_tree,
    uv_lock_hash,
    variant_key,
)


class EmptyModelsError(SystemExit):
    def __init__(self) -> None:
        super().__init__(2)


def evals_path(repo: Path, artifact: str) -> Path:
    if artifact in {"agents", "agents/AGENTS.md"}:
        return repo / "agents" / "evals" / "evals.json"
    return repo / artifact / "evals" / "evals.json"


def load_provenance(repo: Path) -> dict:
    path = repo / "artifacts" / "provenance.json"
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def overlay_for(repo: Path, artifact: str, ablation: Path | None) -> Path:
    if ablation is not None:
        return ablation
    if artifact in {"agents", "agents/AGENTS.md"}:
        return repo / "agents" / "AGENTS.md"
    return repo / artifact


def baseline_bytes(provenance: dict, artifact: str) -> int | None:
    items = provenance.get("items", provenance if isinstance(provenance, list) else [])
    if isinstance(items, list):
        for row in items:
            if not isinstance(row, dict):
                continue
            path = str(row.get("path", ""))
            if "AGENTS.md" in path and artifact.startswith("agents"):
                return int(row.get("always_on_baseline_bytes") or row.get("bytes") or 0) or None
            if artifact in path:
                return int(row.get("bytes") or 0) or None
    if isinstance(provenance, dict) and "always_on_baseline_bytes" in provenance:
        return int(provenance["always_on_baseline_bytes"])
    return None


def hash_path(path: Path) -> str:
    if path.is_file():
        return sha256_file(path)
    return sha256_tree(path)


def execute(
    *,
    artifact: str,
    eval_id: int | None,
    adapter: str | None,
    repeats: int,
    ablation: Path | None = None,
    allow_cross_version: bool = False,
    max_usd: float | None = None,
    repo: Path | None = None,
    config: AppConfig | None = None,
    runner: Runner | None = None,
    interactive: bool | None = None,
) -> list[RunResult]:
    del allow_cross_version
    root = repo or find_repo_root()
    cfg = config or load_config(root)
    if not cfg.models:
        raise EmptyModelsError()
    adapter_name = adapter or cfg.default_adapter
    bundle = load_evals_file(evals_path(root, artifact))
    items = [e for e in bundle.evals if eval_id is None or e.id == eval_id]
    canary = next((e for e in bundle.evals if e.id == 1), None)
    ordered: list[EvalItem] = []
    if canary is not None and eval_id != 1:
        ordered.append(canary)
    for item in items:
        if ordered and item.id == ordered[0].id:
            continue
        ordered.append(item)
    n = max(1, len(ordered) * len(cfg.models) * repeats)
    run_id = str(uuid.uuid4())
    tty = sys.stdin.isatty() if interactive is None else interactive
    cost_state = "unknown" if os.environ.get("CURSOR_API_KEY") and max_usd is not None else "subscription_quota"
    try:
        reserve(
            cfg,
            n=n,
            interactive=tty,
            run_id=run_id,
            cursor_api_key=bool(os.environ.get("CURSOR_API_KEY")),
            max_usd=max_usd,
            cost_state=cost_state,  # type: ignore[arg-type]
        )
    except QuotaError as exc:
        raise SystemExit(exc.exit_code) from exc
    try:
        active = runner or get_runner(adapter_name, cfg, root)
    except AdapterSkip as exc:
        raise SystemExit(f"adapter skipped: {exc}") from exc
    provenance = load_provenance(root)
    results: list[RunResult] = []
    ledger = ledger_path(cfg)
    overlay = overlay_for(root, artifact, ablation)
    before_porcelain = repo_porcelain(root)
    for item in ordered:
        if item.source.state == EvalState.CANDIDATE:
            results.append(
                RunResult(
                    run_id=run_id,
                    eval_id=item.id,
                    adapter=adapter_name,
                    model=cfg.models[0],
                    comparison_key="skipped",
                    variant_key="skipped",
                    passed=False,
                    status="skipped",
                    cost_state="subscription_quota",
                )
            )
            continue
        for model in cfg.models:
            for repeat_index in range(repeats):
                spec = RunSpec(
                    eval_id=item.id,
                    prompt=item.prompt,
                    adapter=adapter_name,
                    model=model,
                    timeout_seconds=cfg.timeout_seconds,
                    crowded=item.crowded,
                    artifact=artifact,
                    overlay_root=overlay if overlay.exists() else None,
                    fixture_relpaths=item.files,
                    plugin_dir=None,
                    env={},
                    repeat_index=repeat_index,
                )
                workspace = active.prepare(spec)
                fixture_hash = ",".join(hash_path(root / rel) for rel in item.files) or "none"
                cmp = comparison_key(
                    fixture_hash=fixture_hash,
                    adapter=adapter_name,
                    cli_version=str(getattr(active, "cli_version", active.name)),
                    model=model,
                    uv_lock_hash=uv_lock_hash(root),
                )
                var = variant_key(
                    overlay_hash=hash_path(overlay) if overlay.exists() else "none",
                    eval_id=item.id,
                    repeat_index=repeat_index,
                )
                completed = active.spawn(workspace, spec)
                harvest = active.harvest(completed)
                fixture_dir = root / item.files[0] if item.files else None
                grades = run_graders(
                    workspace,
                    item,
                    overlay=overlay if overlay.is_file() else None,
                    baseline_bytes=baseline_bytes(provenance, artifact),
                    fixture_dir=fixture_dir,
                )
                passed = all(g.passed for g in grades) and not completed.timed_out
                status = "aborted" if completed.timed_out else ("passed" if passed else "failed")
                result = RunResult(
                    run_id=run_id,
                    eval_id=item.id,
                    adapter=adapter_name,
                    model=model,
                    comparison_key=cmp,
                    variant_key=var,
                    passed=passed and status == "passed",
                    status=status,  # type: ignore[arg-type]
                    grader_results=grades,
                    skill_read=harvest.skill_read,
                    fixture_skill_ids=list(spec.extra.get("fixture_ids", [])),
                    cost_state="subscription_quota",
                    timed_out=completed.timed_out,
                    duration_ms=completed.duration_ms,
                    workspace=str(workspace),
                )
                results.append(result)
                record_spawn(
                    ledger,
                    run_id=run_id,
                    comparison_key=cmp,
                    variant_key=var,
                    cost_state="subscription_quota",
                    reserved_runs=0,
                    actual_spawns=1,
                    eval_id=item.id,
                    adapter=adapter_name,
                    model=model,
                    passed=result.passed,
                    skill_read=harvest.skill_read,
                    artifact=artifact,
                )
                if item.id == 1 and not result.passed:
                    if repo_porcelain(root) != before_porcelain:
                        raise RuntimeError("agent-files git was dirtied by a failed canary run")
                    return results
    if repo_porcelain(root) != before_porcelain:
        raise RuntimeError("agent-files git was dirtied by the eval run")
    return results
