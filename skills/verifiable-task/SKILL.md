---
name: verifiable-task
description: Agree on an objective, observable completion criteria, verification tools, and meaningful design choices before carrying a task through to verified completion. Use when the user invokes verifiable-task or asks to lock in intent and how success will be demonstrated before execution.
license: MIT
---

# Verifiable Task

Make the intended outcome explicit, agree on what will prove it, then work until that agreement is met. Scale the conversation to the task: a small edit can have a short agreement; a complex system needs more investigation.

```text
Objective → Completion criteria → Verification tools → Design, when needed
    ↑                         User-approved revisions                  ↓
    └─────────────────────────────── Implement ↔ Check → Final evidence
```

## Conversation rules

- Speak in plain engineering language, like one person talking to another. Define unfamiliar terms briefly. Avoid invented labels and unexplained shorthand.
- Make each question self-contained: name the task, explain the decision and why it matters, offer concrete options with consequences, and recommend one. The user should be able to decide from that message alone while switching between chats.
- Work through steps 1–4 in order. Ask one focused question at a time, with follow-ups where needed, and wait for the answer before advancing a decision that depends on it. Do not dump the four steps into a questionnaire.
- Use answers already supplied in the conversation. Summarize them rather than asking again; ask for confirmation only where the agreement is missing or materially unclear.
- Read-only inspection may support the current step. Resolve the objective before proposing tests or designs, and finish the applicable agreement before implementing.

## 1. What is the objective right now?

If the objective is missing, ask that question first. If one was supplied, restate it concretely and ask the first unresolved follow-up. An objective can be as large or small as the user needs.

Clarify the desired behavior or result, scope, constraints, and material ambiguities before moving on. Separate the outcome from any proposed solution. Ask enough follow-ups to establish shared understanding without making the user specify routine implementation details.

Finish with a concise objective statement grounded in the user's answers. Do not silently add features or drop stated requirements.

## 2. How should we verify that it is done?

Suggest a few verification options suited to this objective, explain what each demonstrates, and recommend a sufficient combination. Ask the user to choose or adjust the final completion criteria: behavior, tests that must pass, observable outputs, reference designs, or other required evidence. Make qualitative expectations concrete enough to judge together.

For coding tasks, relevant options may include:

- Unit tests for isolated behavior; integration tests for components working together.
- Validation in the running system through a browser, queries, commands, or another task-appropriate interface.
- Screenshots for visual state or recordings for interactions and timing.
- Independent adversarial code review focused on whether it works and whether the solution is the simplest sensible design.
- Independent inspection of actual outputs, such as recordings, screenshots, or files, against the agreed target or design. Source review alone does not establish that the output matches.

These are options, not a mandatory checklist. For non-coding work, propose checks against its actual output, such as source reconciliation, calculations, file inspection, or comparison with a reference.

Keep **final completion criteria** distinct from **checks during iteration**. The user sets the required end state. The agent chooses which checks matter after each change, may add or adapt diagnostic checks, and need not rerun everything on every edit. That discretion does not permit weakening the final criteria or substituting weaker evidence without user signoff.

## 3. What tools will provide that evidence?

Inspect the actual environment: available tools and connections, relevant skills, command-line programs, existing tests, browser access, and independent-worker facilities. Verify relevant capabilities with inexpensive, non-destructive checks. Do not assume a tool is available merely because it is named in instructions.

Map each completion criterion to a feasible tool and the evidence it will produce. Prefer existing tools and the fastest, most token-efficient method that still supplies sufficient evidence. A tool's absence is a verification gap, not a passing result.

Present the proposed verification setup. Ask a sequence of focused questions only for consequential choices or missing access, with recommendations grounded in step 2. For example: “For the checkout form, you required validation of the rendered controls. I recommend the live browser with screenshots because it is available and shows the actual layout. A Cypress test would add repeatable interaction checks but needs setup. Which evidence do you want?” Do not ask how to read files or use Git, or invent a tooling choice when the environment already provides a clear answer.

