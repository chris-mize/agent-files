"""Aggregate ledger into k/n report."""

from __future__ import annotations

import json
from collections import defaultdict

from agent_files.config import load_config
from agent_files.keep import same_comparison_key
from agent_files.ledger import ledger_path, read_ledger
from agent_files.models.run import RunResult
from agent_files.repo import find_repo_root


def report(*, as_json: bool = False) -> str:
    root = find_repo_root()
    cfg = load_config(root)
    entries = read_ledger(ledger_path(cfg), strict=False)
    groups: dict[tuple[object, object, object], list] = defaultdict(list)
    for entry in entries:
        if entry.eval_id is None:
            continue
        groups[(entry.eval_id, entry.variant_key, entry.model)].append(entry)
    rows = []
    for (eval_id, variant, model), items in sorted(groups.items()):
        n = len(items)
        k = sum(1 for i in items if i.passed)
        rows.append({"eval": eval_id, "variant": variant, "model": model, "k": k, "n": n})
    if as_json:
        return json.dumps({"rows": rows}, indent=2)
    lines = ["eval\tvariant\tmodel\tk/n"]
    for row in rows:
        variant = str(row["variant"] or "")[:8]
        lines.append(f"{row['eval']}\t{variant}\t{row['model']}\t{row['k']}/{row['n']}")
    return "\n".join(lines) + "\n"


def refuse_keep_compare(parent: list[RunResult], child: list[RunResult]) -> bool:
    return not same_comparison_key(parent, child)
