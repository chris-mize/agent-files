---
name: reset-cursor-vscode-macos
description: Audits and reversibly resets known local Cursor and Visual Studio Code state on macOS, then guides a separately confirmed uninstall before manual reinstall. Invoke directly for Cursor or VS Code corruption, lag, clean-profile testing, local conversation cleanup, or a full known-local-state reset.
disable-model-invocation: true
license: MIT
compatibility: Claude Code, Cursor, or Codex Agent Skills on macOS; target changes are always performed manually
---

# Reset Cursor and VS Code on macOS

This is a human-supervised recovery procedure, not a cleanup script or security boundary. Optimize for recovering a usable editor without destroying projects, worktrees, credentials, organization-managed state, or inactive archives the user chose to retain.

## Read as needed

- Before classifying any path, read [references/path-catalog.md](references/path-catalog.md).
- Before writing or using a receipt, read [references/receipt.md](references/receipt.md).
- When a path, behavior, or warning needs its evidence basis, read [references/evidence.md](references/evidence.md).

## Meaning of success

`complete` means only that every verified, eligible, known user-local path in the named scope was moved out of its active location and any selected app bundle was manually removed and verified absent. Omitting a known eligible path makes the result `partial`, even when the user intentionally excludes it.

It never means forensic erasure or complete account removal. Backups, Trash, Keychain, cloud data, remote hosts, APFS snapshots, Time Machine, unified logs, MDM, and undocumented state may remain.

## Host boundary

| Runtime | Audit | Reset, restore, or uninstall guidance |
|---|---|---|
| Interactive standalone Claude Code CLI, outside Cursor and VS Code | allowed | allowed; the user performs every target change manually |
| Claude Code inside a Cursor or VS Code terminal/extension | allowed | blocked |
| Cursor Agent or Cursor CLI | allowed | blocked after the read-only plan |
| Codex or another compatible host | allowed | blocked after the read-only plan |
| Headless, cloud, scheduled, or non-interactive session | allowed | blocked after the read-only plan |

There is no reliable portable environment variable that proves standalone execution. Before any reset, restore, or uninstall guidance:

1. Ask the user to attest that this is an interactive standalone Claude Code CLI session outside Cursor and VS Code.
2. Inspect process ancestry only as supporting evidence.
3. Stop if the selected app is the host, an ancestor, still running, or uncertain.

The agent never performs target renames, app removal, package-manager uninstall, shell-profile changes, or permanent deletion. It may write and update the private receipt only from a qualified standalone Claude Code session. The user performs target changes in Finder or, for a provenance-verified package-manager installation, types one exact previewed plain uninstall command and reports completion for read-only verification.

## Hard guardrails

Never issue or recommend:

- any agent-executed target mutation or generated destructive shell command, except one exact user-executed plain package-manager uninstall command for a provenance-verified package;
- `rm`, recursive deletion, broad globs, or mutation through `find`;
- `sudo`, force quit, `pkill`, recursive ownership changes, or SIP changes;
- Homebrew `--zap`, package-manager force flags, or receipt forgetting as file removal;
- Keychain `security` commands, secret dumps, MDM/profile commands, or cloud/API deletion;
- direct Background Task Management database edits or parsing `launchctl print` as an API;
- mutation of a path discovered only by substring, Spotlight, process output, or a broad vendor pattern;
- automatic app-to-Trash actions, Trash emptying, reinstall, or automatic escalation.

Model instructions and typed confirmations do not enforce these rules. The manual Finder boundary, exact literals, host permission prompts, and user review reduce accidental risk; they do not resist a malicious process or user. If Finder cannot perform a non-overwriting same-parent rename, stop.

## Protected by default

Do not mutate:

- projects, repositories, `.git`, Git worktrees, `.cursor`, `.vscode`, or `.code-workspace` project content;
- skills, rules, custom agents, hooks, MCP files, permissions, or user-authored instructions;
- remote server roots, containers, WSL, SSH hosts, network volumes, or cloud placeholders;
- Keychain, account/cloud conversations, synced data, MDM profiles, managed preferences, system helpers, or uncertain shared state;
- the receipt directory or the installed copy of this skill.

Treat organization management, sync, updater registration, and background-item state as `unknown` unless direct evidence resolves them. Unknown required state blocks an unqualified `complete` result.

## Modes

Use one mode per explicit invocation:

- `audit` — inspect and plan; no target mutation.
- `reset` — guide and verify reversible manual moves of active local-state roots to sibling archives.
- `record-test` — record the user's manual before/after result.
- `restore` — after a clean-state test, ask whether archives remain reference-only, supply selective configuration, or become a full-profile rollback.
- `uninstall` — guide native app removal first, then clear known residual active state.

Never infer a mode. Ask if the user did not name one.

## 1. Audit

Read the path catalog, then:

