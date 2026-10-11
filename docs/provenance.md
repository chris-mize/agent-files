# Provenance and redistribution record

This record covers the initial `cmize-skills` bundle. It is part of the release gate: a file is not publishable until its source, ownership, license, and attribution status are clear.

## Repository license

The repository contains the MIT license in [`LICENSE`](../LICENSE), copyright Christopher Mize, 2026. The MIT notice applies only to content the copyright holder is authorized to redistribute. It is not a substitute for checking imported or third-party material.

## Migrated skill content

- `src/skills/adversarial-review/SKILL.md` — based on the maintainer's local `$CODEX_HOME/skills/adversarial-review/SKILL.md`; substantially normalized for the shared Agent Skills format and package-relative references. Ownership: maintainer-authored. Redistribution: MIT.
- `src/skills/auto-review/SKILL.md`, `intent.md`, `anti-patterns.md`, `apply.md`, `examples.md`, and `review-brief.md` — based on the maintainer's local `$CODEX_HOME/skills/auto-review/` files; normalized for host-neutral use. Ownership: maintainer-authored. Redistribution: MIT.
- `src/skills/deep-research/SKILL.md` — based on the maintainer's local `$CODEX_HOME/skills/deep-research/SKILL.md`; absolute local paths were removed. Ownership: maintainer-authored. Redistribution: MIT.
- `src/skills/deep-research/references/protocol/RESEARCH_PROTOCOL.md`, `WORKER_CONTRACT.md`, `EVIDENCE_RUBRIC.md`, `REPORT_CONTRACT.md`, and `FORWARD_TESTS.md` — based on the maintainer's local `$AGENT_SKILLS_HOME/deep-research/` protocol files; links and validator references were rewritten to be package-relative. Ownership: maintainer-authored. Redistribution: MIT.
- `src/skills/best-practices/SKILL.md` and `references/` — based on the maintainer's local `$CODEX_HOME/skills/best-practices/` files; machine-specific rollback paths were replaced with README-directed instructions. Ownership: maintainer-authored. Redistribution: MIT.
- `src/skills/actor-critic-mode/SKILL.md`, `references/`, and `scripts/` — based on the maintainer's local actor-critic-mode skill tree; Codex and Cursor invocation differences were normalized into platform references, and local capability paths were removed from the research ledger. Ownership: maintainer-authored. Redistribution: MIT.
- `src/skills/reset-cursor-vscode-macos/SKILL.md`, `references/`, and Codex invocation metadata — new maintainer-authored macOS recovery guidance synthesized from public Apple, Cursor, Microsoft, GitHub, Homebrew, SQLite, POSIX, Agent Skills, public user-report, and named-practitioner sources linked in the evidence reference. No third-party source text or executable code was imported. Ownership: maintainer-authored. Redistribution: MIT.

## New integration content

- `src/.claude-plugin/plugin.json`, `src/.codex-plugin/plugin.json`, and `src/.cursor-plugin/plugin.json` — new maintainer-authored manifests.
- `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`, and `.cursor-plugin/marketplace.json` — new maintainer-authored marketplace catalogs.
- `src/skills/*/references/platforms/` and Codex `agents/openai.yaml` files — new maintainer-authored host integration metadata, based on the documented host schemas named in the README.
- `scripts/`, `tests/`, `.github/workflows/`, and all top-level documentation —
  new maintainer-authored release tooling and documentation, including the
  manifest-backed direct-install lifecycle.

## Third-party material and audit result

The bundled skill bodies do not intentionally include copied vendor code, credentials, private records, or proprietary built-in platform material. Host documentation and the Agent Skills specification are linked as external references, not redistributed as files. Any future imported text, sample, icon, or dependency must receive a new entry here with its license and required attribution before release.

## `v1.0.0` pre-release audit

Audit result: `pass` for the `1.0.0` release whose canonical `src/`
fingerprint is `5303672d1d1ab2a57eab8adf05923ea807c066b147b69cef6415d82b803453c9`
(excluding generated Python bytecode).

- Reviewed all release files for credentials, private records, personal data, and proprietary platform material; no publishable secret or personal record was found.
- Reviewed external URLs; they point to the public repository or documentation references and do not redistribute third-party source files.
- Confirmed the only machine-path examples are intentional validator fixtures and documented install destinations outside `src/skills`.
- Confirmed no generated skill bodies, build artifacts, icons, or untracked runtime outputs are part of the release candidate.
- Confirmed every migrated skill and protocol file, including actor-critic-mode, is covered by the ownership and redistribution entries above.
- A fresh independent release review found no actionable provenance, schema, portability, or release-gate findings. Claude unavailability and blocked deep-research capabilities remain documented residual gaps.

This audit is evidence for the candidate only; repeat it if canonical `src/` content changes after the fingerprint is recorded.

## Unreleased reset-skill candidate

- Canonical `src/` fingerprint: `bb3e905474f14a026df04b2a32e50d20a7a2f9794251ff6d5dbd1269fecf4fea`, excluding generated Python bytecode.
- The new skill and references are maintainer-authored synthesis. Public third-party sources are linked rather than copied; no executable third-party code, credentials, private records, or personal data were imported.
- Static validation and 27 unit tests passed for this source identity. A Claude-target direct-install dry run and read-only Cursor and Codex explicit-invocation/reference-loading smoke tests passed for prior fingerprint `ba92e3ffed9c05cf93c0d20bb47be7e5d51493d7197a93f40621abc86ea0bda3`; repeat them before attributing host-runtime evidence to the current archive/recovery-policy revision.
- Claude Code runtime behavior remains untested because Claude Code is unavailable in the recorded environment. Cursor and Codex results are behavioral evidence, not host-enforced mutation denial.
- Independent adversarial review findings were applied to the manual-only target-change boundary, conversation/sync scope, uninstall ordering, receipt state model, archive recovery policy, and evidence bookkeeping.
