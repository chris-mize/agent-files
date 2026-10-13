# Claude Code adapter

Use the Claude Code subagent facility that is available in the current session. Confirm that each worker is a fresh isolated context and that it can access the web before assigning research. A worker that cannot fetch representative evidence is failed or blocked according to the protocol.

For automatic runs, complete the non-interactive preflight and announce the inferred question, depth, current-round worker count, round cap, and batching plan before launching. Do not ask for a confirmation merely because the run is automatic.

If the current Claude Code installation cannot provide both fresh isolated workers and web access, stop with a capability gap. Do not downgrade to same-context prompts.
