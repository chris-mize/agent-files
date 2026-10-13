# macOS path catalog

Research cutoff: 2026-08-22.

This is a candidate catalog, not an ownership manifest. Cursor does not publish a complete macOS storage or uninstall manifest. Verify the installed product, edition, bundle identifier, consumers, ownership, and exact literal before using any path.

## Confidence labels

- `official-current` — current vendor documentation directly names the path or behavior.
- `primary-source-current` — current product source, package metadata, or bundle metadata establishes it.
- `version-sensitive` — current support, implementation, or user evidence establishes it for some releases.
- `discovery-only` — inspect if present; never mutate from this catalog alone.
- `protected` — user-authored, shared, credential, project, worktree, managed, or otherwise excluded by default.
- `out-of-scope` — never mutate in this skill.

Globs below describe candidate families only. Expand them for read-only review, then accept only individually verified literal paths.

## Selection classes

- `default reset` — top-level user profile for the selected desktop product.
- `explicit opt-in` — extensions, shared state, CLI/agent state, or other separately consumed data.
- `uninstall candidate` — review only during `uninstall`.
- `audit only` — inspect and report; do not mutate.

Reject any selected set containing both an ancestor and its descendant.

## Cursor

### Product identity

| Edition | App candidate | Bundle identifier | Label |
|---|---|---|---|
| Stable | `/Applications/Cursor.app` or `$HOME/Applications/Cursor.app` | `com.todesktop.230313mzl4w4u92` | `official-current` |
| Standalone Nightly | `/Applications/Cursor Nightly.app` or `$HOME/Applications/Cursor Nightly.app` | `co.anysphere.cursor.nightly` | `official-current` for identity; profile path is `version-sensitive` |

An Early Access or Nightly update channel inside the stable app may retain the stable bundle and profile identity. Read the installed bundle; do not infer the edition from an update setting.

### Desktop and agent state

| Candidate | Contents / consumers | Selection | Label |
|---|---|---|---|
| `$HOME/Library/Application Support/Cursor` | Desktop settings, keybindings, profiles, extension state, caches, logs, backups, History, global/workspace storage, and local conversations depending on version | `default reset` | `primary-source-current`; conversation schema `version-sensitive` |
| `$HOME/Library/Application Support/Cursor Nightly` | Standalone Nightly desktop profile | `default reset` only after installed-bundle verification | `version-sensitive` |
| `$HOME/.cursor/extensions` | Cursor desktop extension payloads | `explicit opt-in` | `primary-source-current` |
| `$HOME/.cursor/chats` | Cursor Agent CLI local chats in some current builds | `explicit opt-in` | `version-sensitive` |
| `$HOME/.cursor/acp-sessions` | ACP session databases and metadata | `explicit opt-in` | `version-sensitive` |
| `$HOME/.cursor/projects` | Project-indexed transcripts and agent state; may contain valuable conversation records | `explicit opt-in` | `version-sensitive` |
| `$HOME/.cursor/cli-config.json` | Global Cursor Agent CLI configuration | `explicit opt-in` | `official-current` |
| Exact user-supplied `CURSOR_CONFIG_DIR` | Relocated Cursor Agent configuration and version-specific mixed state | classify child paths individually; never select the root wholesale | `official-current`, conditional |
| `$HOME/.cursor/sdk/auth.json` | SDK authentication | `protected` | `official-current` |
| `$HOME/.cursor/mcp.json` | Global MCP configuration | `protected` | `official-current` |
| `$HOME/.cursor/hooks.json` | User hooks | `protected` | `official-current` |
| `$HOME/.cursor/skills` | User skills | `protected` | `official-current` |
| `$HOME/.cursor/skills-cursor` | Cursor-managed skill resources | `protected` | `official-current` |
| `$HOME/.cursor/worktrees` | Full Git worktrees, possibly with uncommitted work | `out-of-scope` | `official-current` |
| Other children of `$HOME/.cursor` | Unknown, shared, user-authored, or version-specific state | `protected` until independently classified | `discovery-only` |

Never select the whole `$HOME/.cursor` root.

For a clean-conversation scope, propose each verified `$HOME/.cursor/chats`, `acp-sessions`, and `projects` candidate consumed by the selected Cursor surfaces. Name desktop, CLI, and other consumers before confirmation. These remain separate opt-ins because they are shared or version-sensitive; declining one makes the clean-conversation result `partial`.

The desktop profile can contain SQLite databases named `state.vscdb` plus WAL/SHM sidecars. Treat the whole selected top-level profile as one unit after every owner process is stopped. Do not edit, compact, checkpoint, or copy individual databases in this skill.

### Cursor app and updater candidates

For Stable, the literal bundle-derived candidates below are current primary-source evidence. For Nightly or another verified Cursor edition, substitute its exact installed bundle identifier only for read-only discovery; each resulting literal remains `discovery-only` until local existence, ownership, and product association are verified.

