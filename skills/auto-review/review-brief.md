# Reviewer Brief

Read this immediately before launching the reviewer.

Prompt the reviewer with:

- The complete LOCKED INTENT block from [intent.md](intent.md).
- Artifact type, path or boundary, full inlined plan if chat-only, and mode.
- A report-only instruction: no file edits, git mutations, external posts, or other side effects.
- The instruction to follow [adversarial-review](../adversarial-review/SKILL.md)'s decision tests, attack angles, guardrails, and report shape.
- The instruction to treat every stated requirement and detail as an acceptance check.
- The instruction that inferred bullets are weaker and must not become hard gates without evidence.
- The instruction that the reviewer is the separate judge and must not obtain nested reviewers.

Require:

- Verdict: `ready`, `ready with changes`, `not ready`, or `insufficient evidence`.
- Findings with impact, likelihood, confidence, and evidence tied to the artifact.
- Any violated locked detail.
- The smallest fix or simpler alternative.
- Whether a user decision is required.
- Residual risk.

Pass only minimum task-local context. Do not seed the reviewer's preferred answer or parent conclusions.
