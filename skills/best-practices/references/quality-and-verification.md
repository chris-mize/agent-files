# Quality Floor and Verification

Cross-domain floor for code, research/docs, data/analysis, UI, plans/decisions, and operations. Route to specialized skills instead of re-implementing their checklists.

## Universal floor

Ask: what makes this amateur-ish, and what is the smallest evidence-backed improvement?

| Pillar | Amateur-ish signal | Stronger move |
|---|---|---|
| Correct | Diverges from requirements or reality | Restate done criteria; fix against evidence |
| Context-aware | Ignores local patterns/tools | Reuse project conventions |
| Simple | Speculative abstraction / extra features | Delete or narrow to current need |
| Maintainable | Clever/overbuilt even when tests pass | Clear names; delete generality; route to `code-simplifier` when needed |
| Safe | Checks removed; sinks unmediated | Keep meaningful guards |
| Verified | Confidence without artifact | Cheapest decisive external evidence |

Local conventions and explicit user requirements win over generic advice. For code review depth, keep a practitioner floor in view (design fit, functionality/edges, complexity especially over-engineering, meaningful tests, naming/docs, whole-diff context)—aligned with common engineering review guidance, used here as practitioner guidance rather than a measured claim.

## Interoperability

- **Planning / specs:** `spec-first-planning` owns outcome specs and acceptance criteria. Contribute only amateur-ish gaps (missing done checks, unverified assumptions) and verification gate.
- **Simplification:** `code-simplifier` owns smell cleanup workflows.
- **Frontend UI polish:** `frontend-skill` owns visual/composition guidance.
- **Security:** `security-best-practices` / `security-threat-model` own deep security work. Handoff when the change involves unverified dependencies, trust-boundary sinks, authorization design, crypto, or supply-chain/lockfile risk—not for every ordinary edit.
- **Adversarial critique:** `adversarial-review` / `auto-review` own structured challenge loops.

Do not duplicate their full workflows or contradict their domain rules.

## Verification matrix

Pick the cheapest decisive check for the riskiest assumption.

| Work type | Prefer | Stop / escalate when |
|---|---|---|
| Code change | typecheck/lint/build; focused behavioral test; call-site read | Auth, crypto, data loss, public API—broaden tests + review |
| Review-only | Ranked material findings + smallest fix | Silent edits requested? Don’t; report instead |
| Research / docs | Primary sources; date/version; contradicting view | Single blog as sole authority for a consequential decision |
| Data / analysis | Schema check; row counts; spot-check outliers; repro steps | Irreversible writes without dry-run/backup story |
| UI | Real interaction path; empty/error/loading states | Accessibility or security sinks touched—deepen |
| Plans / decisions | Observable acceptance criteria; non-goals; rollback | Missing done definition or unverified constraints |
| Operations | Dry-run; idempotency; blast radius; monitoring | Production mutate without confirm + recovery path |

When tools/runtime are unavailable, say what could not be verified and residual risk. Do not fabricate pass evidence.

**Oracle quality:** a useful check asserts observable behavior at the real boundary under change and would fail on a plausible bug. Self-scored checklists, mutable rubrics rewritten to pass, and mock-only suites that never exercise the boundary are not sufficient oracles. Mocks may isolate externals when at least one contract/integration check covers the seam.

## Material-defect stop conditions

Block completion (or explicitly flag residual risk) when any of these remain:

1. Invented dependency/API/file presented as real.
2. Unvalidated trust-boundary data treated as typed/safe.
3. Claimed “tests pass” / “verified” without artifact.
4. Plan/decision lacking observable acceptance criteria for consequential work.
5. Safety check removed to “simplify.”
6. Explicit user requirement unmet.
7. Done-criteria weakened after they were set in order to claim pass.

Do not block on formatting preferences, naming bikesheds, or hypothetical hyper-scale.

## Compact output examples

**Implementation (only if material issues or audit requested):**

```markdown
Approach: reuse the existing HTTP helper; add status and schema checks.
Evidence: focused test command (pass); no unverified dependencies.
Amateur-ish risks fixed: removed unchecked type assertion; handle non-OK HTTP.
Residual: no soak test for cache stampede under multi-tab load.
```

**Research / plan:**

```markdown
Decision: reuse the existing middleware pattern.
Acceptance: observable error response, metrics, and a focused fixture.
Uncertainty: unknown proxy behavior—confirm it before enforcing the rule.
Next verification: staging monitor-only window plus false-positive review.
```

**Low-risk auto-invocation:** no commentary if clean; otherwise ≤3 bullets.

## Enforcement fallback

If model-selected activation is not enough for a repo, add project rules, linters, CI, validators, or review gates. Hard constraints that agents ignore in prose often only stick when they become machine-checkable. Guidance is not enforcement.
