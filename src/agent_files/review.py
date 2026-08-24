"""Spawn auto-review via the default Runner."""

from __future__ import annotations

import json
from pathlib import Path

from agent_files.adapters import get_runner
from agent_files.config import load_config
from agent_files.ledger import reserve
from agent_files.models.review import ReviewDocument, ReviewFinding
from agent_files.models.run import RunSpec
from agent_files.repo import find_repo_root


def review_gate(
    gate: str,
    artifact: str,
    eval_id: int | None,
    *,
    repo: Path | None = None,
    runner=None,
) -> Path:
    root = repo or find_repo_root()
    cfg = load_config(root)
    if not cfg.models:
        raise SystemExit(2)
    run_id = f"review-{gate}-{artifact.replace('/', '-')}"
    reserve(
        cfg,
        n=1,
        interactive=True,
        run_id=run_id,
        cursor_api_key=False,
        max_usd=None,
        cost_state="subscription_quota",
    )
    active = runner or get_runner(cfg.default_adapter, cfg, root)
    spec = RunSpec(
        eval_id=eval_id or 0,
        prompt=(
            "Follow the auto-review skill on this diff/eval. "
            'Write verdict ready|ready with changes|not ready to stdout as JSON '
            '{"verdict": "...", "findings": []}'
        ),
        adapter=active.name,
        model=cfg.models[0],
        timeout_seconds=cfg.timeout_seconds,
        crowded=False,
        artifact="skills/auto-review",
        overlay_root=root / "skills" / "auto-review",
        fixture_relpaths=[],
        plugin_dir=None,
        env={},
    )
    workspace = active.prepare(spec)
    completed = active.spawn(workspace, spec)
    payload: dict = {"verdict": "not ready", "findings": []}
    for line in reversed(completed.stdout.strip().splitlines()):
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and "verdict" in obj:
            payload = obj
            break
    findings = [
        ReviewFinding(summary=str(f)) if not isinstance(f, dict) else ReviewFinding(**f)
        for f in payload.get("findings") or []
    ]
    doc = ReviewDocument(
        verdict=payload.get("verdict", "not ready"),  # type: ignore[arg-type]
        findings=findings,
        gate=gate,
        artifact=artifact,
        eval_id=eval_id,
    )
    out = root / "reviews" / f"{gate}-{artifact.replace('/', '-')}-{eval_id or 'all'}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(doc.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return out
