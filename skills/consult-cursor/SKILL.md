---
name: consult-cursor
description: Call Cursor's local Agent CLI for independent review or analysis, including Claude Opus 5.5 and Grok 4.7, from Codex or another working agent. Use for cross-family validation or a requested Cursor model. Reviewers must not launch more reviewers.
---

# Consult Cursor

Use the Cursor Agent CLI, `agent` (also named `cursor-agent`); locate it with `command -v agent`. The `cursor` command launches the editor. Follow [cross-model-validation](../cross-model-validation/SKILL.md), its [review brief](../cross-model-validation/references/review-brief.md), and [subagent supervision](../cross-model-validation/references/supervision.md). The owner keeps edit responsibility.

Run `agent --version`, `agent --help`, and `agent models` at the start of a workflow or after an update/error. Use exact IDs from the live list. These were available on 2026-10-11:

| Model | Normal | Deeper review |
|---|---|---|
| Opus 5.5 | `claude-opus-5-5-high` | `claude-opus-5-5-max` |
| Grok 4.7 | `grok-4.7-high` | `grok-4.7-xhigh` |

Choose the best supported effort variant for the task's difficulty, uncertainty, risk, and Chris's budget or explicit choice. Record the model ID, effort, and a brief reason before launch; do not inherit a silent default. Avoid `auto` when family matters. Report unavailable requested models or effort levels; never silently substitute.

Set `review_repo` to the absolute project, `review_brief` to the completed brief file, and `cursor_review_model` to the chosen ID. Each launch creates its own private directory and prints its path; retain that path with the process handle.

Resolve workspace trust before the first launch. Inspect the resolved project path and its instructions. For Chris's known repo or a fixture created for this task, include `--trust` on the initial call, as below. For an unfamiliar workspace, establish trust with Chris before using this command. Do not launch once just to discover a trust prompt.

```sh
(
set -o pipefail
review_dir=$(mktemp -d "${TMPDIR:-/tmp}/cursor-review.XXXXXX") || exit 1
printf 'REVIEW_DIR=%s\n' "$review_dir"
review_status=0
# Use only for an inspected known repo/task fixture, or a workspace Chris trusts.
agent \
  --trust --print --mode ask --workspace "$review_repo" \
  --model "${cursor_review_model:?Choose a model and effort explicitly}" \
  --output-format stream-json --stream-partial-output \
  "Read the review brief at $review_brief. Follow it; return findings only. Do not edit or delegate." </dev/null \
  2>"$review_dir/cursor-review.stderr" | tee "$review_dir/cursor-events.jsonl" || review_status=$?
printf '%s\n' "$review_status" >"$review_dir/pipeline.exit"
exit "$review_status"
)
```

Launch this through the owner's managed process tool with a short wait that returns a live handle. Keep polling the same job and reading its stream; do not run it through a blocking capture or lifetime timeout. `tee` preserves the raw stream while exposing it to the parent. `pipefail` keeps a CLI or logging failure from looking successful.

If the calling host blocks network access, CLI state files, or a nested sandbox, request its scoped per-command approval. Keep the receiving CLI's review restrictions; do not change persistent permissions, use `--force`/`--yolo`, or approve all MCPs. Ask mode requests read-only behavior; it is not an OS-enforced read-only filesystem. Retain the brief's no-mutation/no-delegation rule, including for external tools. Passing the brief's path keeps its contents out of process arguments.

Track `system/init` (session/model), `tool_call` starts/completions, and new assistant text. Some models also emit thinking events; count their arrival as activity without exposing private reasoning. Partial output includes duplicate flushes: new text has `timestamp_ms` and no `model_call_id`; use the terminal `result` as the authoritative answer. Require its success subtype, `is_error: false`, clean process/pipeline exit, and a complete review. A live process or exit zero alone is insufficient. Record requested and runtime-reported model identity separately. Do not resume the author's session or silently retry failed work.

Calls use existing Cursor authentication and hosted models. Keep credentials out of prompts. Installed help and live model listings govern exact syntax and availability. Sources: [CLI modes](https://cursor.com/docs/cli/overview), [headless CLI](https://cursor.com/docs/cli/headless).
