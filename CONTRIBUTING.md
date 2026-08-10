# Contributing to cmize-skills

## Canonical ownership

The only skill bodies are under `src/skills/<skill-name>/SKILL.md`. Do not add host-specific copies or generated output. Native manifests belong under `src/.claude-plugin/`, `src/.codex-plugin/`, and `src/.cursor-plugin/`; repository marketplace catalogs belong at the repository root.

Each skill must:

- use lowercase letters, numbers, and hyphens in `name`;
- keep the frontmatter name equal to its directory name;
- describe both behavior and intended invocation conditions;
- keep `SKILL.md` below 500 lines;
- use package-relative links and avoid machine-specific absolute paths;
- keep progressive-disclosure references close to the skill that uses them.

## Platform references

Put behavior that genuinely differs by host in `references/platforms/<host>.md` or the host's native manifest metadata. Do not fork a shared workflow merely to change a command spelling. If a target requires a different file format, add an explicit adapter and document why it cannot use the shared Agent Skills format.

Manual-only behavior must use native invocation metadata where the host supports it and must be tested as a release gate. Prompt language alone is not enforcement.

## Changes and validation

Before opening a change:

```bash
python3 scripts/validate.py
python3 -m unittest discover -s tests -p 'test_*.py'
python3 src/skills/actor-critic-mode/scripts/capability_probe.py --self-test
python3 src/skills/actor-critic-mode/scripts/evaluate_runs.py --self-test
```

Review relative links, JSON manifests, Codex metadata, provenance, and the
direct-install dry run. Direct installs must write
`.cmize-skills-manifest.json`; test update and uninstall behavior, including
refusal to remove locally modified skills. The uninstaller may unlink only
manifest-listed files or symlink pointers; it must never remove a skill
directory or an unlisted user file. Do not add dependencies for checks that
the standard library can perform. Actor-critic changes must also pass the
capability-probe and evaluation-harness self-tests, without treating them as
evidence that a model improves on real tasks.

## Provenance

Every migrated or materially rewritten file must have an entry in [`docs/provenance.md`](docs/provenance.md). Confirm that the contributor has the right to redistribute imported text, remove secrets and personal data, and record any required attribution before publication.

## Release process

1. Update the canonical skill tree and documentation.
2. Run static validation and unit tests.
3. Run clean-install and host workflow smoke tests; record versions and evidence in [`docs/compatibility.md`](docs/compatibility.md).
4. Run an independent adversarial review of the release diff.
5. Update [`CHANGELOG.md`](CHANGELOG.md) and the bundle version in every manifest and every catalog field that the host schema permits; Codex and Cursor marketplace catalogs inherit the version from the plugin manifest because their strict schemas do not permit an entry version.
6. Verify the remote and public visibility before publishing.
7. Create the release commit and `v<version>` tag only after the user authorizes publication, then push the branch and tag.

Do not publish secrets, credentials, personal records, or files that are not covered by the provenance record.
