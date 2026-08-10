---
name: auto-review
description: Explicitly review a named plan or bounded work artifact through an independent adversarial reviewer, validate the findings, and rewrite the plan or apply safe high-confidence fixes. Invoke this skill directly when you want the review loop.
disable-model-invocation: true
license: MIT
compatibility: Claude Code, Codex, or Cursor with an independent subagent facility
---

# Auto-Review

Orchestrate an independent adversarial review, then improve the artifact. Preserve the user's stated objective. Do not invent a different goal.

## Progressive disclosure

Read references only when the step needs them:

| When | Read |
|---|---|
| When locking intent | [intent.md](intent.md) |
| Before classifying, applying, escalating, or rewriting | [anti-patterns.md](anti-patterns.md) |
| Before launching the reviewer | [review-brief.md](review-brief.md) |
| After validating findings | [apply.md](apply.md) |
| When wording is ambiguous | [examples.md](examples.md) |

## Runtime selection

Identify the active host from its system instructions and available tools. Read exactly one matching file from [references/platforms/](references/platforms/):

- [Claude Code](references/platforms/claude-code.md)
- [Codex](references/platforms/codex.md)
- [Cursor](references/platforms/cursor.md)

If the host cannot be identified or cannot provide the required independent reviewer, stop and report the capability gap. Do not substitute a same-context self-review and call it independent.

## Workflow

```text
Auto-review:
- [ ] 0. Resolve the artifact and edit target
- [ ] 1. Read intent.md and lock the full thread-wide intent
- [ ] 2. Read review-brief.md and the active host adapter; launch one independent reviewer
- [ ] 3. Validate each finding and each locked stated detail on the artifact
- [ ] 4. Read anti-patterns.md and apply.md; classify findings
- [ ] 5. Apply a plan rewrite or bounded work fix; run cheap verification
- [ ] 6. Repeat until complete, with no progress, or with a blocking escalation
```

### 0. Resolve the artifact

If more than one plausible target exists, ask once and stop.

- **Plan mode:** review the selected or pasted plan, named plan file, or active plan. Rewrite plans in place when the path is known; do not implement from a plan review.
- **Work mode:** use named paths, an uncommitted diff, a commit, or a named branch comparison. Leave unrelated dirty files untouched.

### 1. Lock intent

Read [intent.md](intent.md). Reconstruct the user's Outcome, Stated requirements & details, Constraints & preferences, and Open questions. Do not ship a goal-only lock or invent non-goals.

### 2. Launch the reviewer

Read [review-brief.md](review-brief.md) and the active host adapter before launching a reviewer. Pass only the full intent lock, artifact boundary, current artifact, and mode. The reviewer must report findings only, make no side effects, and must not obtain another reviewer.

Prefer a fresh independent worker from a capable, currently available model. Do not hardcode a model identifier. If the host cannot provide an independent worker, stop rather than self-reviewing.

### 3–6. Validate, classify, apply, verify

Trace every finding to the artifact. Walk every locked requirement and constraint and mark it met, violated, or unclear. Promote missed or violated stated details to findings.

In plan mode, rewrite the positive plan and omit superseded approaches. In work mode, apply only localized, reversible fixes whose intended behavior is already clear. Treat design changes, material ambiguity, and insufficient evidence as blocking escalations.

Run the cheapest relevant verification after each apply. A failed check is not a pass. Stop on a blocking escalation or when the same findings recur without material artifact change.
