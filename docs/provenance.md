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

## New integration content

- `src/.claude-plugin/plugin.json`, `src/.codex-plugin/plugin.json`, and `src/.cursor-plugin/plugin.json` — new maintainer-authored manifests.
- `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`, and `.cursor-plugin/marketplace.json` — new maintainer-authored marketplace catalogs.
- `src/skills/*/references/platforms/` and Codex `agents/openai.yaml` files — new maintainer-authored host integration metadata, based on the documented host schemas named in the README.
- `scripts/`, `tests/`, `.github/workflows/`, and all top-level documentation — new maintainer-authored release tooling and documentation.

## Third-party material and audit result

The bundled skill bodies do not intentionally include copied vendor code, credentials, private records, or proprietary built-in platform material. Host documentation and the Agent Skills specification are linked as external references, not redistributed as files. Any future imported text, sample, icon, or dependency must receive a new entry here with its license and required attribution before release.

## Final pre-release audit

Audit result: `pass` for the release candidate whose canonical `src/` fingerprint is `404867decdfe3d8305206520560052f91a7f53a7e41a3ab2c40db7e53f9c16fb`.

- Reviewed all release files for credentials, private records, personal data, and proprietary platform material; no publishable secret or personal record was found.
- Reviewed external URLs; they point to the public repository or documentation references and do not redistribute third-party source files.
- Confirmed the only machine-path examples are intentional validator fixtures and documented install destinations outside `src/skills`.
- Confirmed no generated skill bodies, build artifacts, icons, or untracked runtime outputs are part of the release candidate.
- Confirmed every migrated skill and protocol file is covered by the ownership and redistribution entries above.
- A fresh independent release review found no actionable provenance, schema, portability, or release-gate findings. Claude unavailability and blocked deep-research capabilities remain documented residual gaps.

This audit is evidence for the candidate only; repeat it if canonical `src/` content changes after the fingerprint is recorded.
