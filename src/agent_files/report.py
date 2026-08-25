"""Aggregate ledger into k/n report."""

from __future__ import annotations

import json
from collections import defaultdict

from agent_files.config import load_config
from agent_files.keep import same_comparison_key
from agent_files.ledger import LedgerEntry, ledger_path, read_ledger
from agent_files.models.run import RunResult
from agent_files.repo import find_repo_root


def _as_results(entries: list[LedgerEntry]) -> list[RunResult]:
    results: list[RunResult] = []
    for entry in entries:
        if entry.eval_id is None:
            continue
        results.append(
            RunResult.model_validate(
                {
                    "run_id": entry.run_id,
                    "eval_id": entry.eval_id,
                    "adapter": entry.adapter or "unknown",
                    "model": entry.model or "",
                    "comparison_key": entry.comparison_key,
                    "variant_key": entry.variant_key,
                    "passed": bool(entry.passed),
                    "status": "passed" if entry.passed else "failed",
                }
            )
        )
    return results


def keep_compare_message(
    parent: list[LedgerEntry],
    child: list[LedgerEntry],
    *,
    min_n: int,
) -> str:
    if not parent or not child:
        return "keep-compare refused: missing parent or child rows"
    parent_r = _as_results(parent)
    child_r = _as_results(child)
    if not same_comparison_key(parent_r, child_r):
        return "keep-compare refused: comparison_key mismatch"
    if len(parent) < min_n or len(child) < min_n:
        return f"keep-compare refused: n<{min_n}"
    return "keep-compare ok"


def report(
    *,
    as_json: bool = False,
    keep_parent: str | None = None,
    keep_child: str | None = None,
) -> str:
    root = find_repo_root()
    cfg = load_config(root)
    entries = read_ledger(ledger_path(cfg), strict=False)
    groups: dict[tuple[object, object, object], list[LedgerEntry]] = defaultdict(list)
    for entry in entries:
        if entry.eval_id is None:
            continue
        groups[(entry.eval_id, entry.variant_key, entry.model)].append(entry)
    rows = []
    for (eval_id, variant, model), items in sorted(groups.items()):
        n = len(items)
        k = sum(1 for i in items if i.passed)
        rows.append(
            {
                "eval": eval_id,
                "variant": variant,
                "model": model,
                "k": k,
                "n": n,
                "comparison_key": items[0].comparison_key,
            }
        )
    min_n = cfg.min_repeats_for_keep
    compare_notes: list[str] = []
    if keep_parent is not None or keep_child is not None:
        parent = [e for e in entries if e.variant_key == keep_parent]
        child = [e for e in entries if e.variant_key == keep_child]
        compare_notes.append(keep_compare_message(parent, child, min_n=min_n))
    else:
        by_eval_model: dict[tuple[object, object], dict[object, list[LedgerEntry]]] = defaultdict(dict)
        for (eval_id, variant, model), items in groups.items():
            by_eval_model[(eval_id, model)][variant] = items
        for (eval_id, model), variants in sorted(by_eval_model.items()):
            if len(variants) < 2:
                continue
            names = list(variants)
            parent = variants[names[0]]
            child = variants[names[1]]
            note = keep_compare_message(parent, child, min_n=min_n)
            compare_notes.append(f"eval {eval_id} {model}: {note}")
    if as_json:
        return json.dumps({"rows": rows, "keep_compare": compare_notes}, indent=2) + "\n"
    lines = ["eval\tvariant\tmodel\tk/n"]
    for row in rows:
        variant = str(row["variant"] or "")[:8]
        lines.append(f"{row['eval']}\t{variant}\t{row['model']}\t{row['k']}/{row['n']}")
    lines.extend(compare_notes)
    return "\n".join(lines) + "\n"


def refuse_keep_compare(parent: list[RunResult], child: list[RunResult]) -> bool:
    return not same_comparison_key(parent, child)
