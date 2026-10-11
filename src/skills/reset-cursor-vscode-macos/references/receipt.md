# Reset receipt contract

The receipt is a private recovery record, not a transaction guarantee. It supports separate invocations and honest partial-state reporting.

## Location and permissions

Resolve the state root in this order:

1. `$XDG_STATE_HOME/reset-cursor-vscode-macos`, if `XDG_STATE_HOME` is an absolute local path outside every target.
2. `$HOME/.local/state/reset-cursor-vscode-macos`.

Create the skill directory with mode `0700` and receipts with mode `0600`. Refuse:

- a symlinked state root or parent;
- a state root inside, above, or below any target;
- a state root inside the current workspace, repository, or any Git worktree;
- a non-user-owned root;
- a network, cloud-placeholder, or unsupported volume;
- permissions or ACLs that cannot be verified.

The receipt is sensitive. It contains local paths and may reveal project or account context. Never print it in full.

## File layout

```text
reset-cursor-vscode-macos/
└── receipts/
    └── <receipt-id>.json
```

Use an opaque, collision-resistant receipt ID. Do not derive it from a username, project, or path.

## Minimum schema

```json
{
  "schema_version": 2,
  "receipt_id": "opaque-id",
  "origin_mode": "reset",
  "created_at": "RFC-3339 timestamp",
  "updated_at": "RFC-3339 timestamp",
  "host": "standalone-claude-code",
  "products": [
    {
      "product": "cursor",
      "edition": "stable",
      "bundle_id": "verified bundle identifier"
    }
  ],
  "origin_scope_result": "pending",
  "current_state": "unchanged",
  "archive_policy": {
    "retention": "keep-until-user-deletes",
    "restore_scope": "pending",
    "selected_at": null
  },
  "app_removals": [],
  "events": [
    {
      "id": "opaque-event-id",
      "mode": "reset",
      "started_at": "RFC-3339 timestamp",
      "status": "planned",
      "item_ids": ["opaque-item-id"],
      "app_removal_ids": [],
      "confirmation": {
        "token_kind": "RESET",
        "confirmed_at": null
      }
    }
  ],
  "items": [
    {
      "id": "opaque-item-id",
      "category": "desktop-profile",
      "archive_role": "original-backup",
      "consumers": ["cursor-stable"],
      "confidence": "primary-source-current",
      "source": "exact absolute path",
      "destination": "exact same-parent sibling path",
      "source_type": "directory",
      "source_device": "numeric device identifier",
      "source_inode": "numeric inode identifier",
      "source_birthtime": "timestamp when available",
      "backup_device": null,
      "backup_inode": null,
      "state": "planned",
      "error_code": null
    }
  ],
  "exclusions": [
    {
      "category": "project-state",
      "path": "exact absolute path or null when no local path applies",
      "eligibility": "protected",
      "reason_code": "out-of-scope"
    }
  ],
  "unknowns": [],
  "test": {
    "status": "not-run",
    "recorded_at": null,
    "product_version": null,
    "architecture": null,
    "workspace_class": null,
    "sync_state": null
  }
}
```

Do not store:

- file or database contents;
- shell, process, environment, Keychain, or `launchctl` output;
- access tokens, account values, prompts, conversations, or error dumps;
- verbatim user test descriptions.

`archive_policy.restore_scope` must be one of:

- `pending` — no post-test recovery choice has been recorded;
- `reference-only` — archives remain inactive and no receipt item may be restored;
- `selective-config` — archives remain inactive; the user may manually recreate selected user-authored settings, keybindings, or snippets in the clean profile;
- `full-profile` — exact whole-root rollback remains eligible.

The skill must recommend `reference-only`, persist the user's choice before recovery, and never broaden it later. Retention is always `keep-until-user-deletes`: the skill does not delete archives or prompt for routine archive deletion.

Record only bounded error codes such as `collision`, `running`, `permission`, `ownership`, `cross-volume`, `symlink`, `missing`, `drift`, `receipt-write`, or `unknown`.

## States

Operation event status:

- `planned` — preview persisted; no target mutation.
- `running` — at least one item may be changing.
- `complete` — every item and app-removal record governed by the event reached its expected terminal state.
- `partial` — at least one governed item or app-removal record changed and another did not complete.
- `blocked` — no governed item or app-removal record changed.
- `needs-review` — receipt or filesystem evidence cannot establish the outcome.

Origin scope result:

- `pending` — eligible scope has not reached a terminal result.
- `complete` — every verified eligible known path in the requested product scope was cleared and each selected app-removal stage completed.
- `partial` — at least one verified eligible path was excluded or did not clear, or an app-removal stage did not complete.
- `blocked` — no selected target changed.

Event status describes execution of one invocation. `origin_scope_result` immutably describes coverage of the originating reset or uninstall after it reaches a terminal value; later recovery does not rewrite it. `current_state` is one of `unchanged`, `archived`, `selective-config-recovered`, `full-profile-restored`, or `unknown`. Every invocation appends an event containing the exact governed item and app-removal IDs plus its mode and confirmation, and persists it before that invocation enters `running`.

App-removal state:

- `planned`
- `removing`
- `removed`
- `failed`
- `unknown`

Each uninstall app-removal record must include an opaque ID, product/edition, exact bundle path and verified bundle ID, installation provenance, selected removal route, expected user-data effect (`none`, `removes-listed-state`, or `unknown`), state, bounded error code, and verification timestamp. Persist the uninstall event and all planned app-removal records before the user changes the app.

