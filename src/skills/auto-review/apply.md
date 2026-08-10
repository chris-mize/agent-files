# Apply, Classify, Pass Modes, and Escalation

Read this after validating reviewer findings and [anti-patterns.md](anti-patterns.md).

## Validate

Before classifying:

1. Trace each reviewer finding to the artifact.
2. Walk every Stated requirements & details and Constraints & preferences bullet in the intent lock.
3. Mark each detail met, violated, or unclear.
4. Promote any violated or missing stated detail to a finding if the reviewer missed it.

## Classify

| Class | Definition | Action |
|---|---|---|
| Auto-fix (plan mode) | Validated plan error whose replacement still matches locked intent and adds no new product choice | Rewrite the plan |
| Auto-fix (work mode) | Validated localized defect with clear intended behavior and no design tradeoff | Apply and verify |
| Blocking escalation | Material ambiguity, conflicting requirements, high-risk choice, approach tradeoff, or insufficient evidence | Ask one decision and stop |
| Non-blocking | Optional, stylistic, or safely deferrable | Report without looping |
| Discard | Speculative, out-of-intent, or not evidenced | Drop with a reason |

In work mode, a simpler alternative that changes architecture or product behavior is a blocking escalation. Restoring a stated user detail is not a new product choice unless carrying it out requires a decision the user never made.

## Apply and verify

In plan mode, rewrite the positive plan and omit superseded steps. In work mode, edit only inside the established boundary, preserve unrelated changes, and do not commit or push unless separately requested.

Run the cheapest relevant verification after every apply. On failure, do not claim a pass or start another review cycle while the check is red.

## Pass modes

- **Until complete:** repeat review, validate, apply or escalate, and verify until no auto-fix or blocking finding remains. Stop on no progress.
- **Single pass:** use exactly one cycle only when the user explicitly requests `single pass`, `one pass`, or `no loop`.

After a user answers an escalation, re-establish the intent and artifact state before resuming.
