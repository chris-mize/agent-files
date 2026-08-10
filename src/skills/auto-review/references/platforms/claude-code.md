# Claude Code adapter

Use the plugin-qualified command when installed as a plugin:

```text
/cmize-skills:auto-review
```

When the same `SKILL.md` is copied into Claude Code's ordinary skills directory, invoke it as:

```text
/auto-review
```

Claude Code's `disable-model-invocation: true` is the manual-only control for this skill. Do not infer that the frontmatter is a security boundary; verify the installed Claude Code version honors it before claiming support.

For the review step, use a genuinely separate Claude Code subagent facility available in the current session. Pass the report-only brief from `review-brief.md`. If no independent worker is available, stop with an evidence gap instead of performing a same-context self-review.