| Candidate | Selection | Label |
|---|---|---|
| Exact verified app bundle | Manual Finder removal during `uninstall` | `official-current` |
| `$HOME/Library/Caches/com.todesktop.230313mzl4w4u92` | `explicit opt-in` reset and `uninstall candidate` | `primary-source-current` |
| `$HOME/Library/Caches/com.todesktop.230313mzl4w4u92.ShipIt` | `explicit opt-in` reset and `uninstall candidate`; registration state remains separate | `primary-source-current` |
| `$HOME/Library/HTTPStorages/com.todesktop.230313mzl4w4u92` | `explicit opt-in` reset and `uninstall candidate` | `primary-source-current` |
| `$HOME/Library/Preferences/com.todesktop.230313mzl4w4u92.plist` | `uninstall candidate` | `primary-source-current` |
| Exact ByHost preference containing the verified stable bundle ID | `uninstall candidate` | `version-sensitive` |
| `$HOME/Library/Logs/Cursor` | `explicit opt-in` reset and `uninstall candidate` if present and verified | `version-sensitive` |
| `$HOME/Library/Caches/<verified-cursor-bundle-id>` | edition-specific read-only discovery; eligible only after literal verification | Stable `primary-source-current`; other editions `discovery-only` |
| `$HOME/Library/Caches/<verified-cursor-bundle-id>.ShipIt` | edition-specific read-only discovery; registration state remains separate | Stable `primary-source-current`; other editions `discovery-only` |
| `$HOME/Library/HTTPStorages/<verified-cursor-bundle-id>` | edition-specific read-only discovery | Stable `primary-source-current`; other editions `discovery-only` |
| `$HOME/Library/Preferences/<verified-cursor-bundle-id>.plist` | edition-specific uninstall discovery; never part of the normal reset | Stable `primary-source-current`; other editions `discovery-only` |
| Edition-specific product logs, such as `Cursor Nightly` | read-only discovery, then explicit reset opt-in if verified | `discovery-only` |
| Cursor-specific Saved Application State path | `audit only` on current macOS | `discovery-only` |
| `$HOME/Library/Application Support/Caches/cursor-updater` | historical updater candidate | `discovery-only` |
| Any `com.todesktop.*`, `co.anysphere.*`, or `com.cursor*` pattern | read-only discovery only | automatic mutation rejected |

Do not remove a ShipIt or updater directory while the app or updater is active. File absence does not prove an updater job or Background Task Management registration is gone.

### Cursor Agent CLI candidates

| Candidate | Selection | Label |
|---|---|---|
| `$HOME/.local/share/cursor-agent/versions` | `explicit opt-in` during full CLI removal | `official-current` |
| `$HOME/.local/bin/agent` | remove only if it is a symlink whose exact target is inside the verified Cursor Agent installation | `official-current` |
| `$HOME/.local/bin/cursor-agent` | same rule as `agent` | `official-current` |
| Other `cursor` command links | `audit only` until exact target and installer ownership are proven | `version-sensitive` |
| Shell integration in `$HOME/.zshrc` | manual review only; never rewrite the whole file | `official-current` |

Desktop Cursor and Cursor Agent CLI share parts of `$HOME/.cursor`. Removing the desktop app does not authorize CLI-state removal.

## Visual Studio Code

### Product identity and primary roots

| Edition | App candidate | Bundle identifier | User roots | Label |
|---|---|---|---|---|
| Stable | `/Applications/Visual Studio Code.app` or `$HOME/Applications/Visual Studio Code.app` | `com.microsoft.VSCode` | `$HOME/Library/Application Support/Code`, `$HOME/.vscode`, `$HOME/.vscode-shared` | `official-current` |
| Insiders | `/Applications/Visual Studio Code - Insiders.app` or user Applications equivalent | `com.microsoft.VSCodeInsiders` | `$HOME/Library/Application Support/Code - Insiders`, `$HOME/.vscode-insiders`, `$HOME/.vscode-insiders-shared` | app/profile/extensions `official-current`; shared root `primary-source-current` |

Selection:

- The edition's Application Support root is `default reset`.
- Its extension root and shared root are separate `explicit opt-in` roots.
- Stable and Insiders are separate editions. Audit and preview each independently.

The Application Support root can contain:

- settings, profiles, global/workspace extension state, and `state.vscdb`;
- local History and unsaved-work Backups;
- downloaded extension packages and cached profile data;
- local chat sessions, agent session databases, plugins, and memory depending on the installed release and extensions.

Moving it can hide or remove access to all of those categories.

### Copilot CLI and agent state

