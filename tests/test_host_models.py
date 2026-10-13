"""Adapter model selection and host invocation regressions."""

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

import pytest
from typer.testing import CliRunner

from agent_files.adapters import codex as codex_module
from agent_files.adapters.fake import FakeRunner
from agent_files.cli import app
from agent_files.config import AppConfig, load_config
from agent_files.execute import EmptyModelsError, PromptError, execute
from agent_files.ledger import LedgerEntry, ledger_path, read_ledger, today_spawn_count
from agent_files.models.evalfile import load_evals_file
from agent_files.models.run import CompletedRun, RunSpec
from agent_files.review import review_gate

REPO = Path(__file__).resolve().parents[1]


class RecordingFake(FakeRunner):
    def __init__(self, config: AppConfig, repo: Path) -> None:
        super().__init__(config, repo)
        self.specs: list[RunSpec] = []

    def spawn(self, workspace: Path, spec: RunSpec) -> CompletedRun:
        self.specs.append(spec)
        return super().spawn(workspace, spec)


@pytest.mark.parametrize("models", [["first", "second"], {"fake": ["first", "second"], "codex": ["other"]}])
def test_run_selects_models_and_checks_canaries_once(tmp_path: Path, models: list[str] | dict[str, list[str]]) -> None:
    cfg = AppConfig(models=models, cache_dir=str(tmp_path), max_runs_per_invocation=8)
    runner = RecordingFake(cfg, REPO)
    results = execute(
        artifact="agents", eval_id=3, adapter="fake", repeats=3,
        repo=REPO, config=cfg, runner=runner, interactive=False,
    )
    assert [(r.eval_id, r.model) for r in results] == [
        (1, "first"), (1, "second"),
        *[(3, model) for model in ("first", "second") for _ in range(3)],
    ]
    assert all(r.passed for r in results)
    assert [s.repeat_index for s in runner.specs if s.eval_id == 3] == [0, 1, 2, 0, 1, 2]
    rel = load_evals_file(REPO / "agents/evals/evals.json").get(3).source.prompt_file
    assert rel is not None
    assert all(s.prompt == (REPO / rel).read_text() for s in runner.specs if s.eval_id == 3)
    entries = read_ledger(ledger_path(cfg), strict=True)
    assert entries[0].reserved_runs == 8
    assert sum(e.actual_spawns for e in entries) == 8


@pytest.mark.parametrize("models", [{"cursor": ["other"]}, {"fake": []}])
def test_unconfigured_adapter_exits_before_reserving(tmp_path: Path, models: dict[str, list[str]]) -> None:
    cfg = AppConfig(models=models, cache_dir=str(tmp_path))
    with pytest.raises(EmptyModelsError) as exc:
        execute(artifact="agents", eval_id=3, adapter="fake", repeats=3, repo=REPO, config=cfg)
    assert exc.value.code == 2
    assert not ledger_path(cfg).exists()


def test_load_adapter_models_from_toml(tmp_path: Path) -> None:
    (tmp_path / "agent-files.toml").write_text('[models]\ncursor = ["opus"]\nfake = ["fake"]\n')
    cfg = load_config(tmp_path)
    assert cfg.models_for("cursor") == ["opus"]
    assert cfg.models_for("fake") == ["fake"]
    assert cfg.models_for("codex") == []


@pytest.mark.parametrize("command", ["run", "review"])
def test_cli_explains_missing_models(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, command: str) -> None:
    (tmp_path / "agent-files.toml").write_text('[models]\nfake = []\n')
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "agent-files"\n')
    monkeypatch.chdir(tmp_path)
    args = [command, "--artifact", "agents", "--adapter", "fake"]
    if command == "review":
        args += ["--gate", "freeze"]
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 2
    assert "no models configured for adapter fake" in result.output


@pytest.mark.parametrize("adapter", [None, "fake"])
def test_review_selects_adapter_model(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, adapter: str | None) -> None:
    from agent_files import review

    cfg = AppConfig(default_adapter="fake", models={"fake": ["review-model"], "cursor": ["other"]},
                    cache_dir=str(tmp_path / "cache"))
    runner = RecordingFake(cfg, tmp_path)
    (tmp_path / "reviews").mkdir()
    monkeypatch.setattr(review, "load_config", lambda _root: cfg)
    review_gate("freeze", "agents", 3, repo=tmp_path, runner=runner, adapter=adapter)
    assert [s.model for s in runner.specs] == ["review-model"]


