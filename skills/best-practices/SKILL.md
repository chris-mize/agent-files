---
name: best-practices
description: Raises the quality floor for substantive coding, research, planning, design, and review work. Use when implementing, changing, reviewing, researching, planning, or shipping a non-trivial deliverable, especially when asked for best practices, production readiness, simplicity, or to “make it not garbage.” Skip for casual questions, brainstorming, translation, purely stylistic rewrites, or when the user says “skip best-practices for this task.”
license: MIT
compatibility: Claude Code, Codex, or Cursor Agent Skills
---

# Best Practices

Raise work from “it works” to correct, context-aware, simple, maintainable, safe, and verified. Local project conventions and explicit requirements outrank generic advice. Prefer the smallest evidence-backed improvement over abstraction, essays, or speculative features.

Treat generated drafts as untrusted until behavior, interfaces, failure modes, dependencies, maintainability, and verification evidence are independently established.

## Opt-out and depth

- Skip entirely when the user says `skip best-practices for this task`.
- Adaptive depth: small tasks get a short sanity pass; consequential tasks get the full workflow.
- Explicit `quick pass` or `deep audit` overrides depth for that task only. Do not create sticky session state.

## Workflow

1. Identify outcome, users, constraints, and definition of done. Ask only a material blocking question.
2. Inspect relevant repository context, sources, call sites, patterns, dependencies, and tests before choosing an approach.
3. Classify risk. Escalate production data, public APIs, authz/authn, crypto, serialization, shell/SQL/HTML sinks, dependencies, concurrency, or irreversible operations. For unverified new packages, untrusted data reaching those sinks, authorization that exists only in prompt/model judgment, or lockfile/supply-chain edits: do not install or ship blindly—apply the minimum safe fix or refuse the unsafe step. When the work is security-substantive, follow `security-best-practices` / `security-threat-model` if available; if those skills are unavailable, still apply that fix-or-refuse rule, then state residual risk and ask only if a user decision is required.
4. Choose the smallest design that fully meets current requirements. Delete, reuse, or narrow before adding abstraction or dependencies. After done-criteria are set in step 1 (or explicitly updated with the user), do not weaken them to manufacture a pass.
5. Route and **read** the selected reference file before applying it. Do not infer a reference from its title. Ordinary work loads at most one reference; trivial work loads none. Load the full LLM-failure taxonomy for deep audits, complex reasoning, or when the compact check below flags a possible hallucination. If a specialized skill owns the task (`spec-first-planning`, `adversarial-review`, `code-simplifier`, frontend, security), let it own the workflow and contribute only the amateur-ish check plus verification gate.
6. Challenge the result: what would look amateur-ish to a maintainer or informed reviewer?
7. Verify the riskiest assumptions with external evidence when possible: commands/outputs for code; source triangulation or observable acceptance checks for research/plans. Self-critique alone is not proof.
8. If authoring, fix material amateur-ish flaws before presenting. If reviewing only, report findings and smallest fixes without silently changing the artifact.
9. Before declaring done, reapply the relevant quality check. Report only material findings with evidence, priority, smallest fix, and residual risk. Do not block on cosmetics or hypothetical scale.

## Compact LLM-failure check

Before shipping or approving, ask:

1. Did I invent a package, API, attribute, file, or behavior that is not evidenced?
2. Did I trust unvalidated external input or `as`/`any` at a trust boundary?
3. Did I miss failure cases the caller will hit (errors, empty, auth, concurrency, timeouts)?
4. Did I claim verification without showing the command/output/source that proves it?
5. Did I add non-requested behavior or skip an explicit requirement?
6. Did I weaken done-criteria after they were set to manufacture a pass?

If any answer is yes or unclear, fix or verify before completing. For deep detail, read `references/llm-failure-modes.md`.

## Non-negotiable quality gates

- Correctness and requirements beat cleverness.
- Context and reuse beat greenfield invention.
- Simple and maintainable beat speculative generality.
- Safety and meaningful checks are not optional simplifications.
- Completion claims require evidence; otherwise state residual risk.

## Routing

| Domain | Load |
|---|---|
| JS/TS implementation or review | `references/javascript-typescript.md` |
| Design, architecture, non-JS review, research, plans, ops, or cross-domain floor | `references/quality-and-verification.md` |
| Deep audit, hallucination risk, complex reasoning | `references/llm-failure-modes.md` |
| Specialized planning / simplify / frontend / security | Existing task skill owns workflow; apply only amateur-ish + verification gate |

## Output contracts

- **Implementation/review:** emit only relevant fields from outcome/assumptions, approach, evidence, amateur-ish risks, residual risk.
- **Research/planning:** emit only relevant fields from decision, evidence/source quality, uncertainty, alternatives, acceptance criteria, next verification step.
- **Low-risk auto-invocation:** default to no quality commentary when nothing material exists; otherwise cap at three bullets. Expand when the user asked for best practices, a deep audit, or “make it not garbage,” or when material risk/ambiguity remains. Do not emit ritual quality essays.

## Enforcement note

Model-selected guidance is not deterministic enforcement. Prefer machine-checkable project rules, linters, CI, validators, or review gates when hard constraints are required—prose skills are guidance, not a substitute for those gates.

## Rollback

Disable the bundle by removing the installed skill directory using the target-specific paths documented in the repository README. If an eval baseline exists, compare post-install behavior with it before retaining the skill; otherwise use fresh smoke prompts. Do not delete a shared skill directory without confirming it is managed by this bundle.
