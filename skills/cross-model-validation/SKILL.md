---
name: cross-model-validation
description: Automatically cross-validate consequential work through local Codex and Cursor CLIs, using independent model families. Use for architecture, public interfaces, persistent data, production, security/privacy/financial impact, or hard-to-detect failures; also use when Chris requests multi-model review. Skip trivial edits. Reviewers must not launch more reviewers.
---

# Cross-model validation

The working agent owns edits and final judgment. Fresh reviewers return findings; they do not edit or delegate. These skills are installed together from the agent-files repository. Calls use existing accounts and consume their usage. Processes run here; selected context goes to hosted models. Keep credentials, unrelated context, and restricted project data out of prompts.

## Choose reviewers

Count model families, not harnesses: GPT in Cursor and GPT in Codex are both OpenAI. Use session metadata to identify the working model; a saved default does not prove which model is active.

| Working family | Consequential work | Higher-risk work |
|---|---|---|
| OpenAI | Opus 5.5 via Cursor | Opus 5.5 + Grok 4.7 via Cursor |
| Anthropic | OpenAI via Codex | OpenAI via Codex + Grok 4.7 via Cursor |
| xAI | OpenAI via Codex | OpenAI via Codex + Opus 5.5 via Cursor |

Where Codex is not installed, run the OpenAI reviewer through Cursor with an OpenAI model from `agent models`.

Use two reviewers for authorization-boundary changes, data migrations/deletion, live production or financial operations, broad effects across projects/users, expensive rollback, or serious failures ordinary checks could miss. Other consequential work gets one. For other known families, use OpenAI normally and add Opus for higher risk; report an unknown family before claiming diversity. Honor requested models and stronger project rules. Reuse a review covering the same version, scope, and required family.

## Run the review

```text
Owner → fixed brief → fresh reviewers → owner verifies findings → fixes → checks
                                                              ↓
                                            targeted review of material changes
```

1. Lock the user's intent, explicit details, constraints, and acceptance criteria. Respect project design-approval gates; a reviewer cannot approve on Chris's behalf.
2. Fix the review boundary and version. For Git work, capture HEAD, status, staged and unstaged diffs, and relevant untracked contents. Exclude unrelated dirty files. For other artifacts, record paths and content hashes. Pause edits to reviewed files until reviewers finish.
3. Complete [review-brief.md](references/review-brief.md) in a private temporary directory outside the project. Give reviewers the same raw evidence, without the author's self-assessment or another reviewer's conclusions. Include bounded artifact contents if paths are inaccessible.
4. Use [consult-cursor](../consult-cursor/SKILL.md) or [consult-codex](../consult-codex/SKILL.md). Start fresh sessions and [supervise them as subagents](references/supervision.md): retain process handles, read live events, and verify terminal status. Independent reviews may run concurrently against the fixed version. For a panel, vary emphasis—design and unnecessary complexity versus failures and missing checks—while both review all requirements.

## Resolve findings

Check each material finding against source or a focused test. Mark it accepted, rejected with evidence, or unresolved. Resolve disagreements through requirements and reproducible evidence, not votes. The owner applies in-scope fixes, runs checks, and compares the result with the original intent.

A material change needs targeted re-review. Default to one initial round and one follow-up. Stop for unresolved permission, model/access failures, or an evidenced stall; silence alone does not establish a stall. Report remaining material issues instead of looping or claiming completion. Empty, partial, blocked, or failed calls are incomplete reviews, never passes. Do not silently substitute requested models.

Report the artifact/version, selected reviewers, supported runtime model identity, findings and resolutions, checks actually run, and remaining gaps. Model agreement is not proof. Automatic skill selection is guidance, not an enforced hook.
