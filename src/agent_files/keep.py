"""Keep-gate comparison."""

from __future__ import annotations

from dataclasses import dataclass

from agent_files.config import AppConfig
from agent_files.models.run import RunResult


@dataclass
class KeepDecision:
    keep: bool
    reason: str
    isolation_only: bool = False


def k_of_n(results: list[RunResult], eval_id: int) -> tuple[int, int]:
    subset = [r for r in results if r.eval_id == eval_id and r.status != "skipped"]
    n = len(subset)
    k = sum(1 for r in subset if r.passed)
    return k, n


def same_comparison_key(parent: list[RunResult], child: list[RunResult]) -> bool:
    p = {r.comparison_key for r in parent if r.comparison_key != "skipped"}
    c = {r.comparison_key for r in child if r.comparison_key != "skipped"}
    return bool(p) and p == c


def isolation_only_win(parent: list[RunResult], child: list[RunResult]) -> bool:
    parent_c = [r for r in parent if r.fixture_skill_ids]
    child_c = [r for r in child if r.fixture_skill_ids]
    if not parent_c or not child_c:
        return False
    pk, pn = k_of_n(parent_c, parent_c[0].eval_id)
    ck, cn = k_of_n(child_c, child_c[0].eval_id)
    crowded_better = (ck / cn if cn else 0) > (pk / pn if pn else 0)
    parent_iso = [r for r in parent if not r.fixture_skill_ids]
    child_iso = [r for r in child if not r.fixture_skill_ids]
    iso_better = False
    if parent_iso and child_iso:
        pik, pin = k_of_n(parent_iso, parent_iso[0].eval_id)
        cik, cin = k_of_n(child_iso, child_iso[0].eval_id)
        iso_better = (cik / cin if cin else 0) > (pik / pin if pin else 0)
    marker_better = any(c.skill_read != "skipped" for c in child) and all(
        p.skill_read == "skipped" for p in parent
    )
    return (iso_better or marker_better) and not crowded_better


def decide_keep(
    config: AppConfig,
    parent: list[RunResult],
    child: list[RunResult],
    *,
    allow_cross_version: bool,
    parent_bytes: int,
    child_bytes: int,
    leak_passed: bool,
    review_ok: bool,
    skill_read_ok: bool,
) -> KeepDecision:
    if not allow_cross_version and not same_comparison_key(parent, child):
        return KeepDecision(False, "comparison_key mismatch")
    eval_ids = sorted({r.eval_id for r in parent + child if r.status != "skipped"})
    for eid in eval_ids:
        ck, cn = k_of_n(child, eid)
        pk, pn = k_of_n(parent, eid)
        if cn < config.min_repeats_for_keep or pn < config.min_repeats_for_keep:
            return KeepDecision(False, f"eval {eid} n<{config.min_repeats_for_keep}")
        if ck < pk:
            return KeepDecision(False, f"eval {eid} regression {ck}/{cn} < {pk}/{pn}")
    if isolation_only_win(parent, child):
        return KeepDecision(False, "isolation-only win; revert", isolation_only=True)
    if eval_ids and child_bytes > parent_bytes:
        ck, _cn = k_of_n(child, eval_ids[-1])
        pk, _pn = k_of_n(parent, eval_ids[-1])
        if not (ck > pk and leak_passed):
            return KeepDecision(False, "size ratchet")
    if not leak_passed:
        return KeepDecision(False, "leak")
    if not skill_read_ok:
        return KeepDecision(False, "skill_read skipped")
    if not review_ok:
        return KeepDecision(False, "review not ready")
    return KeepDecision(True, "keep")
