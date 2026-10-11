# Routing and role profiles

Model IDs, effort, speed, context limits, and billing are runtime inputs. Do not copy a model name into a receipt unless the host observed it.

## Profile registry

| Profile | Generator | Critic | Purpose |
|---|---|---|---|
| `grok-oneshot` | Grok 4.5 | none | Bare host one-shot |
| `grok-loop` | Grok 4.5 | fresh Grok context | Loop comparison |
| `luna-oneshot` | Luna Max | none | Bare host one-shot |
| `luna-loop` | Luna Max | fresh Luna context | Same-model loop comparison |
| `cheap-generate-strong-critic-terra` | Luna Max | Terra | Selected mixed arm if eligible |
| `cheap-generate-strong-critic-sol` | Luna Max | Sol | Fallback mixed arm if Terra is ineligible |
| `sol-oneshot` | Sol Medium | none | Primary external baseline |
| `sol-standard` | Sol Medium | host-native workflow | Secondary baseline |

Diagnostics are separate atomic profiles:

- `grok-scaffolded-oneshot`: copy `grok-loop`'s generator/controller/planner configuration and remove only critic/revision calls.
- `luna-scaffolded-oneshot`: copy `luna-loop`'s configuration and remove only critic/revision calls.
- `luna-terra-scaffolded-oneshot`: copy the Terra mixed arm and remove only Terra critic/revision calls.
- `luna-sol-scaffolded-oneshot`: copy the Sol mixed arm and remove only Sol critic/revision calls.

Only the selected mixed arm and its matching diagnostic are eligible for the primary study. Do not silently run both critic variants or treat a missing variant as a substitution.

## Selection and capability gate

Freeze this checklist before inspecting the live catalog:

1. Exact model is available and the host can produce an observed-model receipt.
2. Fresh-context role dispatch works with the required read-only permission; generator write scope is recorded as prompt-only unless the host explicitly attests a stronger boundary.
3. Required context limit, tools, and artifact handoff are available.
4. The role can return the structured handoff/verdict fields.
5. No silent fallback occurs when the requested model is unavailable.

Select Terra when every check passes. Otherwise select Sol when every check passes. If neither passes, stop before the pilot. Cost is measured after selection, not used to choose a critic or to conceal a fallback.

Run `scripts/capability_probe.py --host <host> --profile <profile> --input <host-snapshot.json>` before freezing an arm. The snapshot must contain exact `catalog_models`, `controller_models`, and `profile_models` IDs. One-shot profiles have controller-only `profile_models`; loop/scaffold profiles add their roles. The probe emits `required_roles` and actual-model receipts; it exits nonzero on missing identity, requested/observed mismatch, unpinned controller, unavailable role, wrong permission, missing structured handoff/tool access, missing usage attribution, or fallback.

When a run actually triggers fresh planner dispatch, set `planner_required: true` in the snapshot and include the planner's exact model and read-only receipt. Controller-owned planning leaves it false.

## Controller policy

The controller is the main agent and owns routing. Keep its model, effort, speed, and tool policy constant across quantitative arms. If the host cannot pin or expose the controller, mark the run exploratory and exclude it from named conclusions.

Use `inherit` or an explicitly observed host model only when the host supports it. A role file may provide a convenient default, but the controller must record requested and observed values for every call. Model, effort, speed, controller, generator, critic, and planner configuration are one atomic arm.

## Planner trigger

Use conditional planning when:

- the request is materially ambiguous or high risk;
- the task has genuinely divergent approaches;
- the critic returns `REPLAN`;
- repeated revisions share a fundamental root cause.

The planner is read-only and creates a `TaskContract`; it does not edit the artifact or spawn another role.

## Loop and fallback rules

- Explicit invocation always runs intake and the quality gate.
- Default budget is one critic pass and at most two revision rounds.
- Stop on clean `PASS`, repeated root cause, no measurable progress, budget exhaustion, missing receipt, or unavailable role dispatch.
- Route an implementation defect to the generator, a contract defect to a fresh planner, and unresolved/high-impact issues to the user.
- Never silently substitute a strategic model. Record degraded state or stop.
