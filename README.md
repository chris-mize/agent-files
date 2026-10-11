# cmize-skills

Portable Agent Skills for adversarial review, actor-critic quality, review orchestration, pluralistic research, quality checks, and macOS editor recovery.

The public repository is `chris-mize/portable-skills`. The published plugin is named `cmize-skills`. One canonical skill tree lives in [`src/skills/`](src/skills/); Claude Code, Codex, and Cursor metadata point at that same tree. The repository does not generate or maintain copied skill bodies per host.

## Included skills

- `adversarial-review` — challenge a plan, design, implementation, or decision before approval.
- `actor-critic-mode` — explicitly run a bounded generator–critic quality mode with fresh verification and receipts.
- `auto-review` — explicitly run an independent adversarial review and then rewrite or safely fix the bounded artifact.
- `deep-research` — research across official/primary, real-user, and independent-expert lanes with claim-level evidence.
- `best-practices` — raise the quality floor for substantive implementation, planning, research, and review work.
- `reset-cursor-vscode-macos` — audit and reversibly reset known local Cursor and VS Code state on macOS, then guide a separately confirmed uninstall before manual reinstall.

`auto-review` is intentionally explicit-only. Prompt text is guidance, not a security boundary; the package uses each host's native manual-invocation metadata where available and release evidence records any remaining gaps.

`actor-critic-mode` is also explicitly invoked. It must stop or report a
degraded `not_confirmed` state when fresh role dispatch, model identity, or
required receipts cannot be verified; it does not claim that prompt-only role
instructions are a host security boundary.

## Install as a plugin

Plugin installation is the preferred path because it preserves the `cmize-skills` namespace and the host's native update behavior.

### Claude Code

In Claude Code, add the repository marketplace and install the plugin:

```text
/plugin marketplace add https://github.com/chris-mize/portable-skills.git
/plugin install cmize-skills@cmize-skills
```

The plugin-qualified commands are:

```text
/cmize-skills:adversarial-review
/cmize-skills:actor-critic-mode
/cmize-skills:auto-review
/cmize-skills:deep-research
/cmize-skills:best-practices
/cmize-skills:reset-cursor-vscode-macos
```

### Codex

Add the repository marketplace, then install `cmize-skills` from the plugin picker or CLI:

```bash
codex plugin marketplace add https://github.com/chris-mize/portable-skills.git
codex plugin add cmize-skills@cmize-skills
```

If the installed Codex surface uses the interactive picker, open `/plugins`, select the `cmize-skills` marketplace entry, and enable the plugin. Invoke skills explicitly with `$actor-critic-mode`, `$auto-review`, `$adversarial-review`, `$deep-research`, `$best-practices`, or `$reset-cursor-vscode-macos`.

### Cursor

Add the repository marketplace with the Cursor Agent CLI, then select `cmize-skills` in Cursor's Plugins/marketplaces UI:

```bash
cursor agent plugin marketplace add https://github.com/chris-mize/portable-skills.git
```

Select the `cmize-skills` entry and install it. Invoke the installed skills explicitly with `/actor-critic-mode`, `/auto-review`, `/adversarial-review`, `/deep-research`, `/best-practices`, or `/reset-cursor-vscode-macos`.

The exact UI labels and CLI availability are version-dependent; see [`docs/compatibility.md`](docs/compatibility.md) for tested surfaces.

### Avoiding duplicate discovery

Use one distribution method per host: either install the plugin through that
host's plugin manager or use the direct-copy installer. Do not install the same
skills both ways.

Cursor also discovers user-level skills from `~/.agents/skills/` and
`~/.cursor/skills/`, and for compatibility from `~/.claude/skills/` and
`~/.codex/skills/`. That means a direct copy can serve more than one host:

- **Claude Code + Cursor:** install once to `~/.claude/skills/`; do not also
  install to `~/.cursor/skills/`.
- **Codex + Cursor:** install once to `~/.agents/skills/`; do not also install
  to `~/.cursor/skills/`.
- **All three:** install directly to `~/.claude/skills/` for Claude Code and
  Cursor, then install the Codex plugin through Codex's plugin manager. This
  keeps a second direct copy out of Cursor's discovery paths.

If you choose plugins, install `cmize-skills` separately through each host's
native plugin UI or CLI and do not use the direct installer for those same
host/name pairs. Plugin managers own their installed copies and their
update/uninstall lifecycle.

## Direct-copy fallback

The dependency-free installer synchronizes the canonical skill directories into
a host skill directory. It never generates a second skill body, refuses to
overwrite an existing destination by default, and supports dry runs, selected
skills, dependency closure, updates, and authoritative uninstall. Selecting
`auto-review` also installs its required `adversarial-review` dependency.

