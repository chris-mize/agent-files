#!/usr/bin/env python3
"""Score sanitized actor-critic-mode JSONL run records.

The harness never opens task repositories, hidden tests, expected answers, or
private scoring keys. A trusted external harness must reduce those inputs to
the public run-record contract described in references/evaluation.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import statistics
import sys
from collections import defaultdict
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

SCHEMA = "actor-critic-mode/run/v1"
ENVIRONMENT_FIELDS = (
    "task_revision",
    "dependency_lock_hash",
    "tool_versions",
    "fixture_hash",
    "network_policy",
)


def environment_key(environment: dict[str, Any]) -> str:
    payload = {field: environment[field] for field in ENVIRONMENT_FIELDS}
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def is_hash(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def is_real_text(value: Any) -> bool:
    return (
        isinstance(value, str)
        and bool(value.strip())
        and value.strip().lower() not in {"...", "placeholder", "unknown", "todo"}
    )


def is_real_value(value: Any) -> bool:
    if isinstance(value, str):
        return is_real_text(value)
    if isinstance(value, dict):
        return bool(value) and all(
            is_real_value(key) and is_real_value(item) for key, item in value.items()
        )
    return False


def _number(value: Any, field: str) -> tuple[float | None, str | None]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None, f"{field} must be numeric"
    value = float(value)
    if not math.isfinite(value) or value < 0:
        return None, f"{field} must be a finite non-negative number"
    return value, None


def validate_record(record: dict[str, Any], line: int) -> list[str]:
    errors: list[str] = []
    if record.get("schema") != SCHEMA:
        errors.append(f"line {line}: schema must be {SCHEMA}")
    if record.get("run_status") == "unrunnable":
        for key in (
            "run_id",
            "profile",
            "reason",
            "model_receipt",
            "capability_receipt",
            "environment_receipt",
        ):
            if key not in record:
                errors.append(f"line {line}: unrunnable record missing {key}")
        if not isinstance(record.get("reason"), str) or not record.get("reason"):
            errors.append(f"line {line}: unrunnable reason must be non-empty")
        model = record.get("model_receipt")
        if (
            not isinstance(model, dict)
            or not isinstance(model.get("requested"), str)
            or not model.get("requested")
            or model.get("observed") is not None
            or model.get("fallback") is not False
        ):
            errors.append(f"line {line}: invalid unrunnable model receipt")
        if not isinstance(model, dict) or not is_hash(model.get("configuration_hash")):
            errors.append(f"line {line}: invalid unrunnable configuration hash")
        capability = record.get("capability_receipt")
        if (
            not isinstance(capability, dict)
            or capability.get("eligible") is not False
            or not capability.get("catalog_snapshot")
        ):
            errors.append(f"line {line}: invalid unrunnable capability receipt")
        environment = record.get("environment_receipt")
        if not isinstance(environment, dict) or any(
            not environment.get(field) for field in ENVIRONMENT_FIELDS
        ):
            errors.append(f"line {line}: incomplete unrunnable environment receipt")
        elif (
            not isinstance(environment.get("key"), str)
            or not re.fullmatch(r"[0-9a-f]{64}", environment["key"])
            or environment["key"] != environment_key(environment)
            or not is_real_text(environment.get("task_revision"))
            or not is_hash(environment.get("dependency_lock_hash"))
            or not is_real_value(environment.get("tool_versions"))
            or not is_hash(environment.get("fixture_hash"))
            or not is_real_value(environment.get("network_policy"))
        ):
            errors.append(f"line {line}: invalid unrunnable environment hash")
        return errors
    if "run_status" in record and (
        not isinstance(record.get("run_status"), (str, type(None)))
        or record.get("run_status") not in {None, "complete"}
    ):
        errors.append(f"line {line}: invalid run_status")
    required = (
        "run_id",
        "task_id",
        "repetition",
        "profile",
        "model_receipt",
        "environment_receipt",
        "quality",
        "cost",
        "usage",
        "secondary",
        "capability_receipt",
        "call_ledger",
    )
    for key in required:
        if key not in record:
            errors.append(f"line {line}: missing {key}")

    if not isinstance(record.get("run_id"), str) or not record.get("run_id"):
        errors.append(f"line {line}: run_id must be a non-empty string")
    if not isinstance(record.get("task_id"), str) or not record.get("task_id"):
        errors.append(f"line {line}: task_id must be a non-empty string")
    if not isinstance(record.get("profile"), str) or not record.get("profile"):
        errors.append(f"line {line}: profile must be a non-empty string")
    if not isinstance(record.get("repetition"), int) or isinstance(
        record.get("repetition"), bool
    ):
        errors.append(f"line {line}: repetition must be an integer")
    elif record["repetition"] < 1:
        errors.append(f"line {line}: repetition must be positive")

    receipt = record.get("model_receipt")
    if not isinstance(receipt, dict):
        errors.append(f"line {line}: model_receipt must be an object")
    else:
        for key in (
            "requested",
            "observed",
            "effort",
            "speed",
            "host",
            "invocation_mode",
            "configuration_hash",
            "fallback",
        ):
            if key not in receipt:
                errors.append(f"line {line}: model_receipt missing {key}")
        if not isinstance(receipt.get("requested"), str) or not receipt.get(
            "requested"
        ):
            errors.append(f"line {line}: model_receipt.requested must be non-empty")
        if not isinstance(receipt.get("observed"), str) or not receipt.get("observed"):
            errors.append(f"line {line}: model_receipt.observed must be non-empty")
        for key in ("effort", "speed", "host", "invocation_mode"):
            if not isinstance(receipt.get(key), str) or not receipt.get(key):
                errors.append(f"line {line}: model_receipt.{key} must be non-empty")
        if receipt.get("invocation_mode") != "explicit":
            errors.append(f"line {line}: model_receipt.invocation_mode must be explicit")
        if not is_hash(receipt.get("configuration_hash")):
            errors.append(f"line {line}: model_receipt.configuration_hash must be a SHA-256 hash")
        elif receipt.get("requested") != receipt.get("observed"):
            errors.append(f"line {line}: model_receipt requested/observed mismatch")
        if not isinstance(receipt.get("fallback"), bool):
            errors.append(f"line {line}: model_receipt.fallback must be boolean")
        elif receipt["fallback"]:
            errors.append(f"line {line}: model fallback makes named result degraded")
        role_receipts = receipt.get("roles")
        if not isinstance(role_receipts, dict) or "controller" not in role_receipts:
            errors.append(f"line {line}: model_receipt.roles must include controller")
            role_receipts = {}
        for role, role_receipt in role_receipts.items():
            if (
                not isinstance(role_receipt, dict)
                or not role_receipt.get("requested")
                or not role_receipt.get("observed")
                or not role_receipt.get("effort")
                or not role_receipt.get("speed")
            ):
                errors.append(f"line {line}: incomplete model receipt for {role}")
            elif role_receipt["requested"] != role_receipt["observed"]:
                errors.append(f"line {line}: requested/observed mismatch for {role}")
        controller_role = role_receipts.get("controller")
        if isinstance(controller_role, dict):
            for field in ("requested", "observed", "effort", "speed"):
                if receipt.get(field) != controller_role.get(field):
                    errors.append(
                        f"line {line}: top-level model receipt does not match controller"
                    )

    capability = record.get("capability_receipt")
    if not isinstance(capability, dict):
        errors.append(f"line {line}: capability_receipt must be an object")
    else:
        if capability.get("eligible") is not True:
            errors.append(f"line {line}: capability receipt is not eligible")
        if capability.get("profile") != record.get("profile"):
            errors.append(f"line {line}: capability profile does not match run profile")
        if not capability.get("catalog_snapshot"):
            errors.append(f"line {line}: capability catalog snapshot is missing")
        if (
            not isinstance(capability.get("write_scope_enforcement"), str)
            or capability.get("write_scope_enforcement")
            not in {"host_enforced", "prompt_only", "not_applicable"}
        ):
            errors.append(f"line {line}: write scope enforcement posture is missing")
        if capability.get("usage_attribution") is not True:
            errors.append(f"line {line}: capability usage attribution is missing")
        actual_models = capability.get("actual_models")
        role_receipts = receipt.get("roles", {}) if isinstance(receipt, dict) else {}
        if not isinstance(actual_models, dict):
            errors.append(f"line {line}: capability actual_models is missing")
        else:
            required_roles = capability.get("required_roles")
            if (
                not isinstance(required_roles, list)
                or not required_roles
                or not all(isinstance(role, str) and role for role in required_roles)
                or set(required_roles) != set(actual_models)
                or set(required_roles) != set(role_receipts)
            ):
                errors.append(f"line {line}: capability required_roles are incomplete")
                required_roles = []
            role_checks = capability.get("role_checks")
            if (
                not isinstance(role_checks, dict)
                or set(role_checks) != set(required_roles or [])
            ):
                errors.append(f"line {line}: capability role checks are incomplete")
                role_checks = {}
            for role, role_receipt in role_receipts.items():
                actual = actual_models.get(role)
                if (
                    not isinstance(actual, dict)
                    or actual.get("requested") != role_receipt.get("requested")
                    or actual.get("observed") != role_receipt.get("observed")
                    or actual.get("effort") != role_receipt.get("effort")
                    or actual.get("speed") != role_receipt.get("speed")
                ):
                    errors.append(f"line {line}: capability/model receipt mismatch for {role}")
                checks = role_checks.get(role, {})
                if not isinstance(checks, dict):
                    errors.append(f"line {line}: invalid capability checks for {role}")
                elif role == "controller":
                    if (
                        any(checks.get(key) is not True for key in ("pinned", "exposes_identity"))
                        or checks.get("fallback") is not False
                    ):
                        errors.append(f"line {line}: controller capability checks are incomplete")
                else:
                    if any(
                        checks.get(key) is not expected
                        for key, expected in (
                            ("fresh_context", True),
                            ("structured_handoff", True),
                            ("tools", True),
                            ("exposes_identity", True),
                            ("fallback", False),
                        )
                    ):
                        errors.append(f"line {line}: {role} capability checks are incomplete")
                    if role == "generator":
                        write_scope = checks.get("write_scope")
                        if (
                            checks.get("readonly") is not False
                            or not isinstance(write_scope, list)
                            or not write_scope
                            or not all(
                                isinstance(path, str) and path
                                for path in write_scope
                            )
                            or not isinstance(checks.get("scope_enforcement"), str)
                            or checks.get("scope_enforcement")
                            not in {"prompt_only", "host_enforced"}
                        ):
                            errors.append("line: generator capability scope checks are incomplete")
                    elif checks.get("readonly") is not True or checks.get("write_scope") != []:
                        errors.append(f"line: {role} capability permission checks are incomplete")
            generator_receipt = role_receipts.get("generator")
            if isinstance(generator_receipt, dict):
                generator_posture = generator_receipt.get("scope_enforcement")
                if capability.get("write_scope_enforcement") != generator_posture:
                    errors.append(
                        f"line {line}: capability write-scope posture does not match generator"
                    )
            elif capability.get("write_scope_enforcement") != "not_applicable":
                errors.append(
                    f"line {line}: controller-only capability must use not_applicable scope posture"
                )

    ledger = record.get("call_ledger")
    role_receipts_for_ledger = receipt.get("roles", {}) if isinstance(receipt, dict) else {}
    if not isinstance(ledger, list) or not ledger:
        errors.append(f"line {line}: call_ledger must be a non-empty list")
    else:
        for call_number, call in enumerate(ledger, 1):
            if not isinstance(call, dict) or any(
                not call.get(key)
                for key in (
                    "role",
                    "requested_model",
                    "observed_model",
                    "effort",
                    "speed",
                    "status",
                )
            ):
                errors.append(f"line {line}: incomplete call_ledger entry {call_number}")
            elif (
                not isinstance(call["status"], str)
                or call["status"] not in {"ok", "failed", "degraded"}
            ):
                errors.append(f"line {line}: invalid call status {call['status']!r}")
            elif call["role"] not in role_receipts_for_ledger:
                errors.append(f"line {line}: call has no matching role receipt")
            elif call["role"] in role_receipts_for_ledger:
                role_receipt = role_receipts_for_ledger[call["role"]]
                if (
                    call["requested_model"] != role_receipt.get("requested")
                    or call["observed_model"] != role_receipt.get("observed")
                    or call["effort"] != role_receipt.get("effort")
                    or call["speed"] != role_receipt.get("speed")
                ):
                    errors.append(f"line {line}: call/model receipt mismatch for {call['role']}")
        ledger_roles = {
            call.get("role")
            for call in ledger
            if isinstance(call, dict) and call.get("role")
        }
        required_roles = (
            capability.get("required_roles", [])
            if isinstance(capability, dict)
            else []
        )
        if (
            isinstance(required_roles, list)
            and all(isinstance(role, str) and role for role in required_roles)
            and not set(required_roles).issubset(ledger_roles)
        ):
            errors.append(f"line {line}: call_ledger omits a required role")

    environment = record.get("environment_receipt")
    if not isinstance(environment, dict):
        errors.append(f"line {line}: environment_receipt must be an object")
    else:
        for key in ("key", *ENVIRONMENT_FIELDS):
            if not environment.get(key):
                errors.append(f"line {line}: environment_receipt.{key} is missing")
        if (
            not isinstance(environment.get("key"), str)
            or not re.fullmatch(r"[0-9a-f]{64}", environment["key"])
            or not all(environment.get(field) for field in ENVIRONMENT_FIELDS)
            or environment["key"] != environment_key(environment)
            or not is_real_text(environment.get("task_revision"))
            or not is_hash(environment.get("dependency_lock_hash"))
            or not is_real_value(environment.get("tool_versions"))
            or not is_hash(environment.get("fixture_hash"))
            or not is_real_value(environment.get("network_policy"))
        ):
            errors.append(f"line {line}: environment_receipt.key must hash its fields")

    quality = record.get("quality")
    if not isinstance(quality, dict):
        errors.append(f"line {line}: quality must be an object")
    else:
        for key in ("valid_gates", "missed_mandatory", "defects", "regressions", "success"):
            if key not in quality:
                errors.append(f"line {line}: quality missing {key}")
        for key in ("valid_gates", "success"):
            if key in quality and not isinstance(quality[key], bool):
                errors.append(f"line {line}: quality.{key} must be boolean")
        for key in ("missed_mandatory", "defects", "regressions"):
            if key in quality:
                value, error = _number(quality[key], f"quality.{key}")
                if error:
                    errors.append(f"line {line}: {error}")
                elif value != int(value):
                    errors.append(f"line {line}: quality.{key} must be an integer")

    cost = record.get("cost")
    if not isinstance(cost, dict):
        errors.append(f"line {line}: cost must be an object")
    else:
        if not isinstance(cost.get("pool"), str) or not cost.get("pool"):
            errors.append(f"line {line}: cost.pool must be non-empty")
        if "units" not in cost:
            errors.append(f"line {line}: cost missing units")
        else:
            _, error = _number(cost["units"], "cost.units")
            if error:
                errors.append(f"line {line}: {error}")

    usage = record.get("usage")
    if not isinstance(usage, dict):
        errors.append(f"line {line}: usage must be an object")
    else:
        for key in ("latency_ms", "input_tokens", "output_tokens", "role_calls"):
            if key not in usage:
                errors.append(f"line {line}: usage missing {key}")
            else:
                value, error = _number(usage[key], f"usage.{key}")
                if error:
                    errors.append(f"line {line}: {error}")
                elif value != int(value):
                    errors.append(f"line {line}: usage.{key} must be an integer")
        if (
            isinstance(ledger, list)
            and "role_calls" in usage
            and isinstance(usage["role_calls"], (int, float))
            and not isinstance(usage["role_calls"], bool)
            and int(usage["role_calls"]) != len(ledger)
        ):
            errors.append(f"line {line}: usage.role_calls must match call_ledger length")

    secondary = record.get("secondary")
    if not isinstance(secondary, dict):
        errors.append(f"line {line}: secondary must be an object")
    else:
        for key in (
            "reviewer_precision",
            "proposal_coverage",
            "critic_soundness",
        ):
            value, error = _number(secondary.get(key), f"secondary.{key}")
            if error:
                errors.append(f"line {line}: {error}")
            elif value > 1:
                errors.append(f"line {line}: secondary.{key} must be at most 1")
        if (
            not isinstance(secondary.get("revision_direction"), str)
            or secondary.get("revision_direction")
            not in {
                "incorrect_to_correct",
                "correct_to_incorrect",
                "unchanged",
                "not_applicable",
            }
        ):
            errors.append(f"line {line}: invalid secondary.revision_direction")
        iterations, error = _number(secondary.get("iterations"), "secondary.iterations")
        if error:
            errors.append(f"line {line}: {error}")
        elif iterations != int(iterations):
            errors.append(f"line {line}: secondary.iterations must be an integer")

    if "human_intervention" not in record:
        errors.append(f"line {line}: human_intervention is required")
    elif not isinstance(record["human_intervention"], bool):
        errors.append(f"line {line}: human_intervention must be boolean")
    return errors


def load_records(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    try:
        handle = path.open(encoding="utf-8")
    except OSError as exc:
        return [], [f"cannot read {path}: {exc}"]

    with handle:
        for line_number, raw in enumerate(handle, 1):
            if not raw.strip():
                continue
            try:
                value = json.loads(raw)
            except json.JSONDecodeError as exc:
                errors.append(f"line {line_number}: invalid JSON: {exc.msg}")
                continue
            if not isinstance(value, dict):
                errors.append(f"line {line_number}: record must be a JSON object")
                continue
            errors.extend(validate_record(value, line_number))
            records.append(value)

    seen: dict[tuple[Any, ...], str] = {}

    def dedupe_value(value: Any) -> Any:
        try:
            hash(value)
        except TypeError:
            return repr(value)
        return value

    for record in records:
        if record.get("run_status") == "unrunnable":
            key = ("__unrunnable__", 0, dedupe_value(record.get("profile", "")))
        else:
            key = (
                dedupe_value(record.get("task_id", "")),
                dedupe_value(record.get("repetition", 0)),
                dedupe_value(record.get("profile", "")),
            )
        prior = seen.get(key)
        if prior:
            errors.append(
                f"duplicate task/repetition/profile {key}: {prior} and {record.get('run_id')}"
            )
        else:
            seen[key] = str(record.get("run_id"))
    return records, errors


def load_manifest(path: Path) -> tuple[dict[str, Any], list[str]]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {}, [f"cannot read study manifest {path}: {exc}"]
    if not isinstance(value, dict):
        return {}, ["study manifest must be a JSON object"]
    return value, []


def validate_manifest(
    manifest: dict[str, Any],
    records: Sequence[dict[str, Any]],
    candidate: str,
    baseline: str,
    scaffold: str | None,
    expected_repetitions: int,
) -> list[str]:
    errors: list[str] = []
    if manifest.get("schema") != "study-manifest/v1":
        errors.append("manifest schema must be study-manifest/v1")
    if (
        not isinstance(manifest.get("phase"), str)
        or manifest.get("phase") not in {"development", "holdout"}
    ):
        errors.append("manifest phase must be development or holdout")
    task_ids = manifest.get("task_ids")
    if (
        not isinstance(task_ids, list)
        or len(task_ids) != 4
        or not all(isinstance(task_id, str) and task_id for task_id in task_ids)
        or len(set(task_ids)) != 4
    ):
        errors.append("manifest must contain exactly four unique task_ids")
        task_ids = []
    if expected_repetitions != 3 or manifest.get("repetitions") != 3:
        errors.append("named evaluation requires exactly three repetitions")
    profiles = manifest.get("profiles")
    required_profiles = {candidate, baseline}
    if scaffold:
        required_profiles.add(scaffold)
    if (
        not isinstance(profiles, list)
        or not all(isinstance(profile, str) and profile for profile in profiles)
        or len(profiles) != len(set(profiles))
        or set(profiles) != required_profiles
    ):
        errors.append("manifest profiles must exactly match the requested comparison arms")
    profile_models = manifest.get("profile_models")
    if (
        not isinstance(profile_models, dict)
        or set(profile_models) != required_profiles
        or any(
            not isinstance(profile_models.get(profile), dict)
            or not profile_models[profile]
            or any(not is_real_text(model) for model in profile_models[profile].values())
            for profile in required_profiles
        )
    ):
        errors.append("manifest must freeze exact model IDs for every comparison arm")
        profile_models = {}
    if not is_real_text(manifest.get("catalog_snapshot")):
        errors.append("manifest catalog_snapshot is missing")
    if not is_hash(manifest.get("configuration_hash")):
        errors.append("manifest configuration_hash must be a SHA-256 hash")
    budget = manifest.get("budget")
    if (
        not isinstance(budget, dict)
        or budget.get("max_revisions") != 2
        or budget.get("max_role_calls") != 8
    ):
        errors.append("manifest must freeze the two-revision/eight-call budget")
    budget_limits = budget if isinstance(budget, dict) else {}
    if (
        not isinstance(manifest.get("write_scope_enforcement"), str)
        or manifest.get("write_scope_enforcement")
        not in {"host_enforced", "prompt_only", "not_applicable"}
    ):
        errors.append("manifest write_scope_enforcement is missing")
    scope_postures = manifest.get("scope_postures")
    if (
        not isinstance(scope_postures, dict)
        or set(scope_postures) != required_profiles
        or any(
            not isinstance(posture, str)
            or posture not in {"host_enforced", "prompt_only", "not_applicable"}
            for posture in scope_postures.values()
        )
    ):
        errors.append("manifest must freeze write-scope posture for every arm")
        scope_postures = {}
    partition = manifest.get("partition")
    if not isinstance(partition, dict):
        errors.append("manifest partition is missing")
        partition = {}
    development_tasks = partition.get("development_task_ids")
    holdout_tasks = partition.get("holdout_task_ids")
    valid_partition = (
        isinstance(development_tasks, list)
        and isinstance(holdout_tasks, list)
        and len(development_tasks) == 4
        and len(holdout_tasks) == 4
        and all(isinstance(task_id, str) and task_id for task_id in development_tasks)
        and all(isinstance(task_id, str) and task_id for task_id in holdout_tasks)
        and len(set(development_tasks)) == 4
        and len(set(holdout_tasks)) == 4
        and set(development_tasks).isdisjoint(set(holdout_tasks))
    )
    if not valid_partition:
        errors.append("manifest must declare disjoint four-task development and holdout partitions")
    elif set(task_ids) != set(
        development_tasks
        if manifest.get("phase") == "development"
        else holdout_tasks
    ):
        errors.append("phase task_ids do not match the declared partition")

    scorer = manifest.get("scorer_receipt")
    if (
        not isinstance(scorer, dict)
        or scorer.get("fresh") is not True
        or scorer.get("blinded") is not True
        or scorer.get("participated_in_arms") is not False
        or not is_hash(scorer.get("rubric_hash"))
    ):
        errors.append("manifest scorer receipt is not independent and blinded")
    sanitization = manifest.get("sanitization")
    if (
        not isinstance(sanitization, dict)
        or sanitization.get("randomized") is not True
        or sanitization.get("strips_profile") is not True
        or sanitization.get("strips_receipts") is not True
    ):
        errors.append("manifest sanitization receipt is incomplete")
    isolation = manifest.get("isolation")
    scope_enforcement = manifest.get("write_scope_enforcement")
    if not isinstance(isolation, dict) or (
        isolation.get("hidden_tests_outside_workspace") is not True
        or isolation.get("trusted_harness_only") is not True
        or (
            scope_enforcement == "host_enforced"
            and isolation.get("deny_probe_passed") is not True
        )
        or (
            scope_enforcement == "prompt_only"
            and isolation.get("deny_probe_passed") is not False
        )
    ):
        errors.append("manifest hidden-test isolation receipt is incomplete")
    else:
        probes = isolation.get("deny_probes")
        required_probe_roles = {"controller", "generator", "critic", "planner", "scorer"}
        if not isinstance(probes, dict) or set(probes) != required_probe_roles:
            errors.append("manifest must include denial probes for every role")
        else:
            for role, probe in probes.items():
                if (
                    not isinstance(probe, dict)
                    or probe.get("tool_access_checked") is not True
                    or not is_hash(probe.get("receipt_hash"))
                ):
                    errors.append(f"manifest denial probe is incomplete for {role}")
                elif role == "generator" and scope_enforcement == "prompt_only":
                    if probe.get("passed") is not False or probe.get("host_enforced") is not False:
                        errors.append("prompt-only generator probe must be explicitly unverified")
                elif probe.get("passed") is not True or probe.get("host_enforced") is not True:
                    errors.append(f"manifest denial probe is not host-enforced for {role}")

    for profile in required_profiles:
        profile_records = [record for record in records if record.get("profile") == profile]
        unrunnable = [
            record for record in profile_records if record.get("run_status") == "unrunnable"
        ]
        runnable = [
            record for record in profile_records if record.get("run_status") != "unrunnable"
        ]
        if unrunnable:
            if len(unrunnable) != 1 or runnable:
                errors.append(f"{profile} has an invalid unrunnable arm record")
            records_to_check = unrunnable
        else:
            actual_tasks = {
                record.get("task_id")
                for record in runnable
                if isinstance(record.get("task_id"), str)
            }
            if actual_tasks != set(task_ids):
                errors.append(f"{profile} task IDs do not exactly match the manifest")
            if len(runnable) != len(task_ids) * expected_repetitions:
                errors.append(f"{profile} does not have the complete repetition matrix")
            records_to_check = runnable
        for record in records_to_check:
            capability_value = record.get("capability_receipt", {})
            capability = capability_value if isinstance(capability_value, dict) else {}
            if capability.get("catalog_snapshot") != manifest.get("catalog_snapshot"):
                errors.append(f"{profile} has a catalog snapshot mismatch")
            if capability.get("write_scope_enforcement") != scope_postures.get(profile):
                errors.append(f"{profile} has a write-scope posture mismatch")
            role_checks = capability.get("role_checks", {})
            generator_checks = (
                role_checks.get("generator")
                if isinstance(role_checks, dict)
                else None
            )
            expected_posture = (
                generator_checks.get("scope_enforcement")
                if isinstance(generator_checks, dict)
                else "not_applicable"
            )
            if capability.get("write_scope_enforcement") != expected_posture:
                errors.append(f"{profile} has a role/posture mismatch")
            model = record.get("model_receipt", {})
            if not isinstance(model, dict) or model.get("configuration_hash") != manifest.get(
                "configuration_hash"
            ):
                errors.append(f"{profile} has a configuration mismatch")
            if record.get("run_status") != "unrunnable":
                expected_models = profile_models.get(profile, {})
                actual_models = capability.get("actual_models", {})
                if not isinstance(actual_models, dict):
                    errors.append(f"{profile} actual model receipt is malformed")
                    actual_ids = {}
                else:
                    actual_ids = {
                        role: value.get("observed")
                        for role, value in actual_models.items()
                        if isinstance(value, dict)
                    }
                if actual_ids != expected_models:
                    errors.append(f"{profile} role models do not match the frozen arm")
            if record.get("run_status") != "unrunnable":
                usage_value = record.get("usage", {})
                secondary_value = record.get("secondary", {})
                usage = usage_value if isinstance(usage_value, dict) else {}
                secondary = (
                    secondary_value
                    if isinstance(secondary_value, dict)
                    else {}
                )
                if usage.get("role_calls", 0) > budget_limits.get("max_role_calls", 0):
                    errors.append(f"{profile} exceeds the role-call budget")
                if secondary.get("iterations", 0) > budget_limits.get("max_revisions", 0):
                    errors.append(f"{profile} exceeds the revision budget")
    return errors


def _calls_ok(record: dict[str, Any]) -> bool:
    ledger = record.get("call_ledger")
    return isinstance(ledger, list) and all(
        isinstance(call, dict) and call.get("status") == "ok"
        for call in ledger
    )


def _valid_success(record: dict[str, Any]) -> bool:
    quality = record["quality"]
    return (
        not record.get("human_intervention", False)
        and _calls_ok(record)
        and quality["valid_gates"]
        and quality["success"]
        and quality["missed_mandatory"] == 0
        and quality["defects"] == 0
        and quality["regressions"] == 0
    )


def _quality_key(record: dict[str, Any]) -> tuple[int, int, int]:
    quality = record["quality"]
    if (
        record.get("human_intervention", False)
        or not _calls_ok(record)
        or not quality["valid_gates"]
        or not quality["success"]
    ):
        return (0, 0, 0)
    missed = int(quality["missed_mandatory"])
    defects = int(quality["defects"]) + int(quality["regressions"])
    return 1, -missed, -defects


def _outcome(candidate: dict[str, Any], baseline: dict[str, Any]) -> str:
    candidate_key = _quality_key(candidate)
    baseline_key = _quality_key(baseline)
    if candidate_key > baseline_key:
        return "win"
    if candidate_key < baseline_key:
        return "loss"
    return "tie"


def _cost_per_success(records: Sequence[dict[str, Any]]) -> float | None:
    total = sum(float(record["cost"]["units"]) for record in records)
    successes = sum(1 for record in records if _valid_success(record))
    if successes == 0:
        return None
    return total / successes


def _median(values: Sequence[float | None]) -> float | None:
    if not values or any(value is None or not math.isfinite(value) for value in values):
        return None
    return float(statistics.median([value for value in values if value is not None]))


def index_records(
    records: Iterable[dict[str, Any]],
) -> dict[tuple[str, str, int], dict[str, Any]]:
    return {
        (record["profile"], record["task_id"], record["repetition"]): record
        for record in records
    }


def usage_summary(records: Sequence[dict[str, Any]]) -> dict[str, Any]:
    usable: list[tuple[dict[str, Any], float, int, int, int]] = []
    for record in records:
        usage = record.get("usage")
        if not isinstance(usage, dict) or any(
            key not in usage
            for key in ("latency_ms", "input_tokens", "output_tokens", "role_calls")
        ):
            continue
        try:
            latency = float(usage["latency_ms"])
            input_tokens = int(usage["input_tokens"])
            output_tokens = int(usage["output_tokens"])
            role_calls = int(usage["role_calls"])
        except (TypeError, ValueError, OverflowError):
            continue
        if (
            not math.isfinite(latency)
            or latency < 0
            or input_tokens < 0
            or output_tokens < 0
            or role_calls < 0
            or any(
                isinstance(usage[key], bool)
                or not isinstance(usage[key], (int, float))
                or usage[key] != int(usage[key])
                for key in ("input_tokens", "output_tokens", "role_calls")
            )
        ):
            continue
        usable.append((record, latency, input_tokens, output_tokens, role_calls))
    latency = [item[1] for item in usable]
    input_tokens = sum(item[2] for item in usable)
    output_tokens = sum(item[3] for item in usable)
    role_calls = sum(item[4] for item in usable)
    return {
        "runs": len(usable),
        "invalid_records": len(records) - len(usable),
        "latency_ms_total": sum(latency),
        "latency_ms_mean": (sum(latency) / len(latency)) if latency else None,
        "input_tokens_total": input_tokens,
        "output_tokens_total": output_tokens,
        "tokens_total": input_tokens + output_tokens,
        "role_calls_total": role_calls,
    }


def secondary_summary(records: Sequence[dict[str, Any]]) -> dict[str, Any]:
    usable: list[tuple[dict[str, Any], float, float, float, str, int]] = []
    valid_directions = {
        "incorrect_to_correct",
        "correct_to_incorrect",
        "unchanged",
        "not_applicable",
    }
    for record in records:
        secondary = record.get("secondary")
        if not isinstance(secondary, dict):
            continue
        try:
            precision = float(secondary["reviewer_precision"])
            coverage = float(secondary["proposal_coverage"])
            soundness = float(secondary["critic_soundness"])
            iterations = int(secondary["iterations"])
        except (KeyError, TypeError, ValueError, OverflowError):
            continue
        if (
            any(
                not math.isfinite(value) or value < 0 or value > 1
                for value in (precision, coverage, soundness)
            )
            or iterations < 0
            or isinstance(secondary["iterations"], bool)
            or not isinstance(secondary["iterations"], (int, float))
            or secondary["iterations"] != iterations
            or secondary.get("revision_direction") not in valid_directions
        ):
            continue
        usable.append(
            (
                record,
                precision,
                coverage,
                soundness,
                secondary["revision_direction"],
                iterations,
            )
        )
    direction_counts = defaultdict(int)
    for item in usable:
        direction_counts[item[4]] += 1
    return {
        "runs": len(usable),
        "invalid_records": len(records) - len(usable),
        "reviewer_precision_mean": (
            sum(item[1] for item in usable)
            / len(usable)
            if usable
            else None
        ),
        "proposal_coverage_mean": (
            sum(item[2] for item in usable)
            / len(usable)
            if usable
            else None
        ),
        "critic_soundness_mean": (
            sum(item[3] for item in usable)
            / len(usable)
            if usable
            else None
        ),
        "revision_direction_counts": dict(sorted(direction_counts.items())),
        "iterations_total": sum(item[5] for item in usable),
        "iterations_mean": (
            sum(item[5] for item in usable) / len(usable)
            if usable
            else None
        ),
    }


def compare_pair(
    records: Sequence[dict[str, Any]],
    candidate_profile: str,
    baseline_profile: str,
    expected_repetitions: int,
    min_net_wins: int,
    cost_gate: bool,
) -> dict[str, Any]:
    candidate = [
        record
        for record in records
        if record["profile"] == candidate_profile
    ]
    baseline = [
        record
        for record in records
        if record["profile"] == baseline_profile
    ]
    candidate_by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    baseline_by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in candidate:
        candidate_by_task[record["task_id"]].append(record)
    for record in baseline:
        baseline_by_task[record["task_id"]].append(record)

    task_ids = sorted(set(candidate_by_task) | set(baseline_by_task))
    task_results: list[dict[str, Any]] = []
    wins = losses = ties = 0
    pair_issues: list[str] = []
    cost_issues: list[str] = []
    candidate_costs: list[float | None] = []
    baseline_costs: list[float | None] = []

    for task_id in task_ids:
        candidates = sorted(candidate_by_task.get(task_id, []), key=lambda item: item["repetition"])
        baselines = sorted(baseline_by_task.get(task_id, []), key=lambda item: item["repetition"])
        repetitions = list(range(1, expected_repetitions + 1))
        outcomes: list[str] = []
        task_issues: list[str] = []
        candidate_reps = {record["repetition"]: record for record in candidates}
        baseline_reps = {record["repetition"]: record for record in baselines}

        if len(candidates) != expected_repetitions:
            task_issues.append(
                f"{candidate_profile} has {len(candidates)} repetitions; expected {expected_repetitions}"
            )
        if len(baselines) != expected_repetitions:
            task_issues.append(
                f"{baseline_profile} has {len(baselines)} repetitions; expected {expected_repetitions}"
            )

        for repetition in repetitions:
            left = candidate_reps.get(repetition)
            right = baseline_reps.get(repetition)
            if left is None or right is None:
                task_issues.append(f"missing paired repetition {repetition}")
                continue
            if left["environment_receipt"]["key"] != right["environment_receipt"]["key"]:
                task_issues.append(f"environment mismatch at repetition {repetition}")
                continue
            outcomes.append(_outcome(left, right))

        if task_issues:
            pair_issues.extend(f"{task_id}: {issue}" for issue in task_issues)
            majority = "inconclusive"
        else:
            wins_for_task = outcomes.count("win")
            losses_for_task = outcomes.count("loss")
            ties_for_task = outcomes.count("tie")
            if wins_for_task > expected_repetitions // 2:
                majority = "win"
                wins += 1
            elif losses_for_task > expected_repetitions // 2:
                majority = "loss"
                losses += 1
            else:
                majority = "tie"
                ties += 1
            assert wins_for_task + losses_for_task + ties_for_task == expected_repetitions

        candidate_task_records = list(candidate_by_task.get(task_id, []))
        baseline_task_records = list(baseline_by_task.get(task_id, []))
        candidate_cost = _cost_per_success(candidate_task_records)
        baseline_cost = _cost_per_success(baseline_task_records)
        candidate_costs.append(candidate_cost)
        baseline_costs.append(baseline_cost)
        task_results.append(
            {
                "task_id": task_id,
                "repetition_outcomes": outcomes,
                "majority": majority,
                "candidate_cost_per_success": candidate_cost,
                "baseline_cost_per_success": baseline_cost,
                "issues": task_issues,
            }
        )

    candidate_pools = {record["cost"]["pool"] for record in candidate}
    baseline_pools = {record["cost"]["pool"] for record in baseline}
    if candidate_pools != baseline_pools or len(candidate_pools) != 1:
        cost_issues.append(
            f"non-comparable cost pools: {sorted(candidate_pools)} vs {sorted(baseline_pools)}"
        )

    candidate_median = _median(candidate_costs)
    baseline_median = _median(baseline_costs)
    if candidate_median is None or baseline_median is None:
        cost_issues.append("a task has zero successful repetitions; cost is inconclusive")
    net_wins = wins - losses
    cost_comparable = not cost_issues
    status = "inconclusive" if pair_issues or not task_results else "measured"
    quality_qualified = status == "measured" and net_wins >= min_net_wins
    cost_qualified = (
        cost_comparable
        and candidate_median is not None
        and baseline_median is not None
        and candidate_median < baseline_median
    )
    if quality_qualified and (not cost_gate or cost_qualified):
        qualification = "qualified"
    elif status == "inconclusive" or (cost_gate and not cost_comparable):
        qualification = "inconclusive"
    else:
        qualification = "not_qualified"

    return {
        "candidate": candidate_profile,
        "baseline": baseline_profile,
        "tasks": task_results,
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "net_wins": net_wins,
        "candidate_median_cost_per_success": candidate_median,
        "baseline_median_cost_per_success": baseline_median,
        "cost_comparable": cost_comparable,
        "issues": pair_issues,
        "cost_issues": cost_issues,
        "cost_gate": cost_gate,
        "cost_status": "measured" if cost_comparable else "inconclusive",
        "status": status,
        "qualification": qualification,
    }


def safety_status(records: Sequence[dict[str, Any]]) -> str:
    postures = {
        record.get("capability_receipt", {}).get("write_scope_enforcement")
        for record in records
        if isinstance(record.get("capability_receipt"), dict)
    }
    if postures == {"host_enforced"}:
        return "host_enforced"
    if "prompt_only" in postures:
        return "degraded_prompt_only"
    if postures == {"not_applicable"}:
        return "not_applicable"
    return "unknown"


def evaluate(
    records: Sequence[dict[str, Any]],
    candidate: str,
    baseline: str,
    scaffold: str | None,
    expected_repetitions: int,
    min_net_wins: int,
    input_errors: Sequence[str],
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    profiles = sorted(
        {
            record.get("profile")
            for record in records
            if isinstance(record.get("profile"), str)
        }
    )
    usage = {
        profile: usage_summary(
            [record for record in records if record.get("profile") == profile]
        )
        for profile in profiles
    }
    secondary = {
        profile: secondary_summary(
            [record for record in records if record.get("profile") == profile]
        )
        for profile in profiles
    }
    if input_errors:
        return {
            "schema": "actor-critic-mode/evaluation-report/v1",
            "candidate": candidate,
            "baseline": baseline,
            "scaffold": scaffold,
            "expected_repetitions": expected_repetitions,
            "min_net_wins": min_net_wins,
            "input_errors": list(input_errors),
            "study_manifest": {
                "phase": (manifest or {}).get("phase"),
                "catalog_snapshot": (manifest or {}).get("catalog_snapshot"),
            },
            "safety_status": safety_status(records),
            "pair": None,
            "scaffold_pair": None,
            "usage": usage,
            "secondary": secondary,
            "decision": "inconclusive",
        }

    target_profiles = {candidate, baseline} | ({scaffold} if scaffold else set())
    unrunnable = [
        {
            "profile": record.get("profile"),
            "reason": record.get("reason"),
            "catalog_snapshot": record.get("capability_receipt", {}).get(
                "catalog_snapshot"
            ),
        }
        for record in records
        if record.get("run_status") == "unrunnable"
        and record.get("profile") in target_profiles
    ]
    if unrunnable:
        return {
            "schema": "actor-critic-mode/evaluation-report/v1",
            "candidate": candidate,
            "baseline": baseline,
            "scaffold": scaffold,
            "expected_repetitions": expected_repetitions,
            "min_net_wins": min_net_wins,
            "input_errors": [],
            "study_manifest": {
                "phase": (manifest or {}).get("phase"),
                "catalog_snapshot": (manifest or {}).get("catalog_snapshot"),
            },
            "safety_status": safety_status(records),
            "unrunnable_profiles": unrunnable,
            "pair": None,
            "scaffold_pair": None,
            "usage": usage,
            "secondary": secondary,
            "decision": "not_confirmed",
        }

    pair = compare_pair(
        records,
        candidate,
        baseline,
        expected_repetitions,
        min_net_wins,
        True,
    )
    scaffold_pair = None
    if scaffold:
        scaffold_pair = compare_pair(
            records,
            candidate,
            scaffold,
            expected_repetitions,
            min_net_wins,
            False,
        )

    report: dict[str, Any] = {
        "schema": "actor-critic-mode/evaluation-report/v1",
        "candidate": candidate,
        "baseline": baseline,
        "scaffold": scaffold,
        "expected_repetitions": expected_repetitions,
        "min_net_wins": min_net_wins,
        "input_errors": list(input_errors),
        "study_manifest": {
            "phase": (manifest or {}).get("phase"),
            "catalog_snapshot": (manifest or {}).get("catalog_snapshot"),
        },
        "safety_status": safety_status(records),
        "pair": pair,
        "scaffold_pair": scaffold_pair,
        "usage": usage,
        "secondary": secondary,
    }
    if scaffold_pair is None:
        report["decision"] = pair["qualification"]
    elif pair["qualification"] == "qualified" and scaffold_pair["qualification"] == "qualified":
        report["decision"] = "qualified"
    elif pair["status"] == "inconclusive" or scaffold_pair["status"] == "inconclusive":
        report["decision"] = "inconclusive"
    else:
        report["decision"] = "not_qualified"
    return report


def _synthetic_record(
    profile: str,
    task_id: str,
    repetition: int,
    success: bool,
    missed: int,
    units: float,
) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "run_id": f"{profile}-{task_id}-{repetition}",
        "task_id": task_id,
        "repetition": repetition,
        "profile": profile,
        "model_receipt": {
            "requested": "sol",
            "observed": "sol",
            "effort": "high",
            "speed": "default",
            "host": "self-test-host",
            "invocation_mode": "explicit",
            "configuration_hash": "a" * 64,
            "fallback": False,
            "roles": {
                "controller": {
                    "requested": "sol",
                    "observed": "sol",
                    "effort": "high",
                    "speed": "default",
                }
            },
        },
        "capability_receipt": {
            "eligible": True,
            "profile": profile,
            "catalog_snapshot": "self-test-catalog",
            "write_scope_enforcement": "not_applicable",
            "required_roles": ["controller"],
            "usage_attribution": True,
            "role_checks": {
                "controller": {
                    "pinned": True,
                    "exposes_identity": True,
                    "fallback": False,
                }
            },
            "actual_models": {
                "controller": {
                    "requested": "sol",
                    "observed": "sol",
                    "effort": "high",
                    "speed": "default",
                }
            },
        },
        "call_ledger": [
            {
                "role": "controller",
                "requested_model": "sol",
                "observed_model": "sol",
                "effort": "high",
                "speed": "default",
                "status": "ok",
            }
        ],
        "environment_receipt": {
            "key": environment_key(
                {
                    "task_revision": "self-test-revision",
                    "dependency_lock_hash": "d" * 64,
                    "tool_versions": {"python": "self-test"},
                    "fixture_hash": "f" * 64,
                    "network_policy": "deny",
                }
            ),
            "task_revision": "self-test-revision",
            "dependency_lock_hash": "d" * 64,
            "tool_versions": {"python": "self-test"},
            "fixture_hash": "f" * 64,
            "network_policy": "deny",
        },
        "quality": {
            "valid_gates": True,
            "missed_mandatory": missed,
            "defects": 0,
            "regressions": 0,
            "success": success,
        },
        "cost": {"pool": "self-test-pool", "units": units},
        "usage": {
            "latency_ms": 1000.0,
            "input_tokens": 100,
            "output_tokens": 50,
            "role_calls": 1,
        },
        "secondary": {
            "reviewer_precision": 1.0,
            "proposal_coverage": 1.0,
            "critic_soundness": 1.0,
            "revision_direction": "not_applicable",
            "iterations": 0,
        },
        "human_intervention": False,
    }


def self_test() -> None:
    records: list[dict[str, Any]] = []
    for task_number in range(1, 5):
        task_id = f"dev-{task_number:02d}"
        for repetition in range(1, 4):
            records.append(
                _synthetic_record(
                    "candidate",
                    task_id,
                    repetition,
                    True,
                    0,
                    1.0,
                )
            )
            baseline_success = repetition == 1
            records.append(
                _synthetic_record(
                    "baseline",
                    task_id,
                    repetition,
                    baseline_success,
                    0 if baseline_success else 1,
                    2.0,
                )
            )
            scaffold_success = repetition == 1
            records.append(
                _synthetic_record(
                    "scaffold",
                    task_id,
                    repetition,
                    scaffold_success,
                    0 if scaffold_success else 1,
                    1.5,
                )
            )

    report = evaluate(records, "candidate", "baseline", "scaffold", 3, 2, [])
    if report["decision"] != "qualified":
        raise AssertionError(json.dumps(report, indent=2))
    mismatch = list(records)
    mismatch[0] = dict(mismatch[0])
    mismatch[0]["environment_receipt"] = {"key": "wrong-fixture"}
    mismatch_report = evaluate(mismatch, "candidate", "baseline", None, 3, 2, [])
    if mismatch_report["decision"] != "inconclusive":
        raise AssertionError("environment mismatch was not inconclusive")
    print("self-test: ok")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="sanitized JSONL run records")
    parser.add_argument("--manifest", type=Path, help="frozen study manifest")
    parser.add_argument("--output", type=Path, help="write JSON report here")
    parser.add_argument("--candidate", required=False, help="candidate profile")
    parser.add_argument("--baseline", required=False, help="baseline profile")
    parser.add_argument("--scaffold", help="matching scaffold profile")
    parser.add_argument("--expected-repetitions", type=int, default=3)
    parser.add_argument("--min-net-wins", type=int, default=2)
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.self_test:
        self_test()
        return 0
    if (
        not args.input
        or not args.manifest
        or not args.candidate
        or not args.baseline
        or not args.scaffold
    ):
        print(
            "--input, --manifest, --candidate, --baseline, and --scaffold are required unless --self-test is used",
            file=sys.stderr,
        )
        return 2
    if args.expected_repetitions != 3 or args.min_net_wins != 2:
        print("named evaluation requires exactly three repetitions and two net wins", file=sys.stderr)
        return 2

    records, errors = load_records(args.input)
    manifest, manifest_errors = load_manifest(args.manifest)
    errors.extend(manifest_errors)
    if not manifest_errors:
        errors.extend(
            validate_manifest(
                manifest,
                records,
                args.candidate,
                args.baseline,
                args.scaffold,
                args.expected_repetitions,
            )
        )
    report = evaluate(
        records,
        args.candidate,
        args.baseline,
        args.scaffold,
        args.expected_repetitions,
        args.min_net_wins,
        errors,
        manifest,
    )
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        try:
            args.output.write_text(encoded, encoding="utf-8")
        except OSError as exc:
            print(f"cannot write {args.output}: {exc}", file=sys.stderr)
            return 1
    else:
        print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