Do not enter `removing` for a vendor-uninstaller record whose expected user-data effect is `removes-listed-state` or `unknown`, or whose deletion scope could include an archive destination. Mark the event `blocked` and use a verified Finder route only when current vendor guidance permits it.

Each exclusion must identify its exact catalog candidate when applicable, eligibility (`eligible`, `protected`, `discovery-only`, or `out-of-scope`), and a bounded reason. An excluded `eligible` candidate forces `origin_scope_result: partial`.

Item state:

- `planned`
- `moving`
- `moved`
- `restoring`
- `restored`
- `failed`
- `unknown`
- `blocked`

Test status:

- `not-run`
- `passed`
- `failed`
- `inconclusive`

Unknown schema versions are read-only failures. Never guess or migrate them during a reset.

## Durable update sequence

For every receipt update:

1. Validate the current receipt and expected item state.
2. Write the complete new JSON to a unique temporary sibling.
3. Set restrictive permissions.
4. Flush the file where the host exposes a supported primitive.
5. Replace the receipt atomically in the same directory.
6. Flush the containing directory where supported.
7. Re-read and validate the receipt.

If any durability or validation step is unavailable or fails, do not claim completion. A receipt failure after a target move makes the operation `partial` or `needs-review`.

This is still not a multi-item transaction. Do not claim crash-proof all-or-nothing behavior.

## Mutation sequence

Before the first target change:

1. Re-audit every item.
2. Preserve every existing item and state. Persist only newly added items or app-removal records as `planned`.
3. Append the current invocation event and its confirmation.
4. Persist that event as `running`.

For each item:

1. Persist `moving`.
2. Present the exact mapping and wait for the user to perform one non-overwriting same-parent Finder rename.
3. Verify source absence, destination presence, and matching device/inode identity.
4. Record the backup device/inode and persist `moved`.

Stop on the first unexpected result. Do not automatically roll back earlier moves.

After the originating reset or uninstall reaches its terminal origin scope result, set `current_state: archived` when at least one selected active-state root is verifiably archived and none has been restored.

On the next invocation, reconcile by the receipt-recorded item state:

- `planned` or `moving`: source present/destination absent means not moved; source absent/destination present means `moved`.
- `moved`: source absent/destination present is expected. Any other arrangement is drift, not “not moved.”
- `restoring`: source present/destination absent means `restored`; source absent/destination present means still `moved`.
- `restored`: source present/destination absent is expected. Any other arrangement is drift.
- A `moved` item with `archive_role: active-generated` may have both paths present after full-profile rollback only when the source identity matches the receipt's restored `original-backup` and the destination identity still matches the generated-state archive. This is expected, not drift.
- Except for the role-aware case above, both paths present, both absent, changed identity, or inaccessible evidence becomes `unknown` or `needs-review` and blocks further mutation.

For app removal, persist `removing` immediately before the user acts. On resume:

- Finder route: exact bundle path absent means `removed`; present means not removed.
- Provenance-verified package-manager route: require both exact bundle absence and read-only confirmation that the recorded package is no longer installed.
- Verified vendor-uninstaller route: require exact bundle absence and every route-specific read-only completion check named in the plan.
- Conflicting, inaccessible, or incomplete evidence becomes `unknown` and blocks further target change.

## Backup names

Use a unique sibling name derived from the source basename plus the opaque receipt and item IDs. The name must not contain user text.

Example shape:

```text
<original-name>.reset-backup.<receipt-id>.<item-id>
```

Never silently add another suffix after a collision. A collision is `blocked`.

## Restore

Before restore:

1. Require a recorded clean-state test.
2. If restore scope is `pending`, ask the user to choose `reference-only`, `selective-config`, or `full-profile`, then persist that choice before continuing.
3. If scope is `reference-only`, retain `current_state: archived`, report the archive locations, and stop without target mutation.
4. If scope is `selective-config`, keep every whole-root archive in `moved` state. The user may manually recreate only locally verified user-authored settings, keybindings, and snippets in the clean profile. Do not copy profile databases, storage directories, History, Backups, conversations, transcripts, sessions, extensions, or extension-owned state. The receipt may record bounded path categories but never file contents. On completion, set `current_state: selective-config-recovered`.
5. If scope is `full-profile`, require the app and helpers to be stopped.
6. Verify the receipt-recorded backup still matches its recorded type, device, inode, and birth time when available.
7. Refuse a missing, changed, symlinked, cross-volume, or non-user-owned backup.
8. If the original active path was recreated, classify it as `active-generated`.
9. Preview a separate receipt item with `archive_role: active-generated`, a new sibling destination, and require confirmation before moving it.
10. Never merge or overwrite.
11. Mark the `original-backup` item `restoring`, then restore only its exact reverse mapping after `RESTORE FULL PROFILE <receipt-id>`.

Keep the `original-backup` and `active-generated` items distinct in the receipt. Generated state may contain useful post-reset work. Never restore an `active-generated` archive over an original profile. After verified rollback, set `current_state: full-profile-restored` without changing `origin_scope_result`.

An archive policy is monotonic: `pending` may become one selected scope, but a selected scope never changes or broadens. In particular, `reference-only` and `selective-config` can never become `full-profile`.

## Record-test

Record only:

- `passed`, `failed`, or `inconclusive`;
- product version and architecture;
- a coarse workspace class such as `single-folder`, `multi-root`, or `empty`;
- sync state such as `paused`, `active`, or `unknown`;
- timestamp.

The result is a user attestation, not proof of causality or eligibility for automatic escalation.