Resolve necessary access or agree on an adequate alternative before depending on that tool. Request only the missing capability; avoid broad installation or configuration changes. If no adequate method is available, explain exactly what is blocked and what the user needs to supply or decide.

## 4. What design or implementation direction should we take?

Skip this step for simple, direct work with no meaningful design decision. For complex work:

1. Develop three materially different, feasible designs that meet the objective and completion criteria. Include the simplest credible approach; do not pad the set with cosmetic variants or knowingly unsuitable options.
2. Automatically obtain independent review of the designs and a separate re-ideation worker tasked with finding missed solutions from the objective and constraints. Give the re-ideation worker the agreed task and relevant system facts before the candidate designs, so it can reason independently. Reviewers should assess correctness, simplicity, verification feasibility, and tradeoffs. They report findings and must not recruit nested reviewers.
3. Prefer different capable model families when the host supports them and access is available. Inspect current capabilities rather than hardcoding model names. Independent workers on the available model are acceptable; do not claim model diversity or independence that did not occur. If independent work is unavailable, disclose the gap and get user signoff on a fallback before proceeding with the complex design decision.
4. Reconcile the findings with evidence and rank the strongest three options, including a missed alternative when it improves the set. Explain each in plain language: how it works, benefits, tradeoffs, and implications for verification. Give a clear recommendation, then ask the user to select or adjust the direction and wait. If fewer than three viable options survive, explain why and ask whether to proceed with the remaining choices rather than inventing alternatives.

Ordinary local implementation choices remain the agent's responsibility. If execution later reveals materially different designs that meet the objective, bring that choice back to the user with context and a recommendation before committing to one.

## Execute and verify

Keep a compact current agreement in the conversation or the host's existing task record:

- Objective and scope.
- Required end behavior and evidence.
- Verification tools and any access limitations.
- Chosen design, or why design selection was unnecessary.

Use the host's goal mechanism when available and authorized, or its equivalent task tracker. If no such facility exists, track progress against the agreement in the conversation. Do not invent tool calls, replace an unrelated active goal, or set unrequested budgets. A goal tracker records work; it does not by itself guarantee unattended execution.

Work through implementation and relevant checks until the objective and final criteria are met. Choose direct work or delegation according to expected speed, token cost, and reliability; execution delegation is optional. Give delegates the relevant agreement and a bounded task. Reuse applicable skills instead of duplicating their procedures.

Inspect actual results, fix failures, and repeat the checks affected by changes. Keep updates short and self-contained: what was learned, what remains uncertain, and what will resolve it. Avoid repeated checks without new evidence or unnecessary progress ceremony.

If progress requires missing access, a material user decision, or an action outside the authorized scope, state the exact blocker and ask the focused question. Stop on a user pause or cancel instruction. If repeated attempts make no progress, explain the failure and propose a concrete next decision rather than looping indefinitely or declaring success. Respect host limits and report unfinished work accurately.

## Changes to the agreement

Any of steps 1–4 may change during the conversation. A direct user revision is the new instruction; clarify only its material ambiguities. For an agent-proposed change, explain what would change, why, and the effect on scope, evidence, or design, then obtain user signoff before dependent work. Silence is not signoff.

Update the current agreement, goal record where supported, and affected delegate briefs. Replace superseded direction in working artifacts. Revisit only affected decisions and checks; do not restart the whole interview. Routine diagnostic choices within the agreed verification setup remain at the agent's discretion.

## Finish

Compare the result with every current completion criterion and inspect the required evidence on the final result. Reuse earlier evidence only where subsequent changes have not invalidated it. Mark the goal complete only when the objective and all required criteria are satisfied.

Report the outcome, relevant evidence, and material assumptions or limitations concisely. Distinguish passed, failed, and unverified criteria. A plausible implementation, a passing unit test, or a review opinion proves only what it actually checked.
