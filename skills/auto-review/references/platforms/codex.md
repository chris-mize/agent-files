# Codex adapter

Invoke the installed skill explicitly:

```text
$auto-review
```

The bundled `agents/openai.yaml` sets `allow_implicit_invocation: false`. Treat that metadata as the Codex-side manual-only control and verify it against the active Codex version; it is guidance, not a security boundary.

For the review step, launch one independent Codex worker using the host's currently available subagent mechanism. Pass the report-only brief from `review-brief.md`. If the session cannot create a separate worker, stop and report that the independent-review gate could not be satisfied.
