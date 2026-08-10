# cmize-skills

Portable Agent Skills for adversarial review, review orchestration, pluralistic research, and quality checks.

The public repository is `chris-mize/portable-skills`. The published plugin is named `cmize-skills`. One canonical skill tree lives in [`src/skills/`](src/skills/); Claude Code, Codex, and Cursor metadata point at that same tree. The repository does not generate or maintain copied skill bodies per host.

## Included skills

- `adversarial-review` — challenge a plan, design, implementation, or decision before approval.
- `auto-review` — explicitly run an independent adversarial review and then rewrite or safely fix the bounded artifact.
- `deep-research` — research across official/primary, real-user, and independent-expert lanes with claim-level evidence.
- `best-practices` — raise the quality floor for substantive implementation, planning, research, and review work.

`auto-review` is intentionally explicit-only. Prompt text is guidance, not a security boundary; the package uses each host's native manual-invocation metadata where available and release evidence records any remaining gaps.

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
/cmize-skills:auto-review
/cmize-skills:deep-research
/cmize-skills:best-practices
```

### Codex

Add the repository marketplace, then install `cmize-skills` from the plugin picker or CLI:

```bash
codex plugin marketplace add https://github.com/chris-mize/portable-skills.git
codex plugin add cmize-skills@cmize-skills
```

If the installed Codex surface uses the interactive picker, open `/plugins`, select the `cmize-skills` marketplace entry, and enable the plugin. Invoke skills explicitly with `$auto-review`, `$adversarial-review`, `$deep-research`, or `$best-practices`.

### Cursor

Add the repository marketplace with the Cursor Agent CLI, then select `cmize-skills` in Cursor's Plugins/marketplaces UI:

```bash
cursor agent plugin marketplace add https://github.com/chris-mize/portable-skills.git
```

Select the `cmize-skills` entry and install it. Invoke the installed skills explicitly with `/auto-review`, `/adversarial-review`, `/deep-research`, or `/best-practices`.

The exact UI labels and CLI availability are version-dependent; see [`docs/compatibility.md`](docs/compatibility.md) for tested surfaces.

## Direct-copy fallback

The dependency-free installer synchronizes the canonical skill directories into a host skill directory. It never generates a second skill body, refuses to overwrite an existing destination by default, and supports dry runs, selected skills, and dependency closure. Selecting `auto-review` also installs its required `adversarial-review` dependency.

```bash
# Preview all four skills for Codex.
python3 scripts/install.py --target codex --dry-run

# Copy only the review pair into Claude Code's personal skills directory.
python3 scripts/install.py --target claude --skills adversarial-review auto-review

# Preview a Cursor install at an explicit destination.
python3 scripts/install.py --target cursor --destination /path/to/skills --dry-run

# Symlink selected skills after inspecting the dry run.
python3 scripts/install.py --target codex --skills deep-research best-practices --symlink
```

Default personal destinations are `~/.claude/skills`, `~/.agents/skills`, and `~/.cursor/skills`. Codex also discovers the legacy `~/.codex/skills` location; pass `--destination ~/.codex/skills` when that is the intended surface. Use `--destination` for a project-local directory such as `.claude/skills`, `.agents/skills`, `.codex/skills`, or `.cursor/skills`. The destination must be a skills directory, not the plugin root.

To update a direct install, rerun the command with `--replace` after reviewing the dry run. To roll back, remove only the installed `cmize-skills` skill directories after confirming they are not shared with another bundle, then restore the prior version from its source or version-control checkout.

## Package layout

```text
src/
├── .claude-plugin/plugin.json
├── .codex-plugin/plugin.json
├── .cursor-plugin/plugin.json
└── skills/
    ├── adversarial-review/
    ├── auto-review/
    ├── best-practices/
    └── deep-research/
```

The shared `SKILL.md` files use the Agent Skills format. Platform differences live in native manifests, Codex metadata, and the `references/platforms/` files inside the skills. The deep-research protocol is vendored under `src/skills/deep-research/references/protocol/` so links remain package-relative.

## Dependencies and limitations

- Installation and validation use Python's standard library only.
- `deep-research` requires a host that can provide genuinely isolated, web-capable workers. It must stop and report a capability gap when that cannot be verified.
- `auto-review` requires a genuinely independent reviewer. A same-context self-review must not be labeled independent.
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
