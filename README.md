# agent-files

Canonical home for Chris Mize’s personal `AGENTS.md`, selected Agent Skills, colocated `evals.json`, and a tiny CLI that runs those evals on this machine’s Cursor and Codex CLIs.

## Install (any machine)

Requires [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/chris-mize/agent-files.git && cd agent-files
./install.sh --dry-run
./install.sh
./install.sh --smoke
```

After `git pull`, run `./install.sh` again; `--smoke` fails while the live instructions differ from the repo.

`install.sh` writes `agents/AGENTS.md` to `~/AGENTS.md` (Cursor) and links `~/.codex/AGENTS.md` (Codex) and `~/.claude/CLAUDE.md` (Claude Code and the Claude desktop Code tab) to it. It copies every skill in `skills/` to `~/.agents/skills` (Codex and Cursor) and `~/.claude/skills` (Claude Code). Tools not installed on the machine are skipped. Destinations and host behavior are recorded in `docs/spike-adapters.md`. `./install.sh --uninstall` restores the previous files.

## Run

```bash
agent-files run --artifact agents --eval 3 --adapter cursor --repeats 3
agent-files report
```

Eval 2 is plumbing (fake adapter / CI). Eval 3 is the first real `AGENTS.md` eval (standalone `SPEC.md`).

`models` in `agent-files.toml` accepts a flat list shared by adapters or a table of adapter-specific lists. `run` and `review` exit 2 when the selected adapter has no models. Each run batch checks one automatic canary per model; explicitly selecting eval 1 honors `--repeats`.

`codex_reasoning_effort` optionally pins Codex effort; Cursor effort is encoded in its model ID. The baseline configuration pins all four models to high, matching Chris's configured settings. Comparison identity includes the effective prompt hash and pinned effort, so these results cannot be silently mixed with different prompts or efforts.

Comparison identities from older runs differ from this baseline: `keep` and comparison reports refuse to mix them. Older ledger entries remain intact.

Referenced prompt files must exist and match their recorded SHA-256 hash before any model call. Eval 3's frozen candidate prompt is tracked; other candidate prompts remain quarantined. Frozen eval records and graders are unchanged.

## Promote a GitHub issue

```bash
agent-files promote https://github.com/chris-mize/agent-files/issues/1 --artifact agents
agent-files promote https://github.com/chris-mize/agent-files/issues/1 --artifact agents --approve
```

`--approve` is allowed only when `gh api user` login is `chris-mize`. Candidates are not executed.

## Layout

```
agents/AGENTS.md
skills/<name>/SKILL.md
agents/evals/evals.json
docs/spike-adapters.md
```

Public GitHub Actions: lint, typecheck, pytest, and a redacted fake-adapter replay. No model calls. No secrets.
