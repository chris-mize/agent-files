# Auto-Review Anti-Patterns

Read this before classifying findings, applying fixes, rewriting a plan, or escalating. Run the exit check after every apply or plan rewrite.

## 1. Agent knowledge assumed

Findings or escalations must be understandable to a cold reader. Situate what was planned or built, contrast it with intent, and state the action or decision in plain language.

## 2. Over-literal integration

Do not paste reviewer prose, verdict tables, disagreement narration, or chat rebuttals into the plan. Use feedback to change the approach and write the positive plan that should exist now.

## 3. Objective narrowing or goal injection

Discard extra hardening, refactors, or features that serve an adjacent goal. Prefer the smallest change that meets the locked intent.

## 4. Negation residue

After dropping an approach, remove warnings about the absent approach. State only the positive plan or code.

## 5. Assumed intent or a thin lock

Every lock clause must trace to user text or a user-endorsed restatement. Do not invent non-goals. Do not omit earlier live requirements.

## 6. Unbounded artifact

Resolve the exact plan, path set, diff, commit, or branch before reviewing. Leave unrelated dirty files untouched.

## Related traps

- A work-mode architecture change is a blocking escalation, not an auto-fix.
- Choose reviewer models from the host's live menu. Do not hardcode one model or default to an expensive flagship.
- The parent is not the adversarial judge. The separate reviewer must not spawn nested reviewers.
- A failed cheap verification is not a pass.

## Exit check

Before summarizing success, answer yes to all:

- A cold reader can understand every finding or escalation.
- The plan or work contains no pasted review transcript.
- Every applied change serves the locked intent.
- No negation residue refers to removed approaches.
- The intent lock still matches user facts and includes their stated details.
- Each locked detail was checked against the artifact.
- Edits stayed inside the resolved artifact boundary.
- The summary lists changed paths and behavior changes plainly.
