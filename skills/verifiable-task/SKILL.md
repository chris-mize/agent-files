---
name: verifiable-task
description: Clarify the goal, agree on how to verify it, then do the work. Use when the user invokes verifiable-task or wants to settle intent and success criteria before execution.
license: MIT
---

# Verifiable Task

Resolve these four questions in order, reusing answers from the conversation. Ask only about gaps that could change the work or its verification. Ask one focused question at a time; wait before doing work that depends on the answer.

Speak plainly. Give enough context to answer without rereading the thread. When a choice matters, explain the options and consequences and recommend one.

```text
Objective → Evidence → Tools → Design if needed → Build ↔ Check → Done
```

## 1. What's the objective right now?

Identify the desired result, at whatever scale the user needs. Resolve ambiguities that would change what you deliver before discussing verification or design. State the objective briefly so misunderstandings are easy to catch.

## 2. How will we know it's done?

Agree on what must be true when the task is finished and what evidence would demonstrate it. Where this is unclear, suggest suitable checks and recommend what would be enough.

For code, some possible options are unit and integration tests, trying the running system through a browser or queries, screenshots, and recordings. Independent reviewers can check whether the code works and is the simplest sensible solution. They can also compare actual outputs—images, videos, or files—with the agreed target. For other work, choose checks suited to the result.

Choose checks that fit the objective, whether or not they appear in these examples. You decide which checks matter during each iteration. You don't need every check after every edit, but the agreed final criteria still have to pass.

## 3. What tools do we need?

Use tools and skills you know can provide the agreed evidence. Search for missing capabilities, using tool search when helpful. Confirm the access and capability you need, then move on. Prefer an adequate setup that takes the least time and tokens.

Explain the setup and make routine tool choices yourself. Ask about choices that change the evidence, involve significant setup or cost, or need user access. If verification is blocked, explain why and recommend a way forward.

## 4. Which design should we use?

Skip this for simple, direct work. For complex work:

- Develop three genuinely different designs that meet the objective.
- Have them reviewed independently. Also give a separate agent the objective and constraints to look for solutions you missed. Prefer different capable models when available; reviewers must not recruit more reviewers.
- Reconcile the findings and present the strongest three options, their benefits and tradeoffs, and your recommendation. Ask the user to choose before implementing.

Don't invent weak options to reach three. If fewer are viable, or independent agents are unavailable, explain why and get the user's agreement on how to proceed. Revisit the choice only when new evidence creates a meaningful design decision.

## Do the work

Track the agreed objective, final criteria, tools, and design in one place: the host's goal feature when available and permitted, otherwise its task tracker or the conversation.

Work, check results, and fix failures until the objective is met. Delegate when useful, passing along the relevant agreement. Stop for a user pause, a blocker, or a decision that needs the user. If repeated attempts make no progress, explain what's stuck.

Any of the four decisions can change. Follow user revisions; for your proposed changes, explain the effect and get signoff before dependent work. Update the agreement and affected delegates. Routine diagnostic choices within that agreement don't need approval.

Before declaring done, account for every final criterion. Reuse evidence that still applies; run checks where evidence is missing or changes may have invalidated it. Report what changed, what passed, and anything unverified. Mark the goal complete only when the objective and required criteria are met.