@pytest.mark.parametrize("effort", [None, "high"])
def test_codex_model_is_option_value(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, effort: str | None) -> None:
    spec = RunSpec(eval_id=1, prompt="Write the canary", adapter="codex", model="catalog-model",
                   timeout_seconds=30, crowded=False, artifact="agents", overlay_root=None,
                   fixture_relpaths=[], plugin_dir=None, env={}, extra={"codex_home": str(tmp_path)})
    captured: list[str] = []

    def capture(argv: list[str], **_kwargs: object) -> CompletedRun:
        captured.extend(argv)
        return CompletedRun(tmp_path, 0, "", "", False, 0, None, argv)

    monkeypatch.setattr(codex_module.shutil, "which", lambda _name: "/bin/codex")
    monkeypatch.setattr(codex_module, "spawn_process", capture)
    cfg = AppConfig.model_validate({"codex_reasoning_effort": effort})
    codex_module.CodexRunner(cfg, tmp_path).spawn(tmp_path, spec)
    assert captured[-3:] == ["-m", "catalog-model", "Write the canary"]
    if effort is None:
        assert "-c" not in captured
    else:
        assert captured[captured.index("-c") + 1] == 'model_reasoning_effort="high"'


def test_explicit_canary_honors_repeats(tmp_path: Path) -> None:
    cfg = AppConfig(models=["fake"], cache_dir=str(tmp_path), max_runs_per_invocation=3)
    results = execute(artifact="agents", eval_id=1, adapter="fake", repeats=3, repo=REPO, config=cfg)
    assert len(results) == 3
    assert all(r.passed for r in results)
    entries = read_ledger(ledger_path(cfg), strict=True)
    assert entries[0].reserved_runs == 3
    assert today_spawn_count(entries) == 3


@pytest.mark.parametrize("missing", [True, False])
def test_invalid_prompt_stops_before_canary_or_reservation(tmp_path: Path, missing: bool) -> None:
    repo = tmp_path / "repo"
    shutil.copytree(REPO / "agents", repo / "agents")
    bundle = load_evals_file(repo / "agents/evals/evals.json")
    rel = bundle.get(3).source.prompt_file
    assert rel is not None
    if not missing:
        p = repo / rel
        p.parent.mkdir(parents=True)
        p.write_text("mismatched prompt")
    cfg = AppConfig(models=["fake"], cache_dir=str(tmp_path / "cache"))
    runner = RecordingFake(cfg, repo)
    with pytest.raises(PromptError, match="missing prompt file" if missing else "prompt hash mismatch"):
        execute(artifact="agents", eval_id=3, adapter="fake", repeats=3, repo=repo, config=cfg, runner=runner)
    assert runner.specs == []
    assert not ledger_path(cfg).exists()


def test_comparison_identity_changes_with_prompt_and_effort(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    shutil.copytree(REPO / "agents", repo / "agents")
    results = []
    for index, (effort, prompt) in enumerate([("high", "canary"), ("low", "canary"), ("high", "canary changed")]):
        path = repo / "agents/evals/evals.json"
        bundle = json.loads(path.read_text())
        bundle["evals"][0]["prompt"] = prompt
        path.write_text(json.dumps(bundle))
        cfg = AppConfig.model_validate({"models": ["same-model"], "codex_reasoning_effort": effort,
                                        "cache_dir": str(tmp_path / f"cache-{index}")})
        results.extend(execute(artifact="agents", eval_id=1, adapter="codex", repeats=1, repo=repo,
                               config=cfg, runner=RecordingFake(cfg, repo)))
    assert all(r.passed for r in results)
    assert len({r.comparison_key for r in results}) == 3


def test_quota_counts_reserved_or_actual_per_batch() -> None:
    def entry(run_id: str, reserved: int = 0, spawned: int = 0, day: str = "2026-10-13") -> LedgerEntry:
        return LedgerEntry(run_id=run_id, comparison_key="c", variant_key="v", cost_state="reserved",
                           reserved_runs=reserved, actual_spawns=spawned, started_at=f"{day}T00:00:00+00:00")

    entries = [entry("completed", reserved=3), *[entry("completed", spawned=1) for _ in range(3)],
               entry("pending", reserved=2), entry("aborted", reserved=4), entry("aborted", spawned=1),
               entry("unreserved", spawned=2), entry("yesterday", reserved=100, day="2026-10-12")]
    assert today_spawn_count(entries, now=datetime(2026, 10, 13, tzinfo=UTC)) == 11