| Candidate | Contents / consumers | Selection | Label |
|---|---|---|---|
| `$HOME/.copilot/session-state` | Copilot CLI local session events and workspace metadata shared across VS Code editions and other Copilot surfaces | `explicit opt-in`, shared-state warning required | `official-current` |
| `$HOME/.copilot/session-store.db` | Copilot CLI session index | `explicit opt-in`, shared-state warning required | `official-current` |
| `$HOME/.copilot/vscode.session.metadata.cache.json` | VS Code/Copilot session metadata cache | `explicit opt-in`, shared-state warning required | `primary-source-current` |
| `$HOME/.copilot/plugin-data` | Plugin-owned state | `protected` unless exact plugin ownership and loss are separately accepted | `official-current` |
| `$HOME/.copilot/installed-plugins` | User-installed Copilot plugins | `protected` | `official-current` |
| `$HOME/.copilot/mcp-oauth-config` | MCP OAuth configuration | `protected` | `official-current` |
| `$HOME/.copilot/mcp-secrets` | MCP secrets | `out-of-scope` | `official-current` |
| Other children of `$HOME/.copilot` | Configuration, permissions, logs, credentials, or version-specific shared state | `protected` until independently classified | `discovery-only` |
| `$HOME/Library/Caches/copilot` | Copilot cache if present | `uninstall candidate` | `version-sensitive` |
| Custom `COPILOT_HOME` or `COPILOT_CACHE_HOME` | Relocated shared state | exact user-supplied path only | `official-current`, conditional |

Do not assume VS Code Settings Sync or Copilot Session Sync data is local. Local reset never authorizes cloud deletion.

For a clean-conversation scope, propose every verified local session candidate consumed by the selected VS Code/Copilot surfaces, including the three session entries above. Keep the shared-state warning and separate confirmation. Require relevant session sync to be paused or the user signed out for the clean test; otherwise report `inconclusive`.

### Portable and custom roots

| Mechanism | Candidate | Selection | Label |
|---|---|---|---|
| Stable portable mode | `code-portable-data` beside the app bundle | exact verified root | `official-current` |
| Insiders portable mode | `code-insiders-portable-data` beside the app bundle | exact verified root | `official-current` |
| `VSCODE_APPDATA` or `--user-data-dir` | custom user-data root | exact user-supplied and locally verified root | `official-current`, conditional |
| `VSCODE_EXTENSIONS` or `--extensions-dir` | custom extension root | exact user-supplied and locally verified root | `official-current`, conditional |
| `--shared-data-dir` | custom shared-data root | exact user-supplied and locally verified root | `primary-source-current`, conditional |
| `VSCODE_CLI_DATA_DIR` or `--cli-data-dir` | CLI metadata root | `audit only` unless explicitly selected | `primary-source-current`, conditional |

Never mutate a custom path learned only from process arguments. Ask the user to supply and confirm the literal, then verify it.

### VS Code app and updater candidates

Substitute the exact verified bundle identifier for the installed edition:

- `$HOME/Library/Caches/<bundle-id>` — `explicit opt-in` reset and uninstall candidate
- `$HOME/Library/Caches/<bundle-id>.ShipIt` — `explicit opt-in` reset and uninstall candidate; registration remains separate
- `$HOME/Library/HTTPStorages/<bundle-id>` — `explicit opt-in` reset and uninstall candidate
- `$HOME/Library/Preferences/<bundle-id>.plist`
- exact ByHost ShipIt preferences
- product-specific logs — `explicit opt-in` reset and uninstall candidate
- legacy Saved Application State paths

These are `version-sensitive` or `discovery-only` candidates. Preferences and saved state remain uninstall-only. Current macOS may retain saved application state in daemon-managed containers; do not delete shared daemon containers.

The `code` and `code-insiders` commands are launch links, not state roots. Remove or report one only after its exact symlink target and installer ownership are verified.

## Selective configuration recovery

Selective recovery is not a whole-profile restore. Keep the archived desktop profile inactive and inspect only locally verified, user-authored configuration:

| Relative candidate inside an archived desktop profile | Recovery rule | Label |
|---|---|---|
| `User/settings.json` | Manually review and recreate only chosen settings in the clean profile | VS Code `official-current`; Cursor `version-sensitive` |
| `User/keybindings.json` | Manually review and recreate only chosen keybindings | VS Code `official-current`; Cursor `version-sensitive` |
| `User/snippets/` | Manually review and recreate only chosen user snippets | VS Code `official-current`; Cursor `version-sensitive` |
| Verified profile-specific settings, keybindings, or snippets under `User/profiles/` | Same rule; never select an unknown profile subtree wholesale | VS Code `primary-source-current`; Cursor `version-sensitive` |

Do not print configuration contents because settings and snippets may contain secrets or private text. Never selectively recover `state.vscdb`, SQLite sidecars, `workspaceStorage`, `globalStorage`, History, Backups, conversations, transcripts, sessions, extension payloads, or extension-owned storage. Reinstall extensions separately only after the clean-state test.

## Always audit only or exclude

- LaunchAgents, LaunchDaemons, Login Items, BTM/SMAppService records, privileged helpers, and system extensions: audit/report only; contact IT or use vendor guidance.
- Keychain and Passwords: out of scope.
- Project `.cursor`, `.vscode`, `.code-workspace`, `.github/copilot`, and source trees: out of scope.
- Git worktrees recorded by Cursor, Copilot, or Git: out of scope.
- Remote `.vscode-server*`, SSH-configured server roots, containers, cloud workspaces, and remote volumes: out of scope.
- MDM profiles, managed preferences, required app assignments, and organization policies: out of scope.
- APFS snapshots, Time Machine, cloud sync, cloud conversations, shared transcripts, and account deletion: out of scope.
- Arbitrary extension-owned files outside verified product roots: discovery-only and protected.
