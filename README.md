# agent-files

Canonical home for Chris Mize’s personal `AGENTS.md`, selected Agent Skills, colocated `evals.json`, and a tiny CLI that runs those evals on this machine’s Cursor and Codex CLIs.

This laptop is the tuner. A work laptop installs artifacts and can run evals with a local login.

## Install (work laptop)

After a tagged release:

```bash
uv tool install git+https://github.com/chris-mize/agent-files@v0.1.0
```

Until a tag exists, from a clone:

```bash
uv tool install -e .
./install.sh --dry-run
./install.sh
agent-files install --smoke
```

`install.sh` copies skills to destinations recorded in `docs/spike-adapters.md`. It **refuses** to write through `realpath` into a git repo whose origin is not `chris-mize/agent-files` (today `~/AGENTS.md`, `~/.codex/AGENTS.md`, and `~/.claude/CLAUDE.md` all resolve into `dev-tools`).

Cursor has no safe global `AGENTS.md` on this machine. Paste `agents/AGENTS.md` into Cursor User Rules if you want it always on.

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
