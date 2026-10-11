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

`run` exits 2 if `models` in `agent-files.toml` is empty.

## Promote a GitHub issue

```bash
agent-files promote https://github.com/chris-mize/agent-files/issues/1 --artifact agents
agent-files promote https://github.com/chris-mize/agent-files/issues/1 --artifact agents --approve
```

`--approve` is allowed only when `gh api user` login is `chris-mize`. Candidates are not executed.

## Layout

```
agents/AGENTS.md
skills/{best-practices,auto-review,adversarial-review,improve-against-evals}/
agents/evals/evals.json
docs/spike-adapters.md
```

Public GitHub Actions: lint, typecheck, pytest, and a redacted fake-adapter replay. No model calls. No secrets.
