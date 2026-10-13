# v1 verification notes

Record of definition-of-done checks. Fake-adapter scores are plumbing only and are never provider scores.

## Isolation-only revert

`tests/test_required.py::test_isolation_only_win_reverts` is the required demo: crowded k/n unchanged while an isolated eval or skill-read marker improves, and `decide_keep` returns `keep=False` with `isolation_only=True`.

## Ablation

`agents/evals/files/ablation/AGENTS.md` is `agents/AGENTS.md` without the stand-alone-artifact bullet. Crowded keep of eval 3 must beat that overlay.

## Freeze review

`reviews/freeze-agents-3.json` is required before freeze. Eval 3 `source.review_path` points at that file.

## Host runs (2026-08-24)

- Fake `--eval 3 --repeats 1`: canary passed; eval 3 passed. Plumbing only.
- Cursor `--eval 3 --repeats 1`: canary passed; eval 3 failed; `skill_read=observed` (branch a). Harness spawned for real; the frozen eval is currently red on this wording.
- Codex `--eval 3 --repeats 1`: canary failed; batch aborted; `skill_read=skipped`. Fail closed (this machine is not logged in to Codex). No invented pass.
- Claude: binary not on PATH; adapter skip.
- `agent-files review --gate freeze --artifact agents --eval 3 --adapter fake` wrote `reviews/freeze-agents-3.json` with verdict `ready`.
- `agent-files install --dry-run` listed copies into `~/.cursor/skills` and `~/.codex/skills`.

## Host runs (2026-10-13)

Canonical crowded eval 3, three fresh workspaces per model, explicit high effort matching Chris's configured settings. All four preflight and four automatic batch canaries passed; all 20 host processes exited 0 without timeout. Frozen eval record, overlay and graders are unchanged.

| Model (exact CLI ID) | Adapter | Effort requested | Eval 3 k/n | Failure cause (repeat numbers are 1-based) |
| --- | --- | --- | --- | --- |
| `claude-opus-5-5-high` | Cursor | high | 0/3 | r1–3: missing literal Commands/Defaults headings |
| `claude-sonnet-5-5-high` | Cursor | high | 0/3 | r1: Commands; r2: Defaults; r3: both |
| `gpt-6.1-sol` | Codex | high | 0/3 | r1/3: Goal/Commands/Defaults/Tests; r2: also File tree |
| `gpt-6-luna` | Codex | high | 0/3 | r1: Commands/File tree; r2/3: Commands/Defaults |

Every graded failure is `grep_headings`: output inspection found the requested content under equivalent or combined headings (for example, “Command and defaults”). The hashed prompt names categories in lowercase prose, while the grader requires exact capitalized headings; the unused inline prompt specifies those names explicitly. This prompt/grader mismatch prevents these scores from ranking the models' standalone-spec quality. Sol r1 also retains “Buddy” planner history, a real behavior miss the residue check ignores; Sol r3 has borderline narration. Scores and frozen files remain unchanged.

Other known frozen-grader gaps: `hi` matches substrings such as “this,” and fenced code comments beginning with `#` can count as headings. Content completeness does not establish identical behavior: Sol r1 specifies no trailing newline; Luna r1/2 specify argument errors.

Cursor `2026.10.01-e373342` receipts confirm high effort and 300K context; Codex `0.162.1` receives `-c model_reasoning_effort="high"`. The tracked source prompt matches `sha256:b88bf53b7b0341dfeb465ff2823a802a27f5a132aacaa845c8cb9539f64ffd5e`; every eval-3 argv used that exact text. Local evidence at `~/.cache/agent-files/host-baseline-2026-10-13-high/` includes catalogs, code diff/hashes, receipts, scores and per-run output assessments. Ledger matrix batch IDs: `5114af14-3fb6-4bc9-8cfe-ac916f894061`, `115731d4-586b-4a64-9219-6d62666e999e`.

Cursor uses the real home environment: 300K context comes from personal settings, and ancestor `~/AGENTS.md` or user skills/plugins may also load (not confirmed by these traces). Codex uses an isolated home with the fixture overlay. These are adapter-specific host baselines, not an isolated comparison of identical environments. Codex traces do not expose resolved runtime model/effort; its table entries record the explicit requests.

Independent Opus 5.5 high follow-up review returned **ready with changes**; the requested evidence/documentation disclosures are recorded here. The receipt-writing driver is saved as `run-high.py` in the evidence directory. Total usage: 40 host calls and two reviews, within the approved 42-call cap.

The earlier 20-call attempt is excluded because it used an inline fallback and mixed efforts; its evidence remains at `~/.cache/agent-files/host-baseline-2026-10-13/`.
