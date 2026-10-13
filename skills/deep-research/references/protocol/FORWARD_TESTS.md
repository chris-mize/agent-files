# Forward Tests

Run these checks before releasing the shared skill tree and after substantial protocol changes.

## Static checks

- Validate the skill frontmatter and description.
- Keep each skill wrapper under 500 lines and free of template placeholders.
- Confirm every platform adapter references the same canonical protocol and that all directly linked core/reference files resolve.
- Confirm routine research assignments use lightweight profiles when available, with no default heavyweight allocation.
- Run the repository validator from the repository root:

```bash
python3 scripts/validate.py
```

## Platform release gate

For each platform and both explicit and automatic invocation paths:

1. Start a fresh worker with the configured isolation mode.
2. Run a discovery query.
3. Fetch representative official, public-user, and expert evidence.
4. Record web access, isolation level, concurrency ceiling, and source restrictions.
5. For the automatic path, assert that it announces question, depth, current-round worker count, round cap, and batching plan after non-interactive preflight, then launches without a confirmation prompt.
6. For the explicit path, assert that it can run when the automatic announcement path is not involved.
7. Record the gate result as: platform, invocation mode, worker identity, isolation evidence, representative fetch results by lane, web restrictions, concurrency ceiling, preflight/announcement evidence, and pass/fail reason.
8. Block that platform's release if any required capability is absent.

Restricted services may be correctly classified as blocked or partially covered; the shared skill must report the limitation.

## Dry-run roster

Run a no-network roster test for each depth:

- Light: three workers, one per lane, adversarial queries folded into each worker.
- Medium: nine workers, three per lane, distinct query/source targets and at least one adversarial worker per lane.
- Heavy: eighteen workers, six per lane, distinct query/source targets and at least one adversarial worker per lane.

Verify no same-lane Medium/Heavy workers share the same query and source target. Verify the batch plan, expansion caps, per-round ledger fields, and expected worker count without launching live workers. Verify any expanded worker count uses distinct assignments and that the parent owns main synthesis rather than launching multiple heavyweight synthesis workers.

## Live behavior tests

Use fresh threads and realistic topics. Check:

- official-versus-user disagreement;
- expert-versus-official disagreement;
- high-stakes research with actionable but uncertain options;
- blocked/deleted/login-gated sources;
- citation integrity for action-driving claims;
- citation-integrity partial and failed-retry behavior;
- critique findings updating the next query set;
- critique dispositions updating the current synthesis;
- parent synthesis consuming compact worker records;
- lightweight model mix across research workers;
- two consecutive low-novelty rounds and capped unsaturated-frontier reporting;
- synthesis failure retry;
- critique failure retry;
- partial critique retry and terminal-failure handling;
- parent-owned synthesis retry and context-limited fallback;
- source-worker zero-fetch retry with bounded attempts, accurate retry accounting, and explicit lane debt when recovery fails;
- adaptive expansion announcing the revised count and batch plan before additional workers start;
- interrupted recovery with incomplete status;
- material redirection starting a new run;
- per-round accounting and unsaturated-frontier fields;
- ordinary runs leaving no files behind.

Forward tests should inspect raw worker records, normalized ledgers, citations, stage outputs, and the final chat report. Do not pass expected conclusions into the test workers.
