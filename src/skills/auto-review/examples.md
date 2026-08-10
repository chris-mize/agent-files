# Auto-Review Examples

## Intent and artifact

Bad: invent a full non-goals list and review against it.

Bad: lock only the headline outcome while omitting concrete requirements stated earlier.

Good: walk the thread, lock Outcome plus every live checkable detail and constraint, and mark each detail met or violated after review.

## Cold-reader escalation

Bad: “Promotion gate guards are malformed on validation params.”

Good: explain what was planned or built, how it diverges from intent, and give two or three plain-language options with a recommendation.

## Plan rewrite

Bad: append a “Reviewer feedback” section and leave the rejected approach in place.

Good: rewrite the plan to contain only the surviving approach.

## Reviewer model

Bad: always inherit, always use one model, or hardcode an expensive model identifier.

Good: choose from the host's live menu, prefer a capable non-matching family when possible, and state the selected model in the run summary.

## Pass modes

- `/auto-review` uses the until-complete loop.
- `/auto-review single pass` runs exactly one cycle.
