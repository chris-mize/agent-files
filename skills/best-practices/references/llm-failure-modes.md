# LLM Failure Modes

Use this reference for deep audits, complex reasoning, or when the router’s compact check flags possible hallucination. For each mode: signal → why → cheapest check → fix. Sources are labeled with scope limits.

## 1. Requirement / context conflict

- **Signal:** Solution ignores an explicit constraint, invents scope, or contradicts nearby code/docs.
- **Why:** Prompt+repo compression; fluency over fidelity.
- **Check:** Restate must/must-not; diff against user text and local conventions.
- **Fix:** Prefer explicit requirements and local patterns; delete non-requested behavior.

## 2. Missing corner cases

- **Signal:** Happy path only; no empty, auth failure, timeout, partial write, retry, or concurrency story.
- **Why:** Examples in training skew to success paths.
- **Check:** “What does the caller hit on day two?” List the top failure modes for this interface.
- **Fix:** Handle or explicitly defer material cases; add focused tests for the riskiest one.

## 3. Invented objects and attributes

- **Signal:** Fields, files, env vars, endpoints, or config keys that do not exist in the repo.
- **Why:** Plausible completion without grounding.
- **Check:** Search the codebase / schema / OpenAPI before using the name.
- **Fix:** Use real symbols; if missing, ask or add them deliberately with evidence.

## 4. Wrong inputs / incomplete generation

- **Signal:** Off-by-one APIs, truncated functions, TODO stubs presented as done, mismatched types.
- **Why:** Partial generation rewarded as helpfulness.
- **Check:** Trace call sites; compile/typecheck; mentally execute one real input.
- **Fix:** Finish or narrow scope; do not ship placeholders as complete.

## 5. Non-requested behavior

- **Signal:** Extra features, refactors, renames, or “improvements” outside the ask.
- **Why:** Helpfulness / demonstration bias.
- **Check:** Would a reviewer ask “why did you touch this?”
- **Fix:** Revert extras; keep the smallest change that meets the request.

## 6. API / library hallucination

- **Signal:** Package, method, option, or version that is not installed and not in official docs.
- **Why:** Memorized APIs drift; name collision with similar libraries.
- **Check:** Verify against lockfile + official docs (or package registry) before recommending.
- **Fix:** Use an evidenced API; prefer stdlib/existing deps.

## 7. Repository-context failure

- **Signal:** Reimplements helpers that already exist; ignores tests/linters; wrong module boundary.
- **Why:** Incomplete retrieval of nearby patterns.
- **Check:** Search for prior art and mirror the local idiom before inventing.
- **Fix:** Reuse and extend; align with project structure.

## 8. Type / validation theater

- **Signal:** `as T`, unchecked `JSON.parse`, trusted `response.json()`, broad `any`, schemas that do not catch real mistakes.
- **Why:** Types look like proof; runtime is ignored.
- **Check:** Where does untrusted data enter? Is there a runtime check?
- **Fix:** Validate at boundaries; narrow types to what is enforced.

## 9. Verification theater

- **Signal:** “Tests pass” / “production ready” without command output, oracle quality, or source triangulation.
- **Why:** Completion pressure; confidence without evidence.
- **Check:** Demand the cheapest decisive artifact (command, log, citation, screenshot).
- **Fix:** Run or cite evidence; otherwise state residual risk.

## 10. Weak test oracles

- **Signal:** Tests mirror implementation, mock everything, assert only snapshots/spy calls, miss property under change.
- **Why:** Easy green bars.
- **Check:** Would a broken implementation still pass?
- **Fix:** Assert observable outcomes and one meaningful edge.

## 11. Safety / sink blindness

- **Signal:** Untrusted data reaches SQL/HTML/shell/path/crypto without mediation; authz checked late or not at all.
- **Why:** Feature-first generation.
- **Check:** Mark trust boundaries and sinks; escalate to security skill when material.
- **Fix:** Validate/encode/parameterize; deny by default; do not “simplify away” checks.

## 12. Maintainability debt (AI smell cluster)

- **Signal:** Speculative options, wrapper cascades, pass-through modules, god coordinators, duplicate near-solutions.
- **Why:** Over-structuring looks professional.
- **Check:** Route to `code-simplifier` when cleanup is the job; otherwise delete unused generality.
- **Fix:** Smallest durable design for current requirements.

## Source notes (limitations)

- Bug taxonomies from LLM-generated code catalog recurring defect classes; treat them as descriptive, not a ranked production risk model. Benchmark bug distributions can diverge from GitHub-derived tasks.
- Code-hallucination taxonomies often restrict to explicit fact conflicts and may exclude ordinary logic/planning or syntax failures—hallucination checks are not a complete correctness gate.
- Repository-context hallucination studies show grounding failures against real codebases; scope is benchmarked settings. JS/TS agent-change prevalence is not established by Python-heavy corpora.
- Selective/missing API-doc use and library-hallucination work support dependency verification; registry existence alone is insufficient for supply-chain safety. Preprint and benchmark selection effects apply.
- Static-analysis datasets that find many AI maintainability smells under-sample runtime/security faults—still verify sinks and API correctness explicitly. LLM self-review is unreliable as a sole security gate; prefer scanners/tests/human review for security claims.

Do not cite statistics as decoration. Prefer local evidence over paper claims when deciding a fix.
