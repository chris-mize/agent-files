# Deep Research Protocol

Use this protocol for broad, contested, decision-oriented, or high-stakes questions where a single source class is insufficient.

## Operating principles

- Research across three independent lanes: official/primary evidence, real-user experience, and named independent authorities.
- Treat institutional status, credentials, repetition, popularity, and polished prose as signals—not proof.
- Actively search for criticism, failure modes, incentives, counterexamples, dissent, and what standard guidance omits.
- Include useful nonofficial evidence without sanitizing it. Label its basis, limitations, conflicts, and uncertainty.
- Use cost-aware lightweight research workers by default; reserve model capacity for the parent agent's synthesis and decision support.
- Return research in chat by default. Create a saved dossier only when requested.
- Never claim to have opened a source, used a platform, or verified a quotation when that did not happen.

Read the directly linked contracts as needed:

- [WORKER_CONTRACT.md](WORKER_CONTRACT.md): worker assignments and result records.
- [EVIDENCE_RUBRIC.md](EVIDENCE_RUBRIC.md): source evaluation, ontology, and disagreement handling.
- [REPORT_CONTRACT.md](REPORT_CONTRACT.md): chat output and interruption behavior.
- [FORWARD_TESTS.md](FORWARD_TESTS.md): release and regression checks.

## 1. Intake and runtime gate

1. Infer the question, decision context, scope, geography, timeframe, and stakeholders.
2. Ask a follow-up only when ambiguity would materially change the research.
3. Infer `depth` as Medium unless the user specifies Light or Heavy.
4. Before launching research assignments, perform a non-interactive runtime preflight:
   - the platform provides a fresh isolated worker context;
   - a current capability check or bounded probe establishes that the worker can run a discovery query and fetch representative official, public-user, and expert evidence;
   - web access and source restrictions are visible;
   - the shared protocol is readable;
   - the current concurrency ceiling is known or conservatively bounded so the batch plan can be computed.
   If a bounded probe is needed, record it separately from research assignments and disclose its scope; it does not count toward the Light/Medium/Heavy worker count. The preflight is not a user confirmation step.
5. For automatic invocation, after preflight and roster generation, announce the inferred question, depth, current-round worker count, round cap, and expected batching plan, then begin without a confirmation prompt. The announced worker count is the planned research-assignment count for that round: three for Light, nine for Medium, or eighteen for Heavy before approved expansion. Keep interruption and redirection available. Automatic-path behavior is release-tested separately.
6. If the platform cannot provide genuinely isolated, web-capable workers, halt that run and report the capability gap. Do not relabel same-context sequential prompts as independent researchers.

## 2. Worker allocation

Create a new, isolated worker for every assignment. Do not give workers other source-gathering workers' conclusions before the synthesis stage.

- Light: one worker per lane, three total.
- Medium: three workers per lane, nine total.
- Heavy: six workers per lane, eighteen total.

For Medium and Heavy, same-lane workers must differ by query and/or source target. Perspective can supplement that distinction but cannot replace it. At Light, fold the adversarial query set into the sole worker for each lane. At Medium and Heavy, assign at least one adversarial worker per lane.

Batch launches when platform concurrency is lower than the requested count. Preserve the requested assignment count, record attempted/completed/failed workers, and disclose isolation level and batching. For each failed assignment, allow at most one retry in a new isolated context when the failure appears transient or platform-specific; do not retry an invalid assignment or a source that is explicitly blocked. A worker with zero successful fetches is failed, not merely low-yield.

### Model and synthesis policy

- Default research workers to a lightweight fast profile: GPT-5.6 Luna when available, or Grok when available. Mix the two across lanes or rounds when practical to reduce correlated blind spots.
- Do not default repetitive source-gathering workers to GPT-5.6 Sol. Use a heavier model only when the user explicitly requests it or when the parent identifies a material unresolved reasoning problem that a lightweight retry cannot resolve.
- The parent agent owns normalization, cross-lane synthesis, the evidence matrix, discrepancy analysis, final report, and decision options. Keep worker records compact enough for the parent to synthesize them directly.
- Use one independent lightweight critique stage per round, preferably Luna or Grok, with at most two fresh attempts including one retry. Launch a separate synthesis worker only when the parent context cannot safely hold the compact ledger.
- Light/Medium/Heavy counts are the base assignment counts for each round. When lightweight workers make it practical, add extra distinct assignments for breadth; announce the revised current-round count and batching plan before launching them, and preserve unique queries or source targets. Record retries and actual attempted/completed/failed counts separately from planned assignments.
- Expansion is bounded: unless the user configures a different budget, allow at most one additional base roster per round and at most `base_count × configured_round_cap` extra assignments across the run. Here `base_count` is three, nine, or eighteen assignments for Light, Medium, or Heavy. `Approved expansion` means parent authorization within that configured budget; it does not require a user confirmation. Retries are recorded as attempts and do not create new planned assignments. If an expansion cap is reached, report the remaining coverage frontier.

### Dry run

When `dry-run` is requested, generate and display the complete worker roster—lane, depth, assignment, adversarial angle, query, source target, and batch—then stop before launching workers or fetching sources.

## 3. Research lanes

### Lane A: official, authoritative, and primary evidence

Search institutional publications, regulators, standards, datasets, technical documentation, peer-reviewed work, original records, and relevant industry material. Record institutional mandate, publication purpose, funding, marketing or liability incentives, definitions, measurement choices, and missing data.

### Lane B: real-user experience

