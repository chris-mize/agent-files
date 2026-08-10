# Chat Report Contract

Return the report in chat unless the user explicitly requests a saved dossier. Keep the readable report concise; preserve detail through claim-level links and compact evidence records.

## Required order

1. **Question and scope**: research question, inferred assumptions, geography/timeframe, depth, invocation mode, round status, lane coverage, and compact run accounting.
2. **Provisional orientation**: a short navigational answer only. Mark it provisional and point to material disagreement below.
3. **Findings by lane**: official/primary evidence, user experience patterns, and expert positions.
4. **Discrepancy map**: where lanes agree or conflict, with reasons for divergence.
5. **Knowledge tiers**:
   - observed evidence;
   - source claims;
   - corroborated patterns;
   - expert interpretations;
   - competing explanations/options;
   - actionable guidance and trade-offs.
6. **Claim-level evidence**: cite consequential claims at first appearance and include source title, author/publisher, URL, publication date, access date/status, short excerpt, and limitations.
7. **Evidence matrix**: confidence, support, conflicts, missing coverage, and what would change the conclusion.
8. **Final synthesis**: opinions, options, trade-offs, and action choices. The user retains the decision.
9. **Gaps and continuation**: saturation status, unresolved claims, source restrictions, and proposed next queries.

## Run accounting

For each round, report the base assignment count, approved expansion count, planned count, batch plan, capability-probe status, attempted/completed/failed research workers, retries, critique status and attempts, draft/final synthesis statuses, citation-integrity status, stop reason, and lane-specific novelty, yield, debt, and next queries. Keep probes, retries, critique workers, and research assignments distinguishable.

## Citation rules

- Cite the first occurrence of every consequential claim; the evidence section indexes citations rather than repairing uncited prose.
- Mark inaccessible, changed, deleted, login-gated, and unverified sources.
- Do not imply that a source supports a stronger claim than its excerpt or method supports.
- Keep low-impact evidence compact, but retain enough information to trace it.
- Report citation-integrity as `pass`, `partial`, or `fail`. `Partial` is an acceptable qualified outcome when inaccessible citations are explicitly labeled and do not solely support action guidance; affected claims remain qualified. `Fail` means an unresolved mismatch or unverifiable citation supports action guidance; qualify or remove that guidance and disclose the failed check.

## Status labels

Use explicit status labels:

- `complete`: all required stages passed and the round's coverage supports the stated conclusion;
- `provisional`: useful evidence exists but further research or reconciliation is needed;
- `contested`: credible sources materially disagree;
- `incomplete`: interrupted, capped, or lane coverage is materially missing;
- `terminal coverage failure`: a required synthesis, critique, or citation-integrity stage could not complete after its bounded retry.

Never claim saturation for an incomplete round. Prior completed rounds may retain an established saturation result, but the interrupted round must still be labeled incomplete.

## Interruption and failure

- Stop launching workers when interrupted or redirected.
- If draft synthesis, critique, and final synthesis pass on completed records and citation integrity is `pass` or qualifying `partial`, return an incomplete partial synthesis; provisional options may be included without claiming saturation.
- If critique fails after retry, return the labeled claim ledger/raw findings and failed phase without action guidance.
- If synthesis fails after retry, return the labeled claim ledger/raw findings and failed phase without a partial synthesis.
- If citation integrity fails after retry, return the affected claims with their access/status limitations and omit unqualified action guidance based on them.
- If the user materially changes the question, start a new run rather than mixing questions.
