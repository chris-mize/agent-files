# Portable protocol

The protocol is host-neutral. Hosts may change how roles are launched, but they must preserve these records and state transitions.

## 1. IntentPacket

Create this packet once at intake and pass it unchanged to every role:

```json
{
  "schema": "intent-packet/v1",
  "request_id": "stable-run-id",
  "original_request": "verbatim user request",
  "requirements": [
    {"id": "R1", "text": "checkable requirement", "source": "user"}
  ],
  "constraints": [
    {"id": "C1", "text": "checkable constraint", "source": "user"}
  ],
  "non_goals": [],
  "ambiguities": [],
  "risk": "low|medium|high",
  "budget": {
    "max_revisions": 2,
    "max_role_calls": 8,
    "stop_on_unverified_gate": true
  },
  "sha256": "hash of canonical JSON without this field"
}
```

Requirements and constraints must be traceable to the request. Do not replace original wording with a plan claim. Add only grounded non-goals and ambiguities. For portable hashing, use RFC 8785 JSON Canonicalization Scheme, encode the canonical JSON as UTF-8, omit the `sha256` member, and compute lowercase hexadecimal SHA-256 over those bytes.

## 2. TaskContract

The controller or a fresh read-only planner derives a contract without changing the packet:

```json
{
  "schema": "task-contract/v1",
  "packet_sha256": "intent-packet-hash",
  "version": 1,
  "task_type": "coding|research|mixed",
  "scope": {
    "write_paths": [],
    "read_paths": [],
    "forbidden_paths": []
  },
  "requirement_map": {
    "R1": {"acceptance": "observable condition", "validation": "command or scorer"}
  },
  "assumptions": [],
  "edge_cases": [],
  "validation_commands": [],
  "stop_conditions": [
    "abort on missing role receipt",
    "escalate unresolved high-impact finding"
  ],
  "budget": {
    "max_revisions": 2,
    "max_role_calls": 8
  }
}
```

For clear low/medium-risk work, the controller may create a compact contract directly. For ambiguous or high-risk work, use a fresh read-only planner. A planner may propose structure, never new user requirements.

## 3. Handoff

Every role receives a handoff with:

```json
{
  "schema": "role-handoff/v1",
  "run_id": "stable-run-id",
  "from": "controller|planner|generator|critic",
  "to": "planner|generator|critic",
  "packet_sha256": "immutable-intent-hash",
  "contract": "task-contract-object",
  "artifact": {
    "kind": "diff|file-set|research-bundle",
    "identifier": "path or immutable artifact id",
    "write_scope": []
  },
  "verified_gates": [],
  "trajectory_digest": {
    "decisions": [],
    "identifiers": [],
    "commands": [],
    "outputs": [],
    "unresolved": []
  },
  "stop_condition": "structured stop rule",
  "receipt": "role model and host receipt"
}
```

Do not pass hidden tests, expected answers, private scoring keys, or prior reviewer conclusions into an agent being evaluated.

## 4. Verdict

The critic returns one of these states:

```json
{
  "schema": "critic-verdict/v1",
  "state": "PASS|REVISE|REPLAN|ESCALATE",
  "severity": "none|low|medium|high|critical",
  "findings": [
    {
      "id": "F1",
      "requirement_ids": ["R1"],
      "summary": "plain-language issue",
      "evidence": ["file:line or command output"],
      "confidence": "low|medium|high",
      "smallest_fix": "localized action",
      "verified": true
    }
  ],
  "residual_risk": [],
  "receipt": "critic role receipt"
}
```

- `PASS`: all requirements and gates are satisfied.
- `REVISE`: implementation defect or missing evidence with a clear local fix.
- `REPLAN`: the contract or approach is materially wrong; send a fresh planner.
- `ESCALATE`: unresolved ambiguity, high-impact risk, missing capability, or a choice the user must make.

The controller validates findings against the artifact before routing them. Unverified findings cannot authorize a revision.

## 5. Run states and receipts

Use these terminal states: `passed`, `stopped_budget`, `stopped_no_progress`, `degraded`, `escalated`, `failed_gate`, `inconclusive`, and `not_confirmed`. Use `not_confirmed` when a frozen required arm cannot run because its model or host capability is unavailable; it is not a quality failure or success. A successful run must include:

- host and invocation mode;
- requested and observed controller/generator/critic models;
- reasoning effort and speed tier;
- catalog/configuration snapshot and fallback state;
- role permissions and dispatch receipt;
- command exit statuses and relevant artifacts;
- revision count and call ledger;
- comparable cost pool/units or an explicit `inconclusive` state.

Explicit invocation must run the quality gate even for trivial work. A role-launch failure, missing model identity, missing execution evidence, or non-comparable cost must be visible in the final state.
