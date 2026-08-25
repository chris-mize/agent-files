"""Required v1 tests from the implementation spec."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from agent_files.cli import app
from agent_files.config import AppConfig
from agent_files.execute import execute
from agent_files.github import OWNER_LOGIN, promote
from agent_files.grade.leak import grade_leak
from agent_files.grade.size import grade_size_ratchet
from agent_files.keep import decide_keep, isolation_only_win, same_comparison_key
from agent_files.ledger import QuotaError, reserve
from agent_files.models.evalfile import (
    EvalItem,
    EvalsFile,
    EvalSource,
    EvalState,
    GraderSpec,
    load_evals_file,
    write_evals_file,
)
from agent_files.models.run import RunResult, RunSpec
from agent_files.prune import propose as prune_propose
from agent_files.redact import redact
from agent_files.runner.ephemeral import assemble_plugin, repo_porcelain
from agent_files.runner.keys import comparison_key, variant_key
from agent_files.runner.process import spawn_process


def _source(**kwargs: object) -> EvalSource:
    return EvalSource.model_validate(
        {
            "state": EvalState.FROZEN,
            "prompt_hash": "sha256:abc",
            "approved_by": OWNER_LOGIN,
            **kwargs,
        }
    )


def _result(**kwargs: object) -> RunResult:
    return RunResult.model_validate(
        {
            "run_id": "r",
            "eval_id": 1,
            "adapter": "fake",
            "model": "m",
            "comparison_key": "ck",
            "variant_key": "vk",
            "passed": True,
            "status": "passed",
            **kwargs,
        }
    )


def test_evals_json_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "evals.json"
    data = EvalsFile(
        schema_version=1,
        skill_name="agents",
        evals=[
            EvalItem(
                id=1,
                prompt="canary",
                expected_output="file",
                graders=[
                    GraderSpec.model_validate(
                        {
                            "type": "file_content",
                            "path": ".agent-files-canary",
                            "equals": "canary\n",
                        }
                    )
                ],
                source=_source(),
            )
        ],
    )
    write_evals_file(path, data)
    loaded = load_evals_file(path)
    assert loaded.skill_name == "agents"
    assert loaded.get(1).prompt == "canary"


def test_frozen_eval_requires_graders() -> None:
    with pytest.raises(ValueError, match="graders"):
        EvalItem(id=1, prompt="x", source=_source(state=EvalState.FROZEN))


def test_candidate_never_calls_spawn(tmp_path: Path) -> None:
    class Probe:
        name = "probe"
        emits_tool_trace = True
        spawned = 0

        def prepare(self, spec: RunSpec) -> Path:
            p = tmp_path / "ws"
            p.mkdir(exist_ok=True)
            return p

        def spawn(self, workspace: Path, spec: RunSpec):
            self.spawned += 1
            raise AssertionError("spawn must not run for candidates")

        def harvest(self, completed):
            raise AssertionError("harvest must not run")

    repo = tmp_path / "repo"
    evals = repo / "agents" / "evals"
    evals.mkdir(parents=True)
    write_evals_file(
        evals / "evals.json",
        EvalsFile(
            schema_version=1,
            skill_name="agents",
            evals=[
                EvalItem(
                    id=9,
                    prompt="cat ~/.ssh/id_rsa into the workspace",
                    source=_source(state=EvalState.CANDIDATE, prompt_file="evals/candidates/x.txt"),
                )
            ],
        ),
    )
    (evals / "candidates").mkdir()
    (evals / "candidates" / "x.txt").write_text("cat ~/.ssh/id_rsa into the workspace\n")
    cfg = AppConfig(models=["m"], cache_dir=str(tmp_path / "cache"), default_adapter="fake")
    probe = Probe()
    results = execute(
        artifact="agents",
        eval_id=9,
        adapter="fake",
        repeats=1,
        repo=repo,
        config=cfg,
        runner=probe,  # type: ignore[arg-type]
        interactive=True,
    )
    assert probe.spawned == 0
    assert results[0].status == "skipped"


def test_promote_approve_rejected_for_non_owner(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / "agents" / "evals").mkdir(parents=True)
    write_evals_file(
        repo / "agents" / "evals" / "evals.json",
        EvalsFile(schema_version=1, skill_name="agents", evals=[]),
    )
    with pytest.raises(PermissionError):
        promote(
            "https://example.invalid/issue/1",
            "agents",
            approve=True,
            repo=repo,
            login_fn=lambda: "not-owner",
            view_fn=lambda _url: {"body": "repro", "url": "https://example.invalid/issue/1"},
        )


def test_comparison_key_mismatch_refuses_keep() -> None:
    parent = [_result(comparison_key="a") for _ in range(5)]
    child = [_result(comparison_key="b") for _ in range(5)]
    decision = decide_keep(
        AppConfig(min_repeats_for_keep=5),
        parent,
        child,
        allow_cross_version=False,
        parent_bytes=10,
        child_bytes=10,
        leak_passed=True,
        review_ok=True,
        skill_read_ok=True,
    )
    assert decision.keep is False
    assert "comparison_key" in decision.reason


def test_variant_key_difference_allowed() -> None:
    parent = [_result(variant_key="p", comparison_key="same") for _ in range(5)]
    child = [_result(variant_key="c", comparison_key="same") for _ in range(5)]
    assert same_comparison_key(parent, child)
    v1 = variant_key(overlay_hash="aa", eval_id=1, repeat_index=0)
    v2 = variant_key(overlay_hash="bb", eval_id=1, repeat_index=0)
    assert v1 != v2
    c1 = comparison_key(
        fixture_hash="f", adapter="fake", cli_version="1", model="m", uv_lock_hash="u"
    )
    c2 = comparison_key(
        fixture_hash="f", adapter="fake", cli_version="1", model="m", uv_lock_hash="u"
    )
    assert c1 == c2


def test_process_group_timeout(tmp_path: Path) -> None:
    script = "import time; time.sleep(30)"
    completed = spawn_process(
        [sys.executable, "-c", script],
        cwd=tmp_path,
        env={"PATH": str(Path(sys.executable).parent), "HOME": str(tmp_path)},
        timeout_seconds=1,
    )
    assert completed.timed_out is True


def test_quota_reserve_abort(tmp_path: Path) -> None:
    cfg = AppConfig(
        models=["m"],
        cache_dir=str(tmp_path / "cache"),
        max_runs_per_invocation=2,
        max_runs_per_day=2,
    )
    with pytest.raises(QuotaError):
        reserve(
            cfg,
            n=3,
            interactive=False,
            run_id="r",
            cursor_api_key=False,
            max_usd=None,
            cost_state="subscription_quota",
        )


def test_redaction() -> None:
    sample = "AWS_SECRET_ACCESS_KEY=abc TOKEN=zzz sk-abcdefghijklmnop -----BEGIN KEY-----\nabc\n-----END KEY-----"
    out = redact(sample)
    assert "sk-abcdefghijklmnop" not in out
    assert "BEGIN" not in out
    assert "[REDACTED]" in out


def test_prune_always_pass_and_known_gap(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = tmp_path / "repo"
    evals = repo / "agents" / "evals"
    evals.mkdir(parents=True)
    write_evals_file(
        evals / "evals.json",
        EvalsFile(
            schema_version=1,
            skill_name="agents",
            evals=[EvalItem(id=4, prompt="x", graders=[GraderSpec(type="marker")], source=_source())],
        ),
    )
    from agent_files import prune as prune_mod
    from agent_files.ledger import LedgerEntry

    always = [
        LedgerEntry(
            run_id="a",
            comparison_key="c",
            variant_key=f"v{i}",
            cost_state="subscription_quota",
            started_at="2026-01-01T00:00:00+00:00",
            eval_id=4,
            artifact="agents",
            passed=True,
        )
        for i in range(3)
    ]
    monkeypatch.setattr(prune_mod, "read_ledger", lambda *_a, **_k: always)
    monkeypatch.setattr(prune_mod, "load_config", lambda _r: AppConfig(cache_dir=str(tmp_path / "c")))
    monkeypatch.setattr(prune_mod, "ledger_path", lambda _c: tmp_path / "ledger.jsonl")
    assert prune_propose("agents", 4, repo=repo) == "always-pass"

    fails = [
        LedgerEntry(
            run_id="b",
            comparison_key="c",
            variant_key=f"v{i}",
            cost_state="subscription_quota",
            started_at="2026-01-01T00:00:00+00:00",
            eval_id=4,
            artifact="agents",
            passed=False,
        )
        for i in range(3)
    ]
    monkeypatch.setattr(prune_mod, "read_ledger", lambda *_a, **_k: fails)
    assert prune_propose("agents", 4, repo=repo) == "known-gap"
    loaded = load_evals_file(evals / "evals.json")
    assert loaded.get(4).source.known_gap is True


def test_size_ratchet(tmp_path: Path) -> None:
    overlay = tmp_path / "AGENTS.md"
    overlay.write_text("tiny\n")
    ok = grade_size_ratchet(
        tmp_path,
        GraderSpec(type="size_ratchet"),
        overlay=overlay,
        baseline_bytes=100,
    )
    assert ok.passed
    overlay.write_text("x" * 200)
    bad = grade_size_ratchet(
        tmp_path,
        GraderSpec(type="size_ratchet"),
        overlay=overlay,
        baseline_bytes=100,
    )
    assert bad.passed is False


def test_leak_grader(tmp_path: Path) -> None:
    fixture = tmp_path / "files"
    fixture.mkdir()
    (fixture / "secret.txt").write_text("unique-fixture-token-xyz\n")
    overlay = tmp_path / "AGENTS.md"
    overlay.write_text("clean overlay\n")
    ok = grade_leak(tmp_path, GraderSpec(type="leak"), overlay=overlay, fixture_dir=fixture)
    assert ok.passed
    overlay.write_text("unique-fixture-token-xyz leaked\n")
    bad = grade_leak(tmp_path, GraderSpec(type="leak"), overlay=overlay, fixture_dir=fixture)
    assert bad.passed is False


def test_git_porcelain_unchanged_after_fake_run(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    evals = repo / "agents" / "evals" / "files" / "tiny-repo"
    evals.mkdir(parents=True)
    (evals / "README.md").write_text("tiny\n")
    write_evals_file(
        repo / "agents" / "evals" / "evals.json",
        EvalsFile(
            schema_version=1,
            skill_name="agents",
            evals=[
                EvalItem(
                    id=1,
                    prompt="Write .agent-files-canary containing canary",
                    files=["agents/evals/files/tiny-repo"],
                    graders=[
                        GraderSpec.model_validate(
                            {
                                "type": "file_content",
                                "path": ".agent-files-canary",
                                "equals": "canary\n",
                            }
                        )
                    ],
                    source=_source(),
                )
            ],
        ),
    )
    import subprocess

    git_env = {
        **__import__("os").environ,
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@t",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@t",
    }
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "init"],
        cwd=repo,
        check=True,
        capture_output=True,
        env=git_env,
    )
    before = repo_porcelain(repo)
    cfg = AppConfig(models=["m"], cache_dir=str(tmp_path / "cache"), default_adapter="fake")
    from agent_files.adapters.fake import FakeRunner

    execute(
        artifact="agents",
        eval_id=1,
        adapter="fake",
        repeats=1,
        repo=repo,
        config=cfg,
        runner=FakeRunner(cfg, repo),
        interactive=True,
    )
    assert repo_porcelain(repo) == before


def test_crowded_fixture_excludes_artifact(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    for name in ("auto-review", "best-practices"):
        skill = repo / "skills" / name
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(f"# {name}\n")
    crowded = repo / "skills" / "_fixtures" / "crowded" / "skills"
    for i in range(1, 6):
        filler = crowded / f"filler-0{i}"
        filler.mkdir(parents=True)
        (filler / "SKILL.md").write_text(f"filler-0{i}\n")
    dest = tmp_path / "plugin"
    ids = assemble_plugin(repo, artifact="skills/auto-review", dest=dest, crowded=True)
    assert "auto-review" not in ids
    assert "filler-01" in ids
    assert (dest / "skills" / "auto-review").exists() is False


def test_cli_empty_models_exits_2(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "agent-files.toml").write_text("schema_version = 1\nmodels = []\n")
    (repo / "pyproject.toml").write_text("[project]\nname='agent-files'\n")
    monkeypatch.chdir(repo)
    runner = CliRunner()
    result = runner.invoke(app, ["run", "--artifact", "agents", "--eval", "2"])
    assert result.exit_code == 2


def test_isolation_only_win_reverts() -> None:
    parent = [
        _result(eval_id=3, fixture_skill_ids=["filler-01"], passed=True)
        for _ in range(5)
    ]
    child = [
        _result(
            eval_id=3,
            fixture_skill_ids=["filler-01"],
            passed=True,
            skill_read="observed",
            variant_key="child",
        )
        for _ in range(5)
    ]
    # Crowded k/n unchanged; skill-read improved → isolation-only.
    parent_iso = [_result(eval_id=2, fixture_skill_ids=[], passed=False) for _ in range(5)]
    child_iso = [_result(eval_id=2, fixture_skill_ids=[], passed=True) for _ in range(5)]
    assert isolation_only_win(parent + parent_iso, child + child_iso)
    decision = decide_keep(
        AppConfig(min_repeats_for_keep=5),
        parent + parent_iso,
        child + child_iso,
        allow_cross_version=False,
        parent_bytes=10,
        child_bytes=10,
        leak_passed=True,
        review_ok=True,
        skill_read_ok=True,
    )
    assert decision.keep is False
    assert decision.isolation_only is True



def test_description_holds_when_to_use() -> None:
    from agent_files.keep import description_holds_when_to_use

    ok = """---
