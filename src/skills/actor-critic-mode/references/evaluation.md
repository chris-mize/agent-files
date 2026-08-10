# Evaluation protocol

This reference defines the reproducible A/B data contract. It does not contain hidden tests, expected answers, scoring keys, holdout tasks, or private receipts.

## Study phases

1. **Tuning:** use disposable fixtures only. Tune prompts, routing, effort, speed, and gate wording here.
2. **Development decision:** freeze the protocol, then run the selected mixed arm, `sol-oneshot`, and its matching scaffold on four disjoint development tasks, three repetitions each. This only decides whether implementation may proceed.
3. **Implementation and forward test:** create persistent packages, smoke-test both hosts, and permit reliability fixes that do not change the frozen behavioral configuration. A behavioral change requires rerunning affected development repetitions or labeling the holdout as a new configuration.
4. **Holdout:** with one catalog snapshot and final configuration, run every eligible measurement arm on four disjoint holdout tasks, three repetitions each, exactly once. Never tune from holdout results.

The same catalog snapshot governs development and holdout. If a frozen model is unavailable at holdout, record that arm as unrunnable and report the affected conclusion as `not_confirmed`; do not substitute or resnapshot.

An unrunnable arm is represented in the JSONL with the normal run schema plus `"run_status": "unrunnable"`, a non-empty `reason`, a requested model with `observed: null`, an ineligible capability receipt, and the complete hashed environment receipt. The evaluator returns `not_confirmed` instead of fabricating a quality or cost result.

## Frozen study manifest

Named scoring requires a separate manifest; the evaluator rejects an absent or incomplete one. It must declare exactly four task IDs, the `development` or `holdout` phase, three repetitions, every requested profile, one catalog snapshot, an independent blinded scorer receipt, randomized sanitization, and role-specific isolation posture receipts:

```json
{
  "schema": "study-manifest/v1",
  "phase": "development",
  "task_ids": ["dev-01", "dev-02", "dev-03", "dev-04"],
  "partition": {
    "development_task_ids": ["dev-01", "dev-02", "dev-03", "dev-04"],
    "holdout_task_ids": ["holdout-01", "holdout-02", "holdout-03", "holdout-04"]
  },
  "profiles": ["candidate", "sol-oneshot", "matching-scaffold"],
  "profile_models": {
    "candidate": {"controller": "sol-medium"},
    "sol-oneshot": {"controller": "sol-medium"},
    "matching-scaffold": {"controller": "sol-medium"}
  },
  "repetitions": 3,
  "budget": {"max_revisions": 2, "max_role_calls": 8},
  "catalog_snapshot": "host-catalog-date",
  "configuration_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "write_scope_enforcement": "prompt_only",
  "scope_postures": {
    "candidate": "prompt_only",
    "sol-oneshot": "not_applicable",
    "matching-scaffold": "prompt_only"
  },
  "scorer_receipt": {
    "fresh": true,
    "blinded": true,
    "participated_in_arms": false,
    "rubric_hash": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
  },
  "sanitization": {
    "randomized": true,
    "strips_profile": true,
    "strips_receipts": true
  },
  "isolation": {
    "hidden_tests_outside_workspace": true,
    "deny_probe_passed": false,
    "trusted_harness_only": true,
    "deny_probes": {
      "controller": {"passed": true, "host_enforced": true, "tool_access_checked": true, "receipt_hash": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"},
      "generator": {"passed": false, "host_enforced": false, "tool_access_checked": true, "receipt_hash": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd"},
      "critic": {"passed": true, "host_enforced": true, "tool_access_checked": true, "receipt_hash": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"},
      "planner": {"passed": true, "host_enforced": true, "tool_access_checked": true, "receipt_hash": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"},
      "scorer": {"passed": true, "host_enforced": true, "tool_access_checked": true, "receipt_hash": "1111111111111111111111111111111111111111111111111111111111111111"}
    }
  }
}
```

## Isolation

Store hidden tests, expected answers, scoring keys, holdout tasks, and private receipts outside agent-readable workspaces. Apply host sandbox or permission-deny rules where available. After pilot authorization, create a disposable sentinel/layout and probe generator, critic, planner, controller, and scorer read/tool access; prompt-only generator scope must be recorded as unverified. A trusted test harness returns only sanitized pass/fail and scored artifact results.

## Sanitized run record

`scripts/evaluate_runs.py` consumes JSONL records shaped like this:

