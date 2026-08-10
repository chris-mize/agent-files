# Codex adapter

Invoke the skill explicitly with `$actor-critic-mode`. The bundled Codex metadata disables implicit invocation.

Use Codex's fresh task or agent facility for the generator and read-only critic when those capabilities and receipts are available. Record the requested and observed model, fresh-context evidence, permissions, tool access, and fallback state in the handoff.

If the current Codex session cannot verify the required role isolation, structured receipts, or capability boundary, stop with `not_confirmed` or a degraded run. Do not substitute same-context prompting and call it an independent role.
