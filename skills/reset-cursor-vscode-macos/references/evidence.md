# Evidence and limitations

Research cutoff: 2026-08-22.

Status: research covered official/primary, user-experience, and independent-expert lanes. Citation integrity is `partial`: action-driving sources were fetched, but some Cursor internals remain undocumented or version-sensitive.

## Decision summary

The evidence supports:

1. diagnosing extensions and a disposable profile before destructive state changes;
2. treating settings, workspace/global databases, History, backups, and conversations as user data rather than disposable cache;
3. using reversible whole-root, same-parent renames after the apps are stopped;
4. requiring a separate invocation and receipt for restore or uninstall;
5. using a verified native removal route before residual-state cleanup and rejecting uninstallers that could remove selected state or consume planned archives;
6. keeping old profile archives inactive by default and recovering only user-selected configuration rather than databases or conversation state;
7. defining full-scope uninstall success as every verified eligible known user-local active path cleared, with any omission reported as `partial`, not forensic erasure.

No source supports a universal broad deletion command for current Cursor and VS Code on macOS.

## Official and primary evidence

### VS Code clean-uninstall roots

Microsoft's current macOS clean-uninstall documentation names:

- `$HOME/Library/Application Support/Code`
- `$HOME/.vscode-shared`
- `$HOME/.vscode`

