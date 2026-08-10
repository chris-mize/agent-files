---
name: deep-research
description: Conduct deep, subagent-driven research across official and primary sources, real-user experiences, independent experts, and adversarial perspectives; map disagreements and evidence quality and return actionable options with claim-level citations. Use for broad, contested, decision-oriented, or high-stakes questions that require more than one source class.
license: MIT
compatibility: Claude Code, Codex, or Cursor with isolated web-capable workers
---

# Deep Research

Use this skill for research that benefits from independent source lanes and iterative coverage rather than a single answer or source list.

## Required protocol

Before planning or launching workers, read:

- [RESEARCH_PROTOCOL.md](references/protocol/RESEARCH_PROTOCOL.md)

Load only the references needed for the current stage:

- [WORKER_CONTRACT.md](references/protocol/WORKER_CONTRACT.md): assignments and normalized worker results.
- [EVIDENCE_RUBRIC.md](references/protocol/EVIDENCE_RUBRIC.md): source quality, claim ontology, and disagreements.
- [REPORT_CONTRACT.md](references/protocol/REPORT_CONTRACT.md): synthesis, chat output, interruption, and failure handling.
- [FORWARD_TESTS.md](references/protocol/FORWARD_TESTS.md): release and regression checks.

## Runtime selection

Identify the active host from its system instructions and available tools. Read exactly one matching file from [references/platforms/](references/platforms/):

- [Claude Code](references/platforms/claude-code.md)
- [Codex](references/platforms/codex.md)
- [Cursor](references/platforms/cursor.md)

If the host cannot provide genuinely isolated, web-capable workers, report the capability gap and stop. Do not substitute same-context prompts and call them independent researchers.

## Execution

- Use the active platform's configured isolated multi-agent/task launcher with live search, or another verified path documented by the platform adapter.
- Use the protocol's fixed Light/Medium/Heavy base lane counts and distinct assignments; any expansion must stay within the protocol's announced caps.
- Have the parent agent perform normalization, draft/final synthesis, the evidence matrix, discrepancy analysis, and final report. Use one lightweight independent critique stage with at most one retry.
- Run the non-interactive capability/concurrency preflight first. For automatic invocation, announce the inferred question, depth, current-round worker count, round cap, and batching plan after preflight, then proceed without a confirmation prompt.
- Keep interruption and redirection available; return the protocol's incomplete or failure status when a run is stopped.
- Keep output in chat unless the user requests a saved dossier.

Never claim to have opened a source, used a platform, or verified a quotation when that did not happen.
