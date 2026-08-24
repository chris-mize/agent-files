# Spike adapters (2026-08-24)

Measured on this machine. Adapter argv and install destinations must follow this file, not guessed paths.

## Binaries

| name | path | notes |
|---|---|---|
| cursor-agent | `/Users/cmize/.local/bin/cursor-agent` | version `2026.08.11-e8db854` (`cursor-agent --version` → `2026.08.11-e8db854`) |
| codex | `/opt/homebrew/bin/codex` | version `0.147.0` |
| claude | **not on PATH** | Claude adapter **skip**; never fake scores |
| uv | `/Users/cmize/.local/bin/uv` | installed during spike (`0.12.5`) |
| gh | `/opt/homebrew/bin/gh` | logged in as `chris-mize` |

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

## Skill discovery (live paths)

| path | status |
|---|---|
| `~/.cursor/skills` | **empty** (valid user install target) |
| `~/.cursor/skills-cursor` | **populated** (Cursor product skills: babysit, canvas, create-skill, …) |
| `~/.cursor/plugins/cache/cmize-skills` | **populated** (live plugin skills including best-practices, auto-review) |
| `~/.codex/skills` | **populated** |
| `~/.agents/skills` | **empty** |

Do **not** assume `~/.agents/skills` is where hosts load skills.

## AGENTS.md realpath (install refuse)

All three resolve to a **foreign git** tree (`Projects/dev-tools`):

- `realpath ~/.codex/AGENTS.md` → `/Users/cmize/projects/dev-tools/dotfiles/agents/AGENTS.md`
- `realpath ~/.claude/CLAUDE.md` → same
- `realpath ~/AGENTS.md` → same

Install **must refuse** writes through these paths (origin is not `chris-mize/agent-files`). Cursor has no safe global AGENTS.md; document a User Rules paste.

## Machine-readable destinations

```toml
[destinations]
cursor_skills = "~/.cursor/skills"
codex_skills = "~/.codex/skills"

[refuse_agents_md]
home = "~/AGENTS.md"
codex = "~/.codex/AGENTS.md"
claude = "~/.claude/CLAUDE.md"
```

Refuse AGENTS.md destinations (do not write; they resolve into `dev-tools`):

- `~/AGENTS.md`
- `~/.codex/AGENTS.md`
- `~/.claude/CLAUDE.md`

Cursor User Rules: paste `agents/AGENTS.md` manually. There is no global AGENTS.md that is not a foreign-git symlink.

## Env allowlist

Login CLIs need `HOME`. Allow: `PATH`, `HOME`, `USER`, `LANG`, `TERM`, `CURSOR_API_KEY`. Hash names of `~/.cursor` and `~/.codex` (not secret file bytes) into `effective_config_hash`.
