---
name: actor-critic-mode
description: Run an explicitly invoked, bounded generator–critic operating mode for high-stakes coding or research tasks. Preserve the original requirements, use conditional planning for ambiguous or risky work, verify the artifact in a fresh critic context, and report model, gate, cost, and degraded-run receipts. This is inference-time orchestration, not RL training. Use when the user explicitly invokes the host's actor-critic-mode command or requests an actor-critic quality pass.
disable-model-invocation: true
license: MIT
compatibility: Claude Code, Codex, or Cursor with structured role dispatch and receipt support
---

# Actor-Critic Mode

Use this skill only after explicit invocation. It adds deliberate inference-time verification; it does not train a model or reproduce latent-state actor–critic research.

## Controller workflow

The parent agent is the controller. Roles do not spawn roles, commit, push, reset, clean, or perform destructive actions.

1. **Lock intent.** Build an immutable `IntentPacket` from the original request. Preserve every user-stated requirement and constraint with stable IDs. Record ambiguity, risk, non-goals only when grounded in the request, and the call/iteration budget.
2. **Gate the task.** Skip nothing after explicit invocation, including trivial work. For clear low/medium-risk work, use the generator fast path. For ambiguous or high-risk work, or after a `REPLAN` verdict, obtain a fresh read-only `TaskContract` from the planner logic.
3. **Dispatch the generator.** Give it the unchanged `IntentPacket`, the derived contract, scoped repository context, and expected validation commands. It may edit only the requested scope and must return changed paths, decisions, and command results.
4. **Verify in the controller.** Re-run relevant tests, typechecks, lint, builds, and runtime checks. Treat generator-reported results as unverified until the controller captures exit status and artifacts.
5. **Dispatch the critic.** Use a fresh read-only context with the intent, contract, actual diff/artifact, verified gate output, and a bounded trajectory digest. The critic checks every requirement, edge cases, regressions, scope drift, and test validity. It returns `PASS`, `REVISE`, `REPLAN`, or `ESCALATE` with evidence and a smallest fix.
6. **Bound the loop.** Default to one review and at most two revision rounds. Stop on `PASS`, repeated root cause, no measurable progress, budget exhaustion, or unresolved high-impact uncertainty. Route implementation defects to the generator and fundamental plan defects to the planner.
7. **Receipt the run.** Record host, invocation mode, requested and observed role models, reasoning effort, speed tier, fallback state, gate results, iteration count, calls, and cost units. If a host cannot expose a required identity or execution result, mark the run degraded or abort; never silently substitute a strategic model.

Before selecting a named profile, run `scripts/capability_probe.py` against the host-supplied catalog/role snapshot. It must confirm controller pinning and identity exposure, exact role models, fresh-context dispatch, permissions, structured handoffs, tools, usage attribution, and no fallback. A missing or failed probe is not eligible for a pilot or named model conclusion.

## Required handoffs

Read [references/protocol.md](references/protocol.md) before constructing packets or verdicts. Read [references/routing.md](references/routing.md) before choosing a profile. Read [references/evaluation.md](references/evaluation.md) only for benchmark, receipt, or cost work. Read [references/research-ledger.md](references/research-ledger.md) when making research-backed design claims.

Identify the active host and read exactly one matching adapter:

- [Claude Code](references/platforms/claude-code.md)
- [Codex](references/platforms/codex.md)
- [Cursor](references/platforms/cursor.md)

Every role handoff must carry the immutable packet hash, contract version, artifact identifier, allowed scope, verified gate summary, and stop condition. Keep trajectory digests compact and factual: decisions, identifiers, commands, outputs, and unresolved questions—not hidden answers or reviewer conclusions.

## Safety and degraded runs

- Use read-only permissions for planner and critic roles. Generator write scope is enforced through controller instructions and post-run diff checks unless the host explicitly attests a stronger boundary; receipt `prompt_only` and downgrade named-run safety status.
- Keep hidden tests, expected answers, scoring keys, holdout tasks, and private receipts outside agent-readable workspaces. Probe host deny rules or a sandbox when available; with prompt-only generator scope, record degraded isolation and do not claim that denial was host-enforced.
- Treat human content changes during a measured run as invalid; charge the full run and do not rerun based on its outcome.
- Never claim completion when role dispatch, model identity, gate evidence, or cost comparability is unavailable. Report a degraded state or `not_confirmed` for an unavailable frozen arm, and stop at the configured boundary.
- Reuse the existing auto-review conventions for intent locking and finding validation; this skill owns routing, handoffs, controller-run gates, and bounded termination.

## Evaluation harness

Use `scripts/evaluate_runs.py` for sanitized JSONL run records. The script is intentionally independent of hidden tests: a trusted harness supplies only pass/fail and scored artifact results. See [references/evaluation.md](references/evaluation.md) for the record contract and commands.
