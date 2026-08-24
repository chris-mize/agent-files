# Cursor adapter

Invoke the installed skill explicitly:

```text
/auto-review
```

Cursor honors the shared `disable-model-invocation: true` skill metadata only when the active skills surface implements that field. Verify the installed Cursor version and installation surface before claiming manual-only enforcement; prompt text cannot provide a security boundary.

For the review step, use one independent Cursor agent or subagent facility available in the current session. Pass the report-only brief from `review-brief.md`. If no independent worker is available, stop with an evidence gap rather than calling a same-context self-review independent.
