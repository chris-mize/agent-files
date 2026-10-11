---
name: agent-files-sync
description: Explicitly update this machine's always-on AGENTS.md and universal skills from Chris's agent-files repository. Invoke directly to pull the latest merged changes and install them into Cursor, Codex, and Claude Code.
disable-model-invocation: true
license: MIT
compatibility: Claude Code, Codex, or Cursor with shell access on macOS
---

# agent-files sync

Bring this machine's live instructions and skills up to date with `main` of `chris-mize/agent-files`. The installer copies; it never edits the repository.

## Steps

1. Find the clone. Try `~/Projects/agent-files` and `~/projects/agent-files`. If neither exists, ask Chris whether to clone `https://github.com/chris-mize/agent-files.git` and where.
2. Run `git status --short --branch` in the clone. If there are uncommitted changes or the branch is not `main`, stop and report them; do not stash, switch, or discard.
3. Run `git pull --ff-only`. If it fails, stop and report why.
4. Run `./install.sh --dry-run` and read every line.
   - `unchanged`, `skip`, and `adopt` lines need no confirmation.
   - Any line that replaces, backs up, or removes something (`->`, `remove stale`, `was backup`, `was symlink`) changes live files. List those lines for Chris and get a yes before continuing.
5. Run `./install.sh`, then `./install.sh --smoke`. A smoke failure means the install is incomplete; report its message.
6. Report in a few lines: the commits pulled (`git log --oneline <old>..<new>`), what changed live, any backups and where they are, and what was skipped because a tool is not installed on this machine. New sessions pick up the changes; Codex detects skill changes automatically.

## Undo

`./install.sh --uninstall` restores what was in place before the first install, including backed-up files and folders.