```json
{
  "run_id": "run-001",
  "task_id": "dev-01",
  "repetition": 1,
  "profile": "sol-oneshot",
  "model_receipt": {
    "requested": "sol-medium",
    "observed": "sol-medium",
    "effort": "high",
    "speed": "default",
    "host": "host",
    "invocation_mode": "explicit",
    "configuration_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "fallback": false,
    "roles": {
      "controller": {"requested": "sol-medium", "observed": "sol-medium"}
    }
  },
  "capability_receipt": {
    "eligible": true,
    "profile": "sol-oneshot",
    "catalog_snapshot": "host-catalog-date",
    "write_scope_enforcement": "not_applicable",
    "required_roles": ["controller"],
    "actual_models": {
      "controller": {"requested": "sol-medium", "observed": "sol-medium"}
    }
  },
  "call_ledger": [
    {
      "role": "controller",
      "requested_model": "sol-medium",
      "observed_model": "sol-medium",
      "status": "ok"
    }
  ],
  "environment_receipt": {
    "key": "19ff75270192d75b7468452e8eb64a28c089e9a9a152076bf847267d3bbcb2e0",
    "task_revision": "git:abc123",
    "dependency_lock_hash": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
    "tool_versions": {"python": "3.13", "runner": "1.0"},
    "fixture_hash": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
    "network_policy": "deny"
  },
  "quality": {
    "valid_gates": true,
    "missed_mandatory": 0,
    "defects": 0,
    "regressions": 0,
    "success": true
  },
  "cost": {
    "pool": "comparable-pool",
    "units": 1.25
  },
  "usage": {
    "latency_ms": 18400,
    "input_tokens": 8200,
    "output_tokens": 3100,
    "role_calls": 3
  },
  "secondary": {
    "reviewer_precision": 0.8,
    "proposal_coverage": 0.7,
    "critic_soundness": 0.9,
    "revision_direction": "incorrect_to_correct",
    "iterations": 1
  },
  "human_intervention": false
}
```

When `write_scope_enforcement` is `prompt_only`, the report's `safety_status` is
`degraded_prompt_only`; this is not evidence of a host sandbox boundary. A
host-enforced posture is eligible only when the manifest records a passed
host-enforced deny probe; the evaluator also accepts `not_applicable` for
one-shot arms without a generator.

Required receipts prevent a run from being treated as a named result. Human content changes invalidate the repetition, charge its full cost, and do not trigger an outcome-based rerun.

## Scoring

For each run, higher quality is the lexicographic tuple:

1. valid acceptance gates;
2. fewer missed mandatory requirements;
3. fewer defects/regressions.

Invalid or failed runs are lowest quality. A successful repetition has valid required gates, zero missed mandatory requirements, and no disqualifying defect. Pair the same task and repetition index across profiles. A task-level result is the majority of three repetition results; no majority is a tie.

For each task/profile, cost-per-success is total comparable spend, including failed attempts, divided by successful repetitions. Zero successes are undefined/infinite. Under the conservative policy, any non-finite task value makes that profile/baseline cost comparison `inconclusive`; do not drop the task or treat it as zero. With four finite values, median is the arithmetic mean of the two middle values.

The selected pilot arm needs at least two net task-level quality wins against bare `sol-oneshot` and at least two net wins against its matching scaffold, plus a lower comparable median cost than bare `sol-oneshot`. Any mismatch, missing receipt, non-comparable pool, or missing primary arm stops the relevant conclusion.

Aggregate each profile's latency, input tokens, output tokens, role calls, successful completion, missed requirements, defects/regressions, reviewer precision, proposal coverage, critic soundness, revision direction, iteration count, and human interventions. Keep critic metrics separate from primary task-success scoring.

## Harness command

Evaluate a sanitized JSONL file:

```bash
python3 scripts/evaluate_runs.py \
  --input runs.jsonl \
  --manifest study-manifest.json \
  --output report.json \
  --candidate cheap-generate-strong-critic-terra \
  --baseline sol-oneshot \
  --scaffold luna-terra-scaffolded-oneshot \
  --min-net-wins 2
```

The report includes pairwise task outcomes, net wins/losses/ties, cost medians, receipt failures, mismatch states, and a `qualified`/`inconclusive`/`not_confirmed` result. It never reads hidden material.

## Residual limits

- This package is inference-time orchestration, not actor–critic reinforcement learning, latent-state transfer, or model training.
- Prompt loops cannot repair shared generator blind spots; proposal coverage and critic soundness remain separate measurements.
- A host that cannot pin/expose the controller, actual role model, usage attribution, or permission boundary cannot contribute a named model/cost conclusion.
- The local host configuration may expose only a subset of the requested catalog at a given time. The capability probe must fail closed until the exact profile is observed.
- The included self-tests validate schemas, scoring, receipts, and bounded termination; they are not evidence that any model improves on real coding tasks.