1. Verify macOS and an interactive host.
2. Require the user to select Cursor, VS Code, or both explicitly. Never default a reset or uninstall to both products.
3. Identify each installed edition and exact app bundle. Read its bundle identifier; do not infer identity from the filename alone.
4. Identify installation provenance: direct app, Homebrew, portable/custom root, or organization-managed. Do not guess.
5. Check custom data, extension, shared-data, Cursor config, and Copilot roots from environment and launch configuration without printing secrets.
6. Ask whether VS Code Settings Sync, Copilot Session Sync, Cursor cloud history, or another sync mechanism is active. Require the user to pause relevant sync or sign out before a clean-conversation test; otherwise mark the test `inconclusive` and warn that old conversations may reappear from cloud state.
7. Ask whether the device or app is organization-managed. Stop and direct the user to IT for required assignments, non-removable management, protected helpers, or managed permissions.
8. Inventory only literal candidates from the catalog. Record:
   - product, edition, and consumers;
   - exact literal path;
   - existence, type, owner, volume, and symlink status;
   - evidence and confidence label;
   - data-loss category;
   - default, opt-in, protected, discovery-only, or out-of-scope status.
9. Reject overlapping ancestor/descendant selections, symlink roots or parents, cross-volume plans, non-user-owned paths, destination collisions, and arbitrary discovered paths.
10. Show the exact proposed scope and exclusions. State that no changes were made.

For a full known-local-state scope, include every verified non-protected default and explicit-opt-in candidate for the selected products. A clean-conversation scope must propose every verified local conversation, transcript, and session candidate consumed by the selected products. Ask separately before shared roots and name every other consumer. If the user excludes a known eligible candidate, retain the exclusion, warn that listed local conversations may remain or reappear, and plan a `partial` result.

### Diagnostic orientation

Before a state reset, offer these lower-loss tests:

1. Reproduce the same symptom with extensions disabled.
2. Use a disposable user-data/profile root where the product supports it.
3. Reproduce the same workload, workspace, version, architecture, and sync state.

Creating disposable state does not alter the existing profile, but it is not literally write-free. Do not use Cursor's `Clear Editor History` without separate consent: Cursor documents it as cached-state cleanup but does not document its deletion scope.

## 2. Reset

`reset` is an operational local-state reset, not “cache cleanup.” Selected roots may contain settings, extension state, unsaved-work backups, local history, conversations, transcripts, tokens, and personal data.

The normal reset scope contains:

- each selected desktop profile;
- exact verified product cache, HTTP-storage, and log roots;
- separately acknowledged extension, shared, and local-agent roots.

Shared or mixed roots remain opt-in, but omitting a verified eligible root makes the result `partial`.

### Required gates

1. Require a prior audit, then repeat the audit in this invocation.
2. Require the user to quit every selected app manually.
3. Recheck the app, helpers, exact source paths, destinations, ownership, volume, overlap, and sync/management unknowns.
4. Read the receipt contract and prepare a private receipt outside every target.
5. Display every source-to-backup mapping and its loss category.
6. Record archive retention as `keep-until-user-deletes` and restore scope as `pending`. Archives are never deleted automatically and never restored without a later explicit choice.
7. Ask:

> This will move the listed active local-state roots to unique sibling archives. It will not delete them. It will hide the listed local settings, extensions, unsaved-work backups, local history, and agent conversations from the clean profile. Excluded, shared, synced, cloud, or undocumented conversations may remain or reappear. The archives will remain inactive until you later choose reference-only retention, selective configuration recovery, or full-profile rollback. It will not touch projects, worktrees, cloud data, Keychain, MDM, or app bundles. Type `RESET CURSOR`, `RESET VSCODE`, or `RESET BOTH` exactly.

Anything else cancels. Confirmation from an earlier turn or invocation does not count.

### Manual execution and verification

1. Persist the planned receipt before the first move.
2. For each disjoint top-level root:
   - mark it `moving`;
   - show the exact source and unique sibling backup name;
   - ask the user to use Finder's **Go to Folder** and rename the source manually without moving it to another parent or volume;
   - wait for the user to report the Finder result;
   - verify the source is absent and the sibling backup is present;
   - mark it `moved`.
3. Stop on the first error. Never compensate automatically.
4. If any move occurred before failure, report `partial`; if the outcome is uncertain, mark the item `unknown`.
5. Finish with the receipt location, exact mappings, exclusions, archive-retention policy, and manual test instructions.
6. Stop. Do not escalate, restore, uninstall, sign in, enable sync, or reinstall in this invocation.

## 3. Record the manual test

On a new explicit invocation:

1. Read and validate the receipt.
2. Ask the user whether the same reproduction was `passed`, `failed`, or `inconclusive`.
3. Record only a short structured result, product version, architecture, workspace class, sync state, and timestamp. Do not store verbatim sensitive text.
4. State that the result does not prove a cause.

