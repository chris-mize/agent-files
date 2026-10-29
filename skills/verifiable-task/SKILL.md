---
name: verifiable-task
description: Clarify the goal, agree on how to verify it, then do the work. Use when the user invokes verifiable-task or wants to settle intent and success criteria before execution.
license: MIT
---

# Verifiable Task

Agree on what done means before starting. Walk through these questions in order, using answers the user has already given. Ask follow-ups one at a time and wait for answers that affect the next step.

Speak plainly. Each question should give enough context, options, tradeoffs, and a recommendation that someone switching between chats can answer without rereading the thread.

```text
Objective → Evidence → Tools → Design if needed → Build ↔ Check → Done
```

## 1. What's the objective right now?

Clarify the result, scope, and constraints. Ask follow-up questions first, until you understand what the user wants. The task can be any size. Summarize the objective before moving on.

## 2. How will we know it's done?

Suggest a few ways to check the result and recommend what would be enough. Agree with the user on what must be true when the task is finished.

For code, some possible options are unit and integration tests, trying the running system through a browser or queries, screenshots, and recordings. Independent reviewers can check whether the code works and is the simplest sensible solution. They can also compare actual outputs—images, videos, or files—with the agreed target. For other work, choose checks suited to the result.

Choose checks that fit the objective, whether or not they appear in these examples. You decide which checks matter during each iteration. You don't need every check after every edit, but the agreed final criteria still have to pass.

## 3. What tools do we need?

Inspect the available tools, skills, command-line programs, test setup, browser, and agent facilities. Recommend tools that can produce the agreed evidence with the least time and tokens.

Ask about meaningful choices or missing access, with a recommendation: “You want the rendered components checked. I recommend the live browser with screenshots; Cypress would add repeatable interaction tests but needs setup. Which do you prefer?” Don't ask obvious questions about reading files or using Git. If required tools are unavailable, explain the gap and agree on a way forward.

## 4. Which design should we use?

Skip this for simple, direct work. For complex work:

- Develop three genuinely different designs that meet the objective.
- Have them reviewed independently. Also give a separate agent the objective and constraints to look for solutions you missed. Prefer different capable models when available; reviewers must not recruit more reviewers.
- Reconcile the findings and present the strongest three options, their benefits and tradeoffs, and your recommendation. Ask the user to choose before implementing.

Don't invent weak options to reach three. If fewer are viable, or independent agents are unavailable, explain why and get the user's agreement on how to proceed. Bring meaningful new design choices back to the user if they arise later.

## Do the work

Keep a short record of the agreed objective, final criteria, tools, and design. Use the host's goal feature when available and permitted, otherwise its task tracker or the conversation.

Work, check the results, and fix failures until the objective is met. Delegate when it saves time or tokens; execution delegation is optional. Give delegates the relevant agreement. Stop for a user pause, a real blocker, or a decision that needs the user. If repeated attempts make no progress, explain what's stuck instead of looping.

Any of the four decisions can change. Follow user revisions; for changes you propose, explain the effect and get signoff before dependent work. Update the agreement and affected delegates without restarting the whole interview. Choosing different diagnostic checks within that agreement doesn't need approval.

Before declaring done, check every final criterion against evidence that still applies to the finished result. Report what changed, what passed, and anything unverified. Mark the goal complete only when the objective and required criteria are met.