Source: [Uninstall Visual Studio Code](https://code.visualstudio.com/docs/setup/uninstall), Microsoft, updated 2026-08-19.

Limit: this is the supported stable baseline, not an inventory of every extension-owned external file, Keychain item, custom root, cloud session, or macOS artifact.

### VS Code state is broader than settings

Pinned VS Code 1.134 source places profiles, global/workspace storage, History, Backups, downloaded extensions, shared storage, local agent sessions, plugins, and chat-related state under product user-data and shared roots.

Sources:

- [VS Code 1.134 source](https://github.com/microsoft/vscode/tree/474a349ad5b745e512ef86b864d1c74f7264dd7a)
- [Profiles](https://code.visualstudio.com/docs/configure/profiles)
- [Portable mode](https://code.visualstudio.com/docs/setup/portable)
- [Command line](https://code.visualstudio.com/docs/configure/command-line)

Limit: Microsoft's branded product values are injected during packaging; Code OSS names differ. Custom roots and portable mode replace or expand defaults.

### Sync and cloud state are separate

VS Code Settings Sync can restore settings, extensions, profiles, and UI state. Current Copilot documentation says Session Sync is enabled by default; Copilot Session Sync and cloud-agent sessions have separate local/cloud deletion controls.

Sources:

- [Settings Sync](https://code.visualstudio.com/docs/configure/settings-sync)
- [Session Sync](https://code.visualstudio.com/docs/agents/sessions/session-sync)

Limit: local deletion cannot establish cloud deletion. A clean local conversation test is inconclusive unless relevant sync is paused or the user signs out, because cloud state may immediately repopulate the local profile.

### Copilot state is shared and mixed

GitHub documents `$HOME/.copilot` as a mixed configuration directory containing session history, logs, plugins, MCP fallback state, permissions, and other customizations. OAuth credentials normally use the operating-system Keychain.

Sources:

- [Copilot CLI configuration directory](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-config-dir-reference)
- [Authenticate Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli/set-up-copilot-cli/authenticate-copilot-cli)

Consequence: never quarantine the whole root automatically. Session children require a shared-consumer warning; credential and MCP-secret children remain protected.

### Cursor has no complete official uninstall manifest

Cursor officially recommends disabling extensions for conflicts, offers `Clear Editor History`, and documents moving the app to Trash for reinstall. It does not document the deletion scope of Clear Editor History or publish a complete macOS desktop storage/uninstall inventory.

Sources:

- [Extension conflicts](https://cursor.com/help/troubleshooting/extensions)
- [Performance troubleshooting](https://cursor.com/help/troubleshooting/performance)
- [Installation and startup](https://cursor.com/help/troubleshooting/install-issues)

Limit: official wording calls some data “cached state” without saying whether chats, prompt history, checkpoints, or other user data are included.

### Cursor product and channel identities

Current Cursor deployment documentation names:

- production bundle: `com.todesktop.230313mzl4w4u92`
- standalone Nightly bundle: `co.anysphere.cursor.nightly`

Source: [Cursor deployment patterns](https://cursor.com/docs/enterprise/deployment-patterns).

Limit: update-channel labels and profile paths can drift. Read the installed app bundle.

### Cursor CLI and user content share `$HOME/.cursor`

Cursor documents global CLI configuration, skills, worktrees, MCP, hooks, and SDK authentication under separate `$HOME/.cursor` children. Current CLI packages also use local chat and ACP session stores in some builds.

Sources:

- [CLI configuration](https://cursor.com/docs/cli/reference/configuration)
- [CLI installation](https://cursor.com/docs/cli/installation)
- [Skills](https://cursor.com/docs/skills)
- [Worktrees](https://cursor.com/docs/configuration/worktrees)
- [MCP](https://cursor.com/docs/mcp)
- [Hooks](https://cursor.com/docs/hooks)
- [Cursor SDK](https://cursor.com/docs/sdk/typescript)

Limit: no maintained source defines every child or a stable desktop/CLI conversation schema. The mixed root must never be deleted wholesale.

### SQLite backup boundary

In WAL mode, the WAL is part of database state; copying the main file alone can lose committed transactions or corrupt the copy. SQLite's Online Backup API produces a consistent snapshot.

Sources:

- [Write-Ahead Logging](https://www.sqlite.org/wal.html)
- [SQLite Online Backup API](https://sqlite.org/backup.html)

Consequence: this skill moves a fully stopped top-level profile as one unit. It does not edit or copy individual Cursor/VS Code databases.

### macOS and Homebrew boundaries

Apple separates app removal from user data and warns that emptying Trash is permanent. Homebrew documents that `zap` is non-default and may remove shared resources.

Sources:

- [Delete or uninstall apps on Mac](https://support.apple.com/en-us/102610)
- [Delete files and folders on Mac](https://support.apple.com/guide/mac-help/delete-files-and-folders-on-mac-mchlp1093/mac)
- [Homebrew Cask Cookbook](https://docs.brew.sh/Cask-Cookbook)

Current Homebrew Cursor cask patterns include broad `com.todesktop.*` candidates that can match other ToDesktop apps. Current VS Code casks omit Microsoft's documented shared root. Casks are useful candidate manifests, not complete ownership proof.

### Agent Skills compatibility

Claude Code and Cursor both document `SKILL.md`, relative supporting files, direct invocation, and `disable-model-invocation: true`.

Sources:

- [Claude Code skills](https://code.claude.com/docs/en/skills)
- [Cursor skills](https://cursor.com/docs/skills)
- [Agent Skills specification](https://agentskills.io/specification)

Limit: `disable-model-invocation` is a Claude/Cursor extension outside the strict six-field Agent Skills standard. It prevents automatic loading; it does not enforce shell safety or authorization.

## User-experience patterns

These sources are selected incident reports. They establish possible outcomes and failure modes, not prevalence.

### App-only reinstall can preserve the failure

Users and Cursor staff distinguish deleting the app bundle from deleting the profile. Reports show app-only reinstall can preserve problematic local state, while full state reset sometimes helps and sometimes does not.

Representative sources:

- [Cursor slow after hours of use](https://forum.cursor.com/t/cursor-becomes-ridiculously-slow-after-a-few-hours-of-usage/148505)
- [Cursor full reinstall still fails](https://forum.cursor.com/t/unexpected-error-occurred-on-all-agent-chats-new-old-after-full-reinstall-persists-across-cache-clear/164868)
- [VS Code reinstall retains settings](https://stackoverflow.com/questions/42603103/how-to-completely-uninstall-vs-code-on-mac)

### Whole-profile quarantine can isolate the problem

One macOS Cursor report confirmed a clean launch after renaming the profile and selectively restored workspace state. Another confirmed that restoring old global/workspace state reintroduced the loading failure.

Sources:

- [Cursor profile quarantine worked](https://forum.cursor.com/t/cursor-is-not-usable-after-the-last-update/150165/25)
- [Restored profile reintroduced failure](https://forum.cursor.com/t/cursor-wont-load/158137)

This is why archives should remain inactive by default, selective recovery must exclude databases and conversation state, and full-profile rollback must preserve newly generated state and warn that the defect may return.

### Databases and conversations are not disposable cache

Mac reports confirm that deleting global `state.vscdb` can strand chats and restoring the original can recover loading. Other reports show titles without bodies or surviving transcripts without a supported import path.

Sources:

- [Deleting global state breaks chat loading](https://forum.cursor.com/t/deleting-global-state-vscdb-causes-infinite-loading-chat-in-projects-history-not-recoverable-without-corrupted-backup/153220)
- [Large database restore produced empty bodies](https://forum.cursor.com/t/unable-to-restore-conversations-from-original-37-gb-state-vscdb-database-request-for-assistance/165794)
- [Update wiped agent chat history](https://forum.cursor.com/t/update-wiped-agent-chat-history-cursordiskkv-agents-window-empty-restore-crashes/168900)

### Lag has competing causes

Reports attribute similar symptoms to extensions, indexing, Git integration, workspace size, helper processes, architecture, and release regressions. Reset success does not prove cache causality.

Representative sources:

- [VS Code Performance Issues](https://github.com/microsoft/vscode/wiki/Performance-Issues)
- [Cursor workspace loading issue](https://forum.cursor.com/t/cursor-is-not-loading-on-both-of-my-macs-keeps-infinitely-loading/159125)
- [VS Code macOS lag persisted after reinstall](https://github.com/microsoft/vscode/issues/241057)

### Updaters, links, and management are separate

ShipIt state can outlive the app lifecycle, command links can remain stale, MDM can reinstall required apps, and macOS App Management can block changes even for root.

Sources:

- [Cursor relaunches after quit](https://forum.cursor.com/t/cursor-reopens-restarts-shortly-after-i-quit-or-close-windows-macos/167044/1)
- [VS Code App Translocation left a broken link](https://github.com/microsoft/vscode/issues/209356)
- [Homebrew App Management check](https://github.com/Homebrew/brew/pull/22967)
- [Apple managed apps](https://support.apple.com/guide/deployment/distribute-managed-apps-dep575bfed86/web)

## Independent expert and practitioner evidence

### Prefer precision and reversibility

Independent macOS administration and uninstaller analyses favor exact attribution, preview, confirmation, and reversible moves over broad path matching.

Sources:

- [Inspecting Packages](https://scriptingosx.com/2025/07/inspecting-packages/), Armin Briegel
- [Sticky preferences](https://eclecticlight.co/2017/07/06/sticky-preferences-why-trashing-or-editing-them-may-not-change-anything/), Howard Oakley
- [Mole uninstaller implementation](https://github.com/tw93/Mole/blob/3d6193fb/lib/uninstall/batch.sh)

Limit: uninstall tools and guides have incentives to appear comprehensive. Their path lists are candidate generators, not app-vendor manifests.

### Modern macOS persistence is not a static plist list

Ventura and later Background Task Management/SMAppService and macOS 15+ saved-state changes make historical path lists incomplete. Detection does not establish safe removal.

Sources:

- [Diagnose login and background items](https://eclecticlight.co/2023/07/04/how-to-diagnose-and-control-login-and-background-items/), Howard Oakley
- [Saved Application State](https://mothersruin.com/software/Archaeology/reverse/appstate.html), Mother's Ruin Software
- [KnockKnock](https://objective-see.org/products/knockknock.html), Objective-See

Consequence: report uncertain registrations and containers; never delete shared BTM or daemon-container databases.

### Same-parent rename is the smallest credible rollback

POSIX and Apple filesystem behavior support same-filesystem directory rename as an atomic namespace operation. Multiple renames are not one transaction, and cross-volume `mv` may become copy-and-delete.

Sources:

- [POSIX rename](https://pubs.opengroup.org/onlinepubs/9799919799.2024edition/functions/rename.html)
- [Apple file management](https://developer.apple.com/library/archive/documentation/FileManagement/Conceptual/FileSystemProgrammingGuide/ManagingFIlesandDirectories/ManagingFIlesandDirectories.html)

Consequence: use disjoint top-level sibling moves, stop on collision or partial failure, and keep an honest receipt.

## Coverage and residual gaps

- Official/primary: covered.
- GitHub: covered.
- Cursor Community Forum: covered.
- Reddit: direct access blocked or no usable fetched results.
- Facebook: partially tested; no decision-relevant evidence.
- Google Reviews: tested; no relevant product evidence.
- Named independent practitioners: covered.

Residual gaps:

- no exhaustive current Cursor desktop artifact manifest;
- contested and version-sensitive Cursor conversation storage;
- no portable proof that a session is standalone rather than IDE-hosted;
- Claude Code runtime unavailable in the repository's recorded compatibility environment;
- no complete inventory of arbitrary extension-owned external state;
- modern saved-state and BTM association remain partly undocumented;
- cloud, Keychain, MDM, backups, and secure erasure are separate scopes.