Never automatically escalate from `failed` or `inconclusive`.

## 4. Restore

Old profile state can reintroduce the original defect. Require a valid receipt, a recorded clean-state test, and a fresh user choice:

1. **Reference-only archive (recommended)** — keep every archive inactive. Record `reference-only`; make no target change and do not offer full-profile rollback later for this receipt.
2. **Selective configuration recovery** — keep the archived profile inactive and record `selective-config`. Guide the user to inspect only locally verified, user-authored settings, keybindings, and snippets and manually recreate the chosen values in the clean profile. Never copy or restore profile databases, `workspaceStorage`, `globalStorage`, History, Backups, conversations, transcripts, session state, extension payloads, or extension-owned storage. Do not print configuration contents because settings may contain secrets.
3. **Full-profile rollback** — record `full-profile` only after warning that conversations, databases, extension state, and the suspected defect may all return. This is the only choice that permits whole-root restoration.

Persist the choice before any target change and never broaden it in a later invocation. All archives use `keep-until-user-deletes`; this skill never deletes them.

For a full-profile rollback only:

1. Repeat the host, quit, identity, collision, and path checks.
2. Preview every reverse mapping and require `RESTORE FULL PROFILE <receipt-id>` exactly.
3. If the app created a new active root, ask the user to preserve it as a separate `active-generated` sibling after a second preview; never merge it into the original archive.
4. Ask the user to restore only an `original-backup` recorded by the receipt through a manual Finder same-parent rename.
5. Stop on drift, collision, missing archive, unknown state, permission failure, or identity mismatch.
6. Verify and record each outcome. Partial work remains `partial`.

## 5. Uninstall

Use a new explicit invocation. Require a recorded failed/inconclusive reset or ask the user to explicitly override that sequencing.

1. Repeat the full audit and loss preview, including every verified local conversation/session candidate in the proposed scope.
2. Require the user to quit the selected app and helpers manually.
3. Select and preview the removal route: a locally verified current edition-specific vendor uninstaller whose expected user-data effect is `none`; manual Finder removal of the verified app bundle when current vendor guidance permits it; or one exact plain package-manager uninstall command for a provenance-verified package. A vendor uninstaller that removes listed state, could consume planned archive destinations, or has unknown effects is blocked; use a verified Finder route instead when vendor guidance permits it. Never use zap or force flags.
4. Read the receipt contract. Before any target change, prepare an uninstall receipt containing the removal route, route-specific read-only verification checks, expected user-data effects, app-removal state, every planned archive mapping, archive retention `keep-until-user-deletes`, restore scope `pending`, and the exact eligible exclusions.
5. For Cursor, never target the whole `$HOME/.cursor` root. Review documented child roots separately. Treat shared VS Code/Copilot state as opt-in and name every consumer. Leave shell profile lines and Keychain items untouched by default.
6. Use this confirmation and persist its event before entering `running`:

> This will remove the listed app bundles through the previewed native route, then move the listed known user-local active paths to reversible inactive archives. The listed old local conversations and profile databases will not enter the clean reinstall unless you later choose full-profile rollback. Excluded, shared, synced, cloud, or undocumented conversations may remain or reappear. Archives, Trash, Keychain, cloud data, MDM, projects, worktrees, and undocumented state will remain. Type `UNINSTALL CURSOR`, `UNINSTALL VSCODE`, or `UNINSTALL BOTH` exactly.

7. Persist the app-removal record as `removing`, then ask the user to perform the previewed removal route.
8. Apply the receipt's route-specific read-only checks and record `removed`, `failed`, or `unknown` before continuing.
9. Re-audit the residual known-local-state candidates. If the actual eligible scope differs from the confirmed receipt, preview the amendment and require the same uninstall token again before adding or changing mappings.
10. Guide only receipt-backed manual Finder same-parent renames, verifying each result before continuing.
11. Verify selected app bundles are absent, every eligible known active root in scope is absent, archives are present, and known command links are either valid or reported as leftovers.
12. Report event execution status, immutable origin scope result, and current state separately. Stop before reinstall, restore choice, or permanent deletion.

## Handoff

Always report:

- mode, products, editions, and receipt ID;
- exact selected categories and exclusions;
- every completed, failed, unknown, or blocked mapping;
- event execution status, origin scope result, and current state;
- archive retention and restore scope (`pending`, `reference-only`, `selective-config`, or `full-profile`);
- sync, MDM, updater-registration, shared-state, and permission unknowns;
- whether app removal was manually verified;
- next safe action: manual test, restore, manual app removal, contact IT, or manual reinstall.

Do not claim that a reinstall will fix lag. Extension behavior, indexing, Git integration, workspace size, runtime regressions, architecture, network/MCP processes, and operating-system behavior can survive or independently cause the symptom.
