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
