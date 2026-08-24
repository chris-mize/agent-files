"""Typer CLI."""

from __future__ import annotations

from pathlib import Path

import typer

from agent_files.execute import EmptyModelsError, execute
from agent_files.github import promote as promote_issue
from agent_files.install import install as install_artifacts
from agent_files.install import smoke
from agent_files.prune import PruneError
from agent_files.prune import approve as prune_approve
from agent_files.prune import propose as prune_propose
from agent_files.repo import find_repo_root
from agent_files.report import report as render_report
from agent_files.review import review_gate
from agent_files.upstream import diff_upstream

app = typer.Typer(no_args_is_help=True, add_completion=False)


@app.command()
def run(
    artifact: str = typer.Option(..., "--artifact"),
    eval_id: int | None = typer.Option(None, "--eval"),
    adapter: str | None = typer.Option(None, "--adapter"),
    repeats: int = typer.Option(1, "--repeats"),
    ablation: Path | None = typer.Option(None, "--ablation"),
    allow_cross_version: bool = typer.Option(False, "--allow-cross-version"),
    max_usd: float | None = typer.Option(None, "--max-usd"),
) -> None:
    try:
        results = execute(
            artifact=artifact,
            eval_id=eval_id,
            adapter=adapter,
            repeats=repeats,
            ablation=ablation,
            allow_cross_version=allow_cross_version,
            max_usd=max_usd,
        )
    except EmptyModelsError as exc:
        raise typer.Exit(2) from exc
    failed = [r for r in results if not r.passed and r.status != "skipped"]
    for result in results:
        typer.echo(
            f"{result.eval_id} {result.adapter} {result.model} {result.status} "
            f"skill_read={result.skill_read}"
        )
    raise typer.Exit(1 if failed else 0)


@app.command()
def report(json_out: bool = typer.Option(False, "--json")) -> None:
    typer.echo(render_report(as_json=json_out), nl=False)


@app.command()
def promote(
    issue_url: str = typer.Argument(...),
    artifact: str = typer.Option(..., "--artifact"),
    approve: bool = typer.Option(False, "--approve"),
) -> None:
    item = promote_issue(
        issue_url, artifact, approve=approve, repo=find_repo_root()
    )
    typer.echo(f"eval {item.id} state={item.source.state.value}")


@app.command()
def prune(
    artifact: str = typer.Option(..., "--artifact"),
    eval_id: int = typer.Option(..., "--eval"),
    propose: bool = typer.Option(False, "--propose"),
    approve: bool = typer.Option(False, "--approve"),
) -> None:
    try:
        if propose:
            typer.echo(prune_propose(artifact, eval_id))
        elif approve:
            prune_approve(artifact, eval_id)
            typer.echo("approved")
        else:
            raise typer.BadParameter("pass --propose or --approve")
    except PruneError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc


@app.command()
def review(
    gate: str = typer.Option(..., "--gate"),
    artifact: str = typer.Option(..., "--artifact"),
    eval_id: int | None = typer.Option(None, "--eval"),
) -> None:
    path = review_gate(gate, artifact, eval_id)
    typer.echo(str(path))


@app.command("install")
def install_cmd(
    dry_run: bool = typer.Option(False, "--dry-run"),
    uninstall: bool = typer.Option(False, "--uninstall"),
    smoke_only: bool = typer.Option(False, "--smoke"),
) -> None:
    if smoke_only:
        typer.echo(" ".join(smoke()))
        return
    for line in install_artifacts(dry_run=dry_run, uninstall=uninstall):
        typer.echo(line)


@app.command("diff-upstream")
def diff_upstream_cmd() -> None:
    lines = diff_upstream()
    if not lines:
        typer.echo("in sync")
        return
    for line in lines:
        typer.echo(line)
    raise typer.Exit(1)
