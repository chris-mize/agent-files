# Cursor adapter

Invoke the skill explicitly with `/actor-critic-mode`. The skill frontmatter disables model-only invocation.

Use Cursor's independent agent or subagent facility for the generator and fresh read-only critic when those capabilities and receipts are available. Record the requested and observed model, fresh-context evidence, permissions, tool access, and fallback state in the handoff.

If the current Cursor session cannot verify the required role isolation, structured receipts, or capability boundary, stop with `not_confirmed` or a degraded run. Do not substitute same-context prompting and call it an independent role.
