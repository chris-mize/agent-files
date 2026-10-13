#!/usr/bin/env python3
"""Fail-closed capability probe for a host-supplied model/role snapshot.

The host adapter supplies the JSON snapshot; this script does not invent a
catalog or silently substitute a model. The snapshot is also the source for
the run's actual-model receipt.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

PROFILE_ROLES = {
    "grok-oneshot": {},
    "grok-loop": {"generator": "grok", "critic": "grok"},
    "luna-oneshot": {},
    "luna-loop": {"generator": "luna", "critic": "luna"},
    "cheap-generate-strong-critic-terra": {"generator": "luna", "critic": "terra"},
    "cheap-generate-strong-critic-sol": {"generator": "luna", "critic": "sol"},
    "sol-oneshot": {},
    "sol-standard": {},
    "grok-scaffolded-oneshot": {"generator": "grok"},
    "luna-scaffolded-oneshot": {"generator": "luna"},
    "luna-terra-scaffolded-oneshot": {"generator": "luna"},
    "luna-sol-scaffolded-oneshot": {"generator": "luna"},
}


def normalize(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value).lower())


def model_matches(observed: Any, required: str) -> bool:
    return observed == required


def probe(snapshot: dict[str, Any], host: str, profile: str) -> dict[str, Any]:
    reasons: list[str] = []
    if not isinstance(snapshot, dict):
        return {
            "schema": "actor-critic-mode/capability-receipt/v1",
            "host": host,
            "profile": profile,
            "catalog_snapshot": None,
            "eligible": False,
            "reasons": ["snapshot must be a JSON object"],
            "warnings": [],
            "write_scope_enforcement": "not_applicable",
            "planner_required": False,
            "usage_attribution": None,
            "role_checks": {},
            "required_roles": ["controller"],
            "actual_models": {},
        }
    if snapshot.get("host") != host:
        reasons.append(f"snapshot host is {snapshot.get('host')!r}, expected {host!r}")
    if (
        not isinstance(snapshot.get("catalog_snapshot"), str)
        or not snapshot.get("catalog_snapshot").strip()
    ):
        reasons.append("catalog_snapshot is missing")
    if snapshot.get("usage_attribution") is not True:
        reasons.append("usage_attribution is not confirmed")
    if snapshot.get("fallback") is not False:
        reasons.append("snapshot reports a fallback")
    catalog_models = snapshot.get("catalog_models")
    if not isinstance(catalog_models, list) or not catalog_models:
        reasons.append("catalog_models is missing")
        catalog_models = []
    elif not all(isinstance(model, str) and model for model in catalog_models):
        reasons.append("catalog_models must contain exact non-empty IDs")

    controller = snapshot.get("controller")
    if not isinstance(controller, dict):
        reasons.append("controller receipt is missing")
        controller = {}
    for key in ("requested_model", "observed_model"):
        if not controller.get(key):
            reasons.append(f"controller.{key} is missing")
    if controller.get("pinned") is not True:
        reasons.append("controller is not pinned")
    if controller.get("exposes_identity") is not True:
        reasons.append("controller identity is not exposed")
    if controller.get("fallback") is not False:
        reasons.append("controller fallback is not explicitly false")
    if controller.get("requested_model") != controller.get("observed_model"):
        reasons.append("controller requested and observed models differ")
    if controller.get("observed_model") not in catalog_models:
        reasons.append("controller observed model is not in the frozen catalog")
    controller_models = snapshot.get("controller_models")
    expected_controller = (
        controller_models.get(profile)
        if isinstance(controller_models, dict)
        else None
    )
    if not isinstance(expected_controller, str) or not expected_controller:
        reasons.append(f"controller_models has no exact model for {profile!r}")
    elif controller.get("requested_model") != expected_controller:
        reasons.append("controller requested model does not match the frozen profile")
    for key in ("effort", "speed"):
        if not isinstance(controller.get(key), str) or not controller.get(key):
            reasons.append(f"controller.{key} is missing")

    role_families = PROFILE_ROLES.get(profile)
    profile_models = snapshot.get("profile_models")
    required_roles = profile_models.get(profile) if isinstance(profile_models, dict) else None
    if role_families is None:
        reasons.append(f"unknown profile {profile!r}")
        role_families = {}
    if not isinstance(required_roles, dict):
        reasons.append(f"profile_models has no exact role mapping for {profile!r}")
        required_roles = {}
    elif not all(isinstance(role, str) and role for role in required_roles):
        reasons.append(f"profile_models has invalid role names for {profile!r}")
        required_roles = {}
    planner_value = snapshot.get("planner_required", False)
    if not isinstance(planner_value, bool):
        reasons.append("planner_required must be boolean when present")
        planner_required = False
    else:
        planner_required = planner_value
    if planner_required:
        role_families = dict(role_families)
        role_families["planner"] = "planner"
        if "planner" not in required_roles:
            reasons.append(f"profile_models has no exact planner model for {profile!r}")
    if set(required_roles) != set(role_families):
        reasons.append(f"profile_models role mapping is incomplete for {profile!r}")
    roles = snapshot.get("roles")
    if not isinstance(roles, dict):
        reasons.append("role receipts are missing")
        roles = {}

    actual_models: dict[str, dict[str, Any]] = {
        "controller": {
            "requested": controller.get("requested_model"),
            "observed": controller.get("observed_model"),
            "effort": controller.get("effort"),
            "speed": controller.get("speed"),
        }
    }
    role_checks: dict[str, dict[str, Any]] = {
        "controller": {
            "pinned": controller.get("pinned"),
            "exposes_identity": controller.get("exposes_identity"),
            "fallback": controller.get("fallback"),
        }
    }
    write_scope_enforcement = "not_applicable"
    for role in role_families:
        receipt = roles.get(role)
        if not isinstance(receipt, dict):
            reasons.append(f"{role} receipt is missing")
            continue
        actual_models[role] = {
            "requested": receipt.get("requested_model"),
            "observed": receipt.get("observed_model"),
            "effort": receipt.get("effort"),
            "speed": receipt.get("speed"),
        }
        role_checks[role] = {
            key: receipt.get(key)
            for key in (
                "fresh_context",
                "structured_handoff",
                "tools",
                "fallback",
                "exposes_identity",
                "readonly",
                "write_scope",
                "scope_enforcement",
            )
        }
        expected_model = required_roles.get(role)
        if not isinstance(expected_model, str) or not expected_model:
            reasons.append(f"{profile}.{role} has no exact model ID")
        if not receipt.get("requested_model") or not receipt.get("observed_model"):
            reasons.append(f"{role} model identity is incomplete")
        elif receipt["requested_model"] != expected_model:
            reasons.append(
                f"{role} requested model {receipt['requested_model']!r} does not match frozen {expected_model!r}"
            )
        elif not model_matches(receipt["observed_model"], expected_model):
            reasons.append(
                f"{role} observed model {receipt['observed_model']!r} does not match frozen {expected_model!r}"
            )
        for key in ("effort", "speed"):
            if not isinstance(receipt.get(key), str) or not receipt.get(key):
                reasons.append(f"{role}.{key} is missing")
        if receipt.get("observed_model") not in catalog_models:
            reasons.append(f"{role} observed model is not in the frozen catalog")
        if receipt.get("requested_model") != receipt.get("observed_model"):
            reasons.append(f"{role} requested and observed models differ")
        for key, expected in (
            ("fresh_context", True),
            ("structured_handoff", True),
            ("tools", True),
            ("fallback", False),
            ("exposes_identity", True),
        ):
            if receipt.get(key) is not expected:
                reasons.append(f"{role}.{key} failed capability check")
        if role in {"critic", "planner"}:
            if receipt.get("readonly") is not True or receipt.get("write_scope") != []:
                reasons.append(f"{role} must be read-only with an empty write scope")
        else:
            write_scope = receipt.get("write_scope")
            if (
                receipt.get("readonly") is not False
                or not isinstance(write_scope, list)
                or not write_scope
                or not all(
                    isinstance(path, str) and path
                    for path in write_scope
                )
            ):
                reasons.append("generator must have write access limited to a declared scope")
        if role == "generator":
            write_scope_enforcement = receipt.get("scope_enforcement")
            if (
                not isinstance(write_scope_enforcement, str)
                or write_scope_enforcement not in {"prompt_only", "host_enforced"}
            ):
                reasons.append(
                    "generator scope_enforcement must be prompt_only or host_enforced"
                )

    warnings = []
    if write_scope_enforcement == "prompt_only":
        warnings.append("generator write scope is prompt-enforced, not a host security boundary")
    return {
        "schema": "actor-critic-mode/capability-receipt/v1",
        "host": host,
        "profile": profile,
        "catalog_snapshot": snapshot.get("catalog_snapshot"),
        "eligible": not reasons,
        "reasons": reasons,
        "warnings": warnings,
        "write_scope_enforcement": write_scope_enforcement,
        "planner_required": planner_required,
        "usage_attribution": snapshot.get("usage_attribution"),
        "role_checks": role_checks,
        "required_roles": ["controller", *sorted(role_families)],
        "actual_models": actual_models,
    }


def self_test() -> None:
    snapshot = {
        "host": "cursor",
        "catalog_snapshot": "self-test-catalog",
        "catalog_models": ["sol-medium", "luna-max", "terra"],
        "fallback": False,
        "profile_models": {
            "cheap-generate-strong-critic-terra": {
                "generator": "luna-max",
                "critic": "terra"
            }
        },
        "controller_models": {
            "cheap-generate-strong-critic-terra": "sol-medium"
        },
        "usage_attribution": True,
        "controller": {
            "requested_model": "sol-medium",
            "observed_model": "sol-medium",
            "pinned": True,
            "exposes_identity": True,
            "fallback": False,
            "effort": "high",
            "speed": "default",
        },
        "roles": {
            "generator": {
                "requested_model": "luna-max",
                "observed_model": "luna-max",
                "fresh_context": True,
                "structured_handoff": True,
                "tools": True,
                "fallback": False,
                "readonly": False,
                "exposes_identity": True,
                "write_scope": ["src/"],
                "scope_enforcement": "prompt_only",
                "effort": "high",
                "speed": "default",
            },
            "critic": {
                "requested_model": "terra",
                "observed_model": "terra",
                "fresh_context": True,
                "structured_handoff": True,
                "tools": True,
                "fallback": False,
                "readonly": True,
                "exposes_identity": True,
                "write_scope": [],
                "effort": "high",
                "speed": "default",
            },
        },
    }
    assert probe(snapshot, "cursor", "cheap-generate-strong-critic-terra")["eligible"]
    snapshot["roles"]["critic"]["fallback"] = True
    assert not probe(snapshot, "cursor", "cheap-generate-strong-critic-terra")["eligible"]
    print("self-test: ok")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", choices=("claude", "codex", "cursor"), required=False)
    parser.add_argument("--profile", choices=sorted(PROFILE_ROLES), required=False)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        self_test()
        return 0
    if not args.host or not args.profile or not args.input:
        parser.error("--host, --profile, and --input are required")
    try:
        snapshot = json.loads(args.input.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"cannot read capability snapshot: {exc}", file=sys.stderr)
        return 1
    if not isinstance(snapshot, dict):
        print("capability snapshot must be a JSON object", file=sys.stderr)
        return 1
    receipt = probe(snapshot, args.host, args.profile)
    text = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if receipt["eligible"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