Search public Reddit, GitHub issues/discussions, Facebook/public community material, Google reviews, app stores, forums, blogs, and other relevant user-report sources. Aggregate recurring patterns and representative experiences while separating prevalence, anecdotes, review-selection effects, duplicate reports, and causal evidence.

Report Reddit, GitHub, Facebook, and Google Reviews separately as covered, partially covered, or blocked, with the reason and resulting gap. Login-gated, deleted, or inaccessible material is an access limitation, not evidence.

### Lane C: independent authorities and field experts

Find practitioners, researchers, critics, long-term users, independent analysts, and well-informed armchair experts inside or outside official institutions. Profile demonstrated work, technical depth, lived experience, long-term track record, predictive accuracy where applicable, peer/community reputation, methods, incentives, and conflicts. Credentials are one signal, not a gate.

## 4. Query design

Give each worker a distinct assignment containing:

- the question and decision context;
- a lane and source target;
- terminology, synonyms, adjacent fields, and definitions to test;
- geography, timeframe, stakeholder, and use-case variants;
- an adversarial angle: failures, criticism, counterexamples, incentives, independent audits, dissent, or omitted practical detail.

Use synthesis to find missing populations, regions, periods, use cases, definitions, expert schools, and high-impact unresolved claims. Expand queries rather than repeating searches. Do not treat a new URL, repost, synonym, or duplicate source family as material novelty.

## 5. Round lifecycle

For each round:

1. Generate distinct assignments.
2. Run all assigned workers in fresh contexts, in bounded batches.
3. Normalize their records without merging away disagreement.
4. Have the parent agent synthesize the compact records, or use one lightweight synthesis worker only when parent context is insufficient.
5. Run one independent lightweight critique stage in another fresh context.
6. Have critique audit omissions, sanitized or liability-shaped guidance, contradictions, vague recommendations, and source-lane imbalance. Record a disposition for every material critique finding, apply accepted findings to the current synthesis, and update the next query set from the audit.
7. Have the parent produce the final current-round synthesis and action guidance from the revised ledger. Keep unresolved critique findings visible and qualify or remove affected guidance.
8. Run a bounded citation-integrity check for action-driving or uncertain citations.
9. Decide whether another round is needed.

In a normal round, draft synthesis, critique, and final synthesis must pass before unqualified action guidance. Citation integrity must be `pass` or a qualifying `partial`; a partial result permits only guidance whose claims do not depend on the inaccessible citations, while affected claims remain qualified. If a stage fails, retry that stage once with the same cost-aware policy from the compact claim ledger. The parent retries draft and final synthesis in its own context; a lightweight synthesis fallback is allowed only after the parent records that its context cannot safely hold the ledger. A citation result is `pass` when required checks succeed, `partial` when inaccessible citations are explicitly marked and do not solely support action guidance, and `fail` when an unresolved citation mismatch or unverifiable citation supports action guidance. A partial critique is not a pass: retry it, and treat a still-partial result as a failed required stage. After a failed retry, preserve the affected ledger and disclose the failed stage; do not present affected action guidance as reliable.

On interruption or redirection, stop launching workers and recover from completed records. If draft synthesis, critique, and final synthesis pass and citation integrity is `pass` or qualifying `partial`, return a partial synthesis labeled with incomplete coverage; provisional options may be included, but do not infer saturation from the incomplete round. If draft synthesis, critique, or final synthesis fails after retry, return the labeled ledger/raw findings and failed phase without action guidance. If citation integrity fails after retry, return the affected claims with their limitations and omit only action guidance based on those claims. A material question change starts a new run.

### Per-round run ledger

Record a compact ledger for every round:

- invocation mode, round, depth, base assignment count, approved expansion count, planned count, and batch plan;
- capability-probe status and scope, kept separate from research assignments;
- research attempted/completed/failed workers and retries;
- critique worker model, attempt count, status, material findings, and dispositions;
- draft-synthesis, final-synthesis, and citation-integrity statuses and retry counts;
- material novelty and evidence yield by lane, unresolved lane debt, consecutive low-novelty count, stop reason, and next queries.

## 6. Saturation

Continue automatically under a configurable bound; the default maximum is three rounds, and the user may raise it or request another pass.

Material novelty means a new decision-relevant claim, mechanism, option, affected population, or credible expert position that changes the evidence matrix or available choices. Track novelty, unresolved coverage, and evidence yield separately by lane.

Stop early only when:

- successive rounds add no material claims, options, or credible positions;
- major contradictions are resolved or explicitly irreducible;
- high-impact claims have independent support or a clearly reported lack of support;
- lane coverage is adequate or its debt is explicit; and
- remaining gaps and next queries are named.

Require two consecutive low-novelty rounds when feasible. Record any reason a second low-novelty round was not feasible. If the bound is reached first, report `unsaturated frontier` with lane-specific gaps and next queries instead of implying that the whole space was found.

## 7. Failure and integrity rules

- A missing shared core, unavailable isolated worker, or failed release gate blocks that platform's run.
- A failed synthesis or critique never silently becomes a final answer.
- A source that cannot be fetched is marked unverified or inaccessible.
- Re-fetch every citation supporting an action recommendation and citations flagged as uncertain when accessible; mark changed or unverifiable sources.
- A failed citation-integrity retry blocks unqualified guidance based on the affected claims and gives the report an incomplete or terminal coverage-failure status.
- Never use an official-only fallback for high-stakes topics. If platform restrictions affect the source mix, state the restriction and the resulting gap.
