"""Prune always-pass evals; mark always-fail as known_gap."""

from __future__ import annotations

from pathlib import Path

from agent_files.config import load_config
from agent_files.execute import evals_path
from agent_files.github import OWNER_LOGIN, user_login
from agent_files.ledger import ledger_path, read_ledger
from agent_files.models.evalfile import EvalState, load_evals_file, write_evals_file
from agent_files.repo import find_repo_root


class PruneError(RuntimeError):
    pass


def propose(artifact: str, eval_id: int, repo: Path | None = None) -> str:
    root = repo or find_repo_root()
    cfg = load_config(root)
    entries = read_ledger(ledger_path(cfg), strict=False)
    rows = [e for e in entries if e.eval_id == eval_id and e.artifact == artifact]
    if len(rows) < 3:
        raise PruneError("need at least 3 report rows")
    variants = {e.variant_key for e in rows}
    if len(variants) < 2:
        raise PruneError("need at least 2 variants")
    data = load_evals_file(evals_path(root, artifact))
    item = data.get(eval_id)
    if item.source.state == EvalState.RELEASED:
        raise PruneError("cannot prune released evals")
    passes = [e.passed for e in rows if e.passed is not None]
    if passes and all(passes):
        return "always-pass"
    if passes and not any(passes):
        item.source.known_gap = True
        write_evals_file(evals_path(root, artifact), data)
        return "known-gap"
    raise PruneError("mixed results; not a prune candidate")


def approve(artifact: str, eval_id: int, repo: Path | None = None, login_fn=user_login) -> None:
    login = login_fn()
    if login != OWNER_LOGIN:
        raise PermissionError(f"{login} is not {OWNER_LOGIN}")
    root = repo or find_repo_root()
    data = load_evals_file(evals_path(root, artifact))
    item = data.get(eval_id)
    if item.source.known_gap:
        return
    data.evals = [e for e in data.evals if e.id != eval_id]
    write_evals_file(evals_path(root, artifact), data)
