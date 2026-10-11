# Spike adapters (2026-08-24)

Measured on this machine. Adapter argv and install destinations must follow this file, not guessed paths.

## Binaries

| name | path | notes |
|---|---|---|
| cursor-agent | on `PATH` (`~/.local/bin`) | version `2026.08.11-e8db854` (`cursor-agent --version` → `2026.08.11-e8db854`) |
| codex | on `PATH` (Homebrew) | version `0.147.0` |
| claude | **not on PATH** | Claude adapter **skip**; never fake scores |
| uv | on `PATH` (`~/.local/bin`) | installed during spike (`0.12.5`) |
| gh | on `PATH` (Homebrew) | logged in as `chris-mize` |

## Cursor argv (confirmed)

Non-interactive eval spawn:

```text
cursor-agent -p --output-format stream-json --trust --sandbox enabled --workspace <ephemeral> --plugin-dir <plugin> --model <model> <prompt>
```

Notes:

- `--output-format json` is insufficient for skill-read; use `stream-json`.
- `--plugin-dir` loads a **plugin directory** (needs plugin metadata + `skills/`), not a bare skill folder.
- Login works with default user env (`apiKeySource: login`). `HOME` is required.
- Sentinel (composer-2.5-fast, ~15s): wrote `sentinel.txt` containing `ping`. Events included `system`, `user`, `thinking`, `tool_call` (`editToolCall`, `readToolCall`, `shellToolCall`). Truncated capture did not include a token/usage field.
- Stderr was empty on success.

### Cursor skill-read: branch (a) and (b)

Plugin at `/tmp/agent-files-spike/plugin` with `skills/spike-skill/SKILL.md`. Prompt: “Follow spike-skill. Prove the skill loaded.”

- **(a) observed:** `readToolCall` path `/private/tmp/agent-files-spike/plugin/skills/spike-skill/SKILL.md`
- **(b) marker:** workspace `.agent-files-skill-loaded` contained `spike-skill`

v1 keep-gate uses **(a)** when the stream contains a `readToolCall` whose path includes the skill’s `SKILL.md`; otherwise **(b)** if the marker file exists. Do not treat missing evidence as a pass.

Plugin metadata used in the spike:

```json
{"name":"spike-plugin","version":"0.0.1","description":"spike","skills":["./skills/spike-skill"]}
```

## Codex argv (confirmed)

Help: `codex exec --approve-for-me` routes approvals through automatic review using the workspace-write sandbox.

**Do not** pass `--sandbox` together with `--approve-for-me` (CLI error: cannot be used together).

Non-interactive flags that avoid approval hang:

```text
codex exec --json --approve-for-me --ephemeral -C <ephemeral> --skip-git-repo-check [-m <model>] <prompt>
```

Required process hygiene:

- Close stdin (`stdin=subprocess.DEVNULL`). The CLI prints `Reading additional input from stdin...` even then; with stdin closed it did **not** hang (failed in ~17s on 401).
- Do **not** copy `~/.codex/auth.json` into git.
- `--ignore-user-config` plus a fresh `CODEX_HOME` yields **401** (no auth). Runtime isolation: ephemeral `CODEX_HOME` **and** a runtime-only symlink of `~/.codex/auth.json` into that home (never committed).

This machine: `codex login status` → **Not logged in**. `~/.codex/auth.json` exists (mode 600) but API calls return 401 Unauthorized. Codex adapter must fail closed (error/skip), **never** invent a pass.

JSONL event types observed on 401: `thread.started`, `turn.started`, `error`, `item.completed`, `turn.failed`. No token/usage fields on those events.

### Codex skill-read: branch (c)

Cannot prove (a) or (b) without a working login. Crowded keep-gate on Codex is **skipped** (`skill_read=skipped`), not a pass. v1 may keep on Cursor only.

## Claude

`which claude` failed. Adapter: skip.

## Models (Cursor `--list-models`)

Eval default (cheap, sentinel-proven): `composer-2.5-fast`.

Full ids observed (non-exhaustive of the printed list): `auto`, `composer-2.5`, `composer-2.5-fast`, `cursor-grok-4.6-high-fast`, `gemini-3.7-flash-high`, plus many `gpt-5.3-codex-*`, `gpt-5.6-sol-*`, `claude-opus-*`, `claude-sonnet-*` variants.

`agent-files.toml` `models` is filled with `composer-2.5-fast` only so `run` is cost-bounded. Expand locally if needed.

## Where each host reads the always-on instructions

| host | reads |
|---|---|
| Codex CLI and app | `~/.codex/AGENTS.md` |
| Cursor | `~/AGENTS.md`, as an ancestor of any workspace under the home directory (observed on both laptops) |
| Claude Code, including the Claude desktop Code tab | `~/.claude/CLAUDE.md`, plus every `AGENTS.md` in the working directory's ancestors when the project has no `CLAUDE.md` ([memory docs](https://code.claude.com/docs/en/memory)) |

`~/AGENTS.md` is a real file. The other two are symlinks to it, so Claude Code sees one file and does not load the same content twice. Claude desktop **Cowork** sessions skip a symlinked `~/.claude/CLAUDE.md`; Cowork is not a target.

## Where each host reads user skills

| host | reads |
|---|---|
| Codex | `~/.agents/skills` ([skills docs](https://developers.openai.com/codex/skills)); same-named skills in two locations both appear |
| Cursor | `~/.agents/skills`, `~/.cursor/skills`, `~/.claude/skills`, `~/.codex/skills` |
| Claude Code | `~/.claude/skills` |

Skills install to `~/.agents/skills` (Codex and Cursor) and, when `~/.claude` exists, `~/.claude/skills` (Claude Code). Nothing installs to `~/.cursor/skills` or `~/.codex/skills`, and copies a previous install left there are removed. Project-scoped skills live in their project's `.agents/skills` and are not installed from here.

## Machine-readable destinations

```toml
[skills]
destinations = ["~/.agents/skills", "~/.claude/skills"]
create = ["~/.agents/skills"]

[instructions]
file = "~/AGENTS.md"
links = ["~/.codex/AGENTS.md", "~/.claude/CLAUDE.md"]
```

Install copies `agents/AGENTS.md` to `file`, points each link at it, and copies every `skills/<name>` into each skill destination. A destination whose parent directory is missing (the tool is not installed on this machine) is skipped unless it is listed in `create`. A symlink is replaced, never written through. A real instruction file is moved to `<name>.agent-files-backup`; a skill folder that differs from the repo and was not installed by a previous run is moved under `~/.agent-files-backups/`, outside every skill directory. `--uninstall` restores what was there before the first install.

## Env allowlist

Login CLIs need `HOME`. Allow: `PATH`, `HOME`, `USER`, `LANG`, `TERM`, `CURSOR_API_KEY`. Hash names of `~/.cursor` and `~/.codex` (not secret file bytes) into `effective_config_hash`.
