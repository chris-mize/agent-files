# Worker Contract

Source-gathering workers receive only the original question, their assignment, depth, and the source constraints for their lane. They do not receive other source-gathering workers' conclusions before the synthesis stage.

## Assignment

Every assignment must name:

- `worker_id` and `round`;
- `model_profile`: lightweight research profile, preferably GPT-5.6 Luna or Grok;
- `lane`: `official`, `user-experience`, or `expert`;
- `query_strategy` and concrete search queries;
- `source_targets`;
- adversarial angle;
- geography, timeframe, population, or use-case constraints;
- expected output budget.

Same-lane Medium and Heavy assignments differ by query and/or source target. A perspective label alone is insufficient.

## Critique assignment

The separate critique worker runs after parent synthesis in a fresh context. It receives the original question, the current round's normalized compact claim ledger, the parent's draft synthesis, and a critique assignment. It audits omissions, contradictions, sanitized or liability-shaped guidance, vague recommendations, and source-lane imbalance; it does not gather a second copy of the same source set.

Return a compact critique record:

```text
Critique worker: <id>
Round: <round>
Model profile: <lightweight profile>
Input status: <ledger and draft synthesis received; isolation verified>
Status: <pass, partial, or failed>
Findings:
- Finding: <checkable issue>
  Category: <omission, sanitization, contradiction, vague guidance, or lane imbalance>
  Evidence: <ledger claim or synthesis passage>
  Recommended change: <specific revision or unresolved question>
Next-query updates: <distinct queries or none>
Unresolved: <remaining audit gaps>
```

The critique has one normal pass and at most one retry, for at most two fresh attempts. A `partial` result requires the retry; if it remains partial, it is failed. A malformed or zero-yield critique is failed, not passing. The parent owns every disposition and current-report effect; the critique recommends changes but does not approve its own findings.

## Cost-aware model policy

- Use GPT-5.6 Luna as the default research-worker profile when available.
- Use Grok for a complementary lightweight worker profile when available.
- Keep GPT-5.6 Sol out of routine source gathering unless the user explicitly requests it or the parent identifies a material unresolved reasoning problem.
- The parent agent owns the main synthesis, evidence matrix, discrepancy map, and final report. A single lightweight critique stage may challenge the parent's synthesis.
- Light/Medium/Heavy base depth counts are fixed required assignments. Extra Luna/Grok workers are allowed only as distinct, parent-authorized expansion within the protocol's announced per-round and per-run caps; record the actual count. Automatic expansion does not require a user confirmation.

## Result format

Return a compact result with these sections:

```text
Worker: <id>
Assignment: <lane, query strategy, source targets>
Access summary: <successful, partial, blocked, or failed; explain restrictions>

Consequential claims:
- Claim: <one checkable claim>
  Evidence type: <observation, source claim, pattern, interpretation, hypothesis>
  Source: <title; author/publisher; URL>
  Publication date: <date or unknown>
  Access date/status: <date; fetched, partial, blocked, deleted, or login-gated>
  Exact excerpt: <short verbatim excerpt, or why unavailable>
  Context: <population, sample, geography, timeframe, or use case>
  Source family: <identifier for syndicated/duplicate sources>
  Limitations: <selection, methodology, missing denominator, or other limitation>
  Incentives/conflicts: <known or unknown>
  Support: <independent corroboration or conflict>
  Evidence quality: <strong, moderate, limited, contested, or unknown; applicable dimensions and short reason>
  Confidence: <high, moderate, low, contested, or unknown; scope and convergence reason>

Exploratory leads:
- Claim, URL, date, excerpt if available, and next lead.

Unresolved:
- Missing sources, disputed claims, access gaps, or questions for the next round.
```

## Evidence rules

- One claim per consequential record.
- Use exact excerpts only from content actually fetched or visibly available.
- Record `unknown` instead of guessing a date, sample, author, or method.
- A search snippet is a lead, not decisive evidence.
- Do not count syndicated copies, reposts, or duplicate source families as independent corroboration.
- Report blocked, deleted, login-gated, or zero-result targets explicitly.
- A worker with zero successful fetches is failed. Preserve its attempted-source ledger and failure reason.
- Separate what users report from how common it is and from what causes it.
- Preserve relevant minority and contrarian findings even when they are weak; label their support and limitations.

## Output budgets

Default maximum consequential records:

- Light: 8 per worker;
- Medium: 6 per worker;
- Heavy: 4 per worker.

Keep excerpts to two sentences or 400 characters. Put lower-confidence leads in the short form. When a budget is reached, return uncaptured leads as unresolved gaps rather than silently dropping them. Apply the protocol's expansion caps and record planned assignments, actual attempts, retries, and failures separately.
