---
name: consult-codex
description: Call the local Codex CLI for independent OpenAI model review or analysis from Cursor or another working agent. Use when Cursor needs Codex models or cross-family validation. Reviewers must not launch more reviewers.
---

# Consult Codex

Use the Codex CLI, `codex` (locate it with `command -v codex`), with existing CLI authentication. If it is not installed, use an OpenAI model through [consult-cursor](../consult-cursor/SKILL.md) instead. Follow [cross-model-validation](../cross-model-validation/SKILL.md), its [review brief](../cross-model-validation/references/review-brief.md), and [subagent supervision](../cross-model-validation/references/supervision.md). The owner keeps edits; implementation by the other harness needs a separate, explicitly scoped handoff.

At the start of a workflow or after an update/error, check `codex --version`, `codex exec --help`, and `codex login status`. Read model candidates from `models_cache.json` in the Codex home (`$CODEX_HOME`, default `$HOME/.codex`); a successful call confirms access. The catalog observed on 2026-10-11 includes `gpt-6.1-sol` (normal review) and `gpt-6-astra` (optional deeper analysis). Honor requested models; report failures rather than silently replacing them. GPT through both harnesses is still one family.

Before each call, the owner must choose the best supported effort for the task, considering difficulty, uncertainty, risk, and Chris's budget or explicit choice. Check the selected model's `supported_reasoning_levels`; refresh stale metadata after updates/errors. Low/medium can suit narrow, straightforward checks; high suits complex logic and edge cases; xhigh/max can suit especially demanding reviews when supported. Exclude modes advertised as automatic delegation: reviewers must not delegate. Record the model, effort, and a brief reason before launch. Never inherit a silent default or silently downgrade an unsupported choice.

Set `review_repo` to the absolute project, `review_brief` to the completed brief, `codex_review_model` to the chosen ID, and `codex_review_effort` to the chosen supported level. Each launch creates its own private directory and prints its path; retain that path with the process handle.

```sh
(
set -o pipefail
review_dir=$(mktemp -d "${TMPDIR:-/tmp}/codex-review.XXXXXX") || exit 1
printf 'REVIEW_DIR=%s\n' "$review_dir"
review_status=0
codex -a never exec \
  --sandbox read-only --ephemeral -C "$review_repo" \
  -m "${codex_review_model:?Choose a model explicitly}" \
  -c "model_reasoning_effort=\"${codex_review_effort:?Choose a supported effort explicitly}\"" \
  --json -o "$review_dir/codex-review.txt" - <"$review_brief" \
  2>"$review_dir/codex-review.stderr" | tee "$review_dir/codex-events.jsonl" || review_status=$?
printf '%s\n' "$review_status" >"$review_dir/pipeline.exit"
exit "$review_status"
)
```

Launch this through the owner's managed process tool with a short wait that returns a live handle. Keep polling the same job and reading its stream; do not use blocking capture or a lifetime timeout. `tee` preserves events while exposing them to the parent; `pipefail` preserves CLI/logging failures.

Add `--skip-git-repo-check` only for intentional non-Git workspaces. Explicit read-only mode overrides broader local defaults. `-a never` fails denied operations; it grants no extra permissions. If the calling host blocks network access, CLI state files, or a nested sandbox, request its scoped per-command approval. Keep the receiving CLI read-only; do not change persistent permissions or use bypass flags. The shell sandbox does not constrain every external tool; retain the brief's no-mutation/no-delegation rule. `--ephemeral` does not promise zero logs or service-side retention.

Track `thread.started`, `turn.started`, and `item.started/updated/completed`, including command/tool status and public progress messages. `--json` is an event stream, not a promise of token-by-token text during reasoning. Require `turn.completed`, clean process/pipeline exit, no unresolved failure events, and the complete final-message file. A start acknowledgement or exit zero alone is insufficient. Record requested model/effort; if events omit model identity, report selection only. Do not use `resume`/`fork` to import the author's context into an independent review.

`exec` accepts the custom brief for code, plans, and documents. `codex review` has different flags and selector/prompt constraints; check its help before using it. Calls use hosted models and existing authentication; keep credentials out of prompts. Source: [non-interactive Codex](https://developers.openai.com/codex/noninteractive).
