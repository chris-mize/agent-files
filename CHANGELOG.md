# Changelog

All notable changes to the `cmize-skills` bundle are recorded here. The bundle uses one release version; individual skills do not have independent versions.

## [Unreleased]

### Added

- `reset-cursor-vscode-macos`, an explicit, human-supervised macOS workflow for auditing and reversibly resetting known local Cursor and VS Code state, using native app removal before residual cleanup, and retaining old profiles as inactive archives with an explicit post-test recovery choice.

## [1.0.0] - 2026-08-10

### Added

- Manifest-backed direct installs with safe updates, partial or full
  uninstalls, local-edit detection, and explicit override flags. Added a
  standalone manifest-only uninstaller that preserves skill directories and
  unlisted user files.
- Cross-host installation guidance that avoids duplicate Cursor discovery.
- `actor-critic-mode`, a bounded generator–critic operating mode with
  host-specific invocation references, capability probing, receipt validation,
  and a sanitized evaluation harness.

### Changed

- Made `.claude-plugin/marketplace.json` `metadata.version` authoritative for
  installer manifests and validation; schema-required version copies are
  checked against it.

## [0.1.0] - 2026-08-10

### Added

- Canonical Agent Skills tree for `adversarial-review`, `auto-review`, `deep-research`, and `best-practices`.
- Claude Code, Codex, and Cursor plugin manifests and repository marketplace catalogs.
- Platform reference files and Codex invocation metadata.
- Vendored, package-relative deep-research protocol and forward-test contract.
- Dependency-free validator, direct-install helper, fixtures, unit tests, and CI workflow.
- Compatibility, provenance, contribution, and release documentation.
