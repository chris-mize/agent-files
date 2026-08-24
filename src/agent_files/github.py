"""GitHub issue intake via `gh`."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from agent_files.execute import evals_path
from agent_files.models.evalfile import (
    EvalItem,
    EvalsFile,
    EvalSource,
    EvalState,
    load_evals_file,
    write_evals_file,
)

OWNER_LOGIN = "chris-mize"
OWNER_LOGIN = OWNER_LOGIN


class GhError(RuntimeError):
    pass


def run_gh(args: list[str]) -> str:
    result = subprocess.run(
        ["gh", *args], capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        raise GhError(result.stderr.strip() or result.stdout.strip())
    return result.stdout


def user_login() -> str:
    return run_gh(["api", "user", "--jq", ".login"]).strip()


user_login = user_login


def issue_view(url: str) -> dict[str, Any]:
    return json.loads(run_gh(["issue", "view", url, "--json", "number,title,body,url"]))


def create_issue(title: str, body: str) -> str:
    return run_gh(["issue", "create", "--title", title, "--body", body]).strip()


def promote(
    issue_url: str,
    artifact: str,
    *,
    approve: bool,
    repo: Path,
    login_fn=user_login,
    view_fn=issue_view,
) -> EvalItem:
    issue = view_fn(issue_url)
    body = str(issue.get("body") or "")
    prompt = (
        body
        + "\n\nWrite SPEC.md in the workspace. Do not rely on this issue thread remaining available.\n"
    )
    digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    prompt_hash = "sha256:" + digest
    candidate_dir = repo / "evals" / "candidates"
    candidate_dir.mkdir(parents=True, exist_ok=True)
    prompt_file = candidate_dir / f"{digest}.txt"
    prompt_file.write_text(prompt, encoding="utf-8")
    path = evals_path(repo, artifact)
    data = load_evals_file(path) if path.is_file() else None
    next_id = (max((e.id for e in data.evals), default=0) + 1) if data else 1
    state = EvalState.CANDIDATE
    approved_by = None
    if approve:
        login = login_fn()
        if login != OWNER_LOGIN:
            raise PermissionError(f"{login} is not {OWNER_LOGIN}")
        state = EvalState.APPROVED
        approved_by = login
    item = EvalItem(
        id=next_id,
        prompt="" if state == EvalState.CANDIDATE else prompt,
        expected_output="Standalone SPEC.md",
        files=["agents/evals/files/standalone-spec"],
        crowded=True,
        source=EvalSource(
            state=state,
            issue=str(issue.get("url") or issue_url),
            prompt_hash=prompt_hash,
            prompt_file=str(prompt_file.relative_to(repo)),
            approved_by=approved_by,
        ),
    )
    if data is None:
        data = EvalsFile(schema_version=1, skill_name=artifact, evals=[item])
    else:
        data.evals.append(item)
    write_evals_file(path, data)
    return item