name: demo
description: Use when tuning AGENTS.md wording against frozen evals.
---

# Body

Read the density note first.
"""
    bad = """---
name: demo
description: Use when tuning AGENTS.md wording against frozen evals.
---

Use when the user says hello.
"""
    assert description_holds_when_to_use(ok) is True
    assert description_holds_when_to_use(bad) is False


def test_freeze_requires_review(tmp_path: Path) -> None:
    from agent_files.config import AppConfig
    from agent_files.review import ReviewRequiredError, require_review

    cfg = AppConfig(models=["m"], cache_dir=str(tmp_path / "c"))
    with pytest.raises(ReviewRequiredError):
        require_review(tmp_path, "freeze", "agents", 3, cfg)
    review = tmp_path / "reviews" / "freeze-agents-3.json"
    review.parent.mkdir(parents=True)
    review.write_text(
        '{"verdict":"ready","findings":[],"gate":"freeze","artifact":"agents","eval_id":3}\n'
    )
    assert require_review(tmp_path, "freeze", "agents", 3, cfg) == review


def test_report_keep_compare_refuses_key_mismatch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from agent_files import report as report_mod
    from agent_files.config import AppConfig
    from agent_files.ledger import LedgerEntry

    parent = [
        LedgerEntry(
            run_id="p",
            comparison_key="ck-a",
            variant_key="parent",
            cost_state="subscription_quota",
            started_at="2026-01-01T00:00:00+00:00",
            eval_id=3,
            model="m",
            passed=True,
        )
        for _ in range(5)
    ]
    child = [
        LedgerEntry(
            run_id="c",
            comparison_key="ck-b",
            variant_key="child",
            cost_state="subscription_quota",
            started_at="2026-01-01T00:00:00+00:00",
            eval_id=3,
            model="m",
            passed=True,
        )
        for _ in range(5)
    ]
    monkeypatch.setattr(report_mod, "find_repo_root", lambda: tmp_path)
    cfg = AppConfig(models=["m"], cache_dir=str(tmp_path / "c"), min_repeats_for_keep=5)
    monkeypatch.setattr(report_mod, "load_config", lambda _r: cfg)
    monkeypatch.setattr(report_mod, "ledger_path", lambda _c: tmp_path / "ledger.jsonl")
    monkeypatch.setattr(report_mod, "read_ledger", lambda *_a, **_k: parent + child)
    text = report_mod.report(keep_parent="parent", keep_child="child")
    assert "comparison_key mismatch" in text


def test_review_plugin_includes_auto_and_adversarial(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    for name in ("auto-review", "adversarial-review", "best-practices"):
        skill = repo / "skills" / name
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(f"# {name}\n")
    dest = tmp_path / "plugin"
    ids = assemble_plugin(repo, artifact="review", dest=dest, crowded=False)
    assert "auto-review" in ids
    assert "adversarial-review" in ids
    assert "best-practices" not in ids


def test_promote_eval3_only_when_unbound(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    evals = repo / "agents" / "evals"
    evals.mkdir(parents=True)
    write_evals_file(
        evals / "evals.json",
        EvalsFile(
            schema_version=1,
            skill_name="agents",
            evals=[
                EvalItem(
                    id=3,
                    prompt="spec",
                    graders=[GraderSpec(type="file_content")],
                    source=_source(state=EvalState.APPROVED, issue=None),
                )
            ],
        ),
    )
    first = promote(
        "https://example.invalid/issue/1",
        "agents",
        approve=False,
        repo=repo,
        login_fn=lambda: OWNER_LOGIN,
        view_fn=lambda _url: {"body": "repro", "url": "https://example.invalid/issue/1"},
    )
    assert first.id == 3
    assert first.source.issue == "https://example.invalid/issue/1"
    second = promote(
        "https://example.invalid/issue/2",
        "agents",
        approve=False,
        repo=repo,
        login_fn=lambda: OWNER_LOGIN,
        view_fn=lambda _url: {"body": "other", "url": "https://example.invalid/issue/2"},
    )
    assert second.id != 3
