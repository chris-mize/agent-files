from __future__ import annotations

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/actor-critic-mode"


def load_script(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ActorCriticTests(unittest.TestCase):
    def test_canonical_tree_contains_protocol_and_host_adapters(self) -> None:
        expected = (
            "SKILL.md",
            "agents/openai.yaml",
            "references/protocol.md",
            "references/routing.md",
            "references/evaluation.md",
            "references/research-ledger.md",
            "references/platforms/claude-code.md",
            "references/platforms/codex.md",
            "references/platforms/cursor.md",
            "scripts/capability_probe.py",
            "scripts/evaluate_runs.py",
            "scripts/smoke_protocol.py",
        )
        for relative_path in expected:
            self.assertTrue(
                (SKILL / relative_path).is_file(),
                f"missing actor-critic-mode file: {relative_path}",
            )

    def test_capability_probe_self_test_passes(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SKILL / "scripts/capability_probe.py"), "--self-test"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        self.assertIn("self-test: ok", result.stdout)

    def test_evaluation_harness_self_test_passes(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SKILL / "scripts/evaluate_runs.py"), "--self-test"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        self.assertIn("self-test: ok", result.stdout)

    def test_evaluator_requires_explicit_invocation_and_ok_calls(self) -> None:
        evaluator = load_script(
            "actor_critic_evaluator",
            SKILL / "scripts/evaluate_runs.py",
        )
        record = evaluator._synthetic_record("candidate", "dev-01", 1, True, 0, 1.0)
        record["model_receipt"]["observed"] = "forged-model"
        self.assertTrue(any("does not match controller" in error for error in evaluator.validate_record(record, 1)))
        record["model_receipt"]["observed"] = "sol"
        record["model_receipt"]["invocation_mode"] = "implicit"
        errors = evaluator.validate_record(record, 1)
        self.assertTrue(any("must be explicit" in error for error in errors))

        record["model_receipt"]["invocation_mode"] = "explicit"
        record["call_ledger"][0]["status"] = "failed"
        self.assertFalse(evaluator._valid_success(record))
        self.assertEqual(evaluator._quality_key(record), (0, 0, 0))

    def test_evaluator_fails_closed_on_malformed_manifest(self) -> None:
        evaluator = load_script(
            "actor_critic_evaluator_malformed",
            SKILL / "scripts/evaluate_runs.py",
        )
        record = evaluator._synthetic_record("candidate", "dev-01", 1, True, 0, 1.0)
        record["capability_receipt"]["required_roles"] = [{"not": "a role name"}]
        self.assertTrue(evaluator.validate_record(record, 1))

        errors = evaluator.validate_manifest(
            {
                "phase": [],
                "task_ids": [{"not": "text"}],
                "profiles": [{"not": "text"}],
                "partition": {},
            },
            [],
            "candidate",
            "baseline",
            "scaffold",
            3,
        )
        self.assertTrue(errors)

        duplicate_profiles = {
            "phase": "development",
            "task_ids": ["dev-01", "dev-02", "dev-03", "dev-04"],
            "profiles": ["candidate", "baseline", "scaffold", "candidate"],
            "partition": {
                "development_task_ids": ["dev-01", "dev-02", "dev-03", "dev-04"],
                "holdout_task_ids": ["holdout-01", "holdout-02", "holdout-03", "holdout-04"],
            },
        }
        self.assertTrue(
            evaluator.validate_manifest(
                duplicate_profiles,
                [],
                "candidate",
                "baseline",
                "scaffold",
                3,
            )
        )

        malformed_capability = dict(evaluator._synthetic_record("candidate", "dev-01", 1, True, 0, 1.0))
        malformed_capability["capability_receipt"] = []
        self.assertTrue(
            evaluator.validate_manifest(
                duplicate_profiles,
                [malformed_capability],
                "candidate",
                "baseline",
                "scaffold",
                3,
            )
        )

    def test_capability_probe_accepts_claude_and_rejects_bad_scope(self) -> None:
        probe = load_script(
            "actor_critic_capability_probe",
            SKILL / "scripts/capability_probe.py",
        )
        snapshot = {
            "host": "claude",
            "catalog_snapshot": "test",
            "catalog_models": ["sol"],
            "controller_models": {"sol-oneshot": "sol"},
            "profile_models": {"sol-oneshot": {}},
            "usage_attribution": True,
            "fallback": False,
            "controller": {
                "requested_model": "sol",
                "observed_model": "sol",
                "pinned": True,
                "exposes_identity": True,
                "fallback": False,
                "effort": "high",
                "speed": "default",
            },
            "roles": {},
        }
        self.assertTrue(probe.probe(snapshot, "claude", "sol-oneshot")["eligible"])

        snapshot["profile_models"]["sol-oneshot"] = {"generator": "sol"}
        snapshot["roles"]["generator"] = {
            "requested_model": "sol",
            "observed_model": "sol",
            "fresh_context": True,
            "structured_handoff": True,
            "tools": True,
            "fallback": False,
            "readonly": False,
            "exposes_identity": True,
            "write_scope": "*",
            "scope_enforcement": "prompt_only",
            "effort": "high",
            "speed": "default",
        }
        self.assertFalse(probe.probe(snapshot, "claude", "sol-oneshot")["eligible"])

        snapshot["roles"]["generator"]["scope_enforcement"] = []
        self.assertFalse(probe.probe(snapshot, "claude", "sol-oneshot")["eligible"])

        snapshot["catalog_snapshot"] = ["bad-type"]
        snapshot["planner_required"] = "true"
        self.assertFalse(probe.probe(snapshot, "claude", "sol-oneshot")["eligible"])


if __name__ == "__main__":
    unittest.main()