```bash
# Install all bundled skills for Claude Code (also makes them visible to Cursor).
python3 scripts/install.py --target claude --all

# Install all bundled skills for Codex (also makes them visible to Cursor).
python3 scripts/install.py --target codex --all

# Preview a Cursor install at an explicit destination.
python3 scripts/install.py --target cursor --destination /path/to/skills --all --dry-run

# Copy only the review pair into a fresh destination.
python3 scripts/install.py --target claude --skills adversarial-review auto-review

# Symlink selected skills after inspecting the dry run.
python3 scripts/install.py --target codex --skills deep-research best-practices --symlink
```

Omitting `--all` and `--skills` also selects every skill for a fresh install.
Default personal destinations are `~/.claude/skills`, `~/.agents/skills`, and
`~/.cursor/skills`. Codex also discovers the legacy `~/.codex/skills` location;
pass `--destination ~/.codex/skills` when that is the intended surface. Use
`--destination` for a project-local directory such as `.claude/skills`,
`.agents/skills`, `.codex/skills`, or `.cursor/skills`. The destination must be
a skills directory, not the plugin root.

Every successful direct install writes
`<destination>/.cmize-skills-manifest.json`. The manifest records the bundle
version, source fingerprint, installation mode, and the exact files owned by
this installer. It prevents an update or uninstall from touching unmanaged
skills, removes managed files that disappear from the source on update, and
detects local edits before destructive operations.

```bash
# Preview and then update the manifest-owned install.
python3 scripts/install.py --target claude --update --dry-run
python3 scripts/install.py --target claude --update

# If a managed skill was intentionally edited, review it before replacing it.
python3 scripts/install.py --target claude --update --replace

# Preview and then remove every manifest-listed file.
python3 scripts/uninstall.py --target claude --dry-run
python3 scripts/uninstall.py --target claude

# Remove only one managed skill; the manifest remains for the others.
python3 scripts/uninstall.py --target claude --skills best-practices

# Remove only manifest-listed files even if a managed skill has local edits.
python3 scripts/uninstall.py --target claude --force
```

The standalone uninstaller never removes a skill directory. It removes only
manifest-listed files and symlink pointers, preserves unlisted user files, and
leaves skill directories in place, even when they become empty. The
`install.py --uninstall` form remains available as a compatibility alias.
Without a valid manifest, the uninstaller refuses to guess which files it
owns.
Partial uninstall refuses to remove `adversarial-review` while `auto-review`
remains managed, because that would leave a broken dependency.

The installer refuses to claim an existing unmanaged install unless
`--replace` is explicitly supplied during a fresh install. For a project-local
destination, repeat the same `--target` and `--destination` on every update or
uninstall command.

## Package layout

```text
src/
├── .claude-plugin/plugin.json
├── .codex-plugin/plugin.json
├── .cursor-plugin/plugin.json
└── skills/
    ├── adversarial-review/
    ├── actor-critic-mode/
    ├── auto-review/
    ├── best-practices/
    ├── deep-research/
    └── reset-cursor-vscode-macos/
```

The shared `SKILL.md` files use the Agent Skills format. Platform differences live in native manifests, Codex metadata, and the `references/platforms/` files inside the skills. The deep-research protocol is vendored under `src/skills/deep-research/references/protocol/` so links remain package-relative.

## Dependencies and limitations

- Installation and validation use Python's standard library only.
- `deep-research` requires a host that can provide genuinely isolated, web-capable workers. It must stop and report a capability gap when that cannot be verified.
- `auto-review` requires a genuinely independent reviewer. A same-context self-review must not be labeled independent.
- `reset-cursor-vscode-macos` is a human-supervised recovery procedure, not an enforcement boundary. It removes the verified app before residual-state cleanup, retains old profiles as inactive archives, and asks after the clean-state test whether to keep them reference-only, recover selected configuration, or perform a warned full-profile rollback. Reset, restore, and uninstall guidance requires an interactive standalone Claude Code CLI session outside Cursor and VS Code, and the user performs every target rename or app-removal action manually. Cursor and Codex use is audit-only; Claude runtime behavior is untested until recorded in [`docs/compatibility.md`](docs/compatibility.md).
- Manual-only invocation metadata can be checked by hosts, but no prose skill is a security control. Do not use these skills as authorization, secret-handling, or compliance enforcement.
- Research lanes may be restricted by login requirements, robots policies, network access, or unavailable services. The report must preserve those gaps.

## Development checks

Run the dependency-light validator before release:

```bash
python3 scripts/validate.py
python3 -m unittest discover -s tests -p 'test_*.py'
```

The validator checks manifests, marketplace paths, skill frontmatter, relative links, support files, Codex policy metadata, and machine-specific paths. It does not prove host behavior. Host evidence and limitations belong in [`docs/compatibility.md`](docs/compatibility.md).

See [`CONTRIBUTING.md`](CONTRIBUTING.md), [`docs/provenance.md`](docs/provenance.md), and [`CHANGELOG.md`](CHANGELOG.md) before making a release.
