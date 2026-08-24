# Intent Lock

Read this when locking intent, before launching any reviewer.

The parent is trusted to build the lock. Reconstruct exceptionally clear user intent from the thread, then hand that clarity to the reviewer. A thin goal-only lock is a defect because the reviewer can only check what is included.

## How to extract

1. Walk the thread. User messages are authoritative. Agent messages are leads back to user-endorsed asks, not new requirements.
2. Pull every live ask: concrete wants, constraints, corrections, additions, and explicit refusals.
3. Reconcile agent summaries with the user's words. Discard agent-only additions or mark them as open questions.
4. Write the lock clearly enough that a cold reviewer can judge the artifact without chat history.
5. Re-read the thread once more specifically looking for missed live requirements.

## Lock shape

```text
LOCKED INTENT
Outcome: …
Stated requirements & details:
- … — "short user quote" when possible
Constraints & preferences:
- … — "short user quote" when possible
Open questions: (none | …)
```

Keep artifact facts separate from the lock so solution claims do not become user requirements. Mark inferred bullets `(inferred)` and treat them as weaker.

## When to stop and ask

Ask one or two focused questions when different answers would change the review target, acceptance bar, or allowed edits. Otherwise lock and proceed.

After review, walk every locked detail and constraint against the artifact and mark it met, violated, or unclear. A headline outcome that omits a stated detail is not ready.
