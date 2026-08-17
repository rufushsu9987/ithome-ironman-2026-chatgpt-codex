#!/usr/bin/env python3
"""Read-only, deterministic verification gate for a deployed release candidate."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any


class DeploymentVerificationError(ValueError):
    """Raised when an intent or observation is malformed."""


def _string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DeploymentVerificationError(f"{field} must be a non-empty string")
    return value


def _object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise DeploymentVerificationError(f"{field} must be an object")
    return value


def _integer(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise DeploymentVerificationError(f"{field} must be an integer")
    if value < 0:
        raise DeploymentVerificationError(f"{field} must not be negative")
    return value


def _required_identity(value: Any, prefix: str) -> dict[str, str]:
    raw = _object(value, prefix)
    return {
        field: _string(raw.get(field), f"{prefix}.{field}")
        for field in (
            "intent_id",
            "run_id",
            "candidate_id",
            "source_commit",
            "input_digest",
            "environment_id",
            "target",
        )
    }


def _unique_reasons(reasons: list[str]) -> list[str]:
    return list(dict.fromkeys(reasons))


def evaluate_deployment(intent: dict[str, Any], observed: dict[str, Any]) -> dict[str, Any]:
    """Verify serving state without changing either input object."""
    intent_identity = _required_identity(intent, "intent")
    observed_identity = _required_identity(observed, "observed")
    expected = _object(intent.get("expected_deployment"), "intent.expected_deployment")
    expected_artifact_digest = _string(expected.get("artifact_digest"), "intent.expected_deployment.artifact_digest")
    expected_version = _string(expected.get("version"), "intent.expected_deployment.version")
    expected_config_digest = _string(expected.get("config_digest"), "intent.expected_deployment.config_digest")
    expected_replicas = _integer(expected.get("replicas"), "intent.expected_deployment.replicas")

    required_checks_raw = intent.get("required_checks")
    if not isinstance(required_checks_raw, list):
        raise DeploymentVerificationError("intent.required_checks must be a list")
    required_checks = [_string(value, "intent.required_checks item") for value in required_checks_raw]
    if len(set(required_checks)) != len(required_checks):
        raise DeploymentVerificationError("intent.required_checks must not contain duplicates")

    reasons: list[str] = []
    for field, expected_value in intent_identity.items():
        if observed_identity[field] != expected_value:
            reasons.append(f"{field}_mismatch")

    deployment = _object(observed.get("deployment"), "observed.deployment")
    deployment_status = _string(deployment.get("status"), "observed.deployment.status")
    rollout_state = _string(deployment.get("rollout_state"), "observed.deployment.rollout_state")
    deployed_candidate = _string(deployment.get("candidate_id"), "observed.deployment.candidate_id")
    deployed_artifact_digest = _string(deployment.get("artifact_digest"), "observed.deployment.artifact_digest")
    deployed_version = _string(deployment.get("version"), "observed.deployment.version")
    deployed_config_digest = _string(deployment.get("config_digest"), "observed.deployment.config_digest")
    deployed_expected_replicas = _integer(deployment.get("replicas_expected"), "observed.deployment.replicas_expected")
    replicas_ready = _integer(deployment.get("replicas_ready"), "observed.deployment.replicas_ready")

    if observed_identity["target"] != intent_identity["target"]:
        reasons.append("target_mismatch")
    if deployment_status != "available":
        reasons.append("deployment_not_available")
    if rollout_state != "complete":
        reasons.append("rollout_not_complete")
    if deployed_candidate != intent_identity["candidate_id"]:
        reasons.append("deployment_candidate_mismatch")
    if deployed_artifact_digest != expected_artifact_digest:
        reasons.append("deployment_artifact_digest_mismatch")
    if deployed_version != expected_version:
        reasons.append("deployment_version_mismatch")
    if deployed_config_digest != expected_config_digest:
        reasons.append("deployment_config_digest_mismatch")
    if deployed_expected_replicas != expected_replicas:
        reasons.append("deployment_replica_expectation_mismatch")
    if replicas_ready < expected_replicas:
        reasons.append("replica_shortfall")

    checks = _object(observed.get("checks"), "observed.checks")
    for check_name in required_checks:
        result = checks.get(check_name)
        if result is None:
            reasons.append(f"check_missing:{check_name}")
        elif result != "passed":
            reasons.append(f"check_not_passed:{check_name}")

    traffic = _object(observed.get("traffic"), "observed.traffic")
    serving_candidate_id = _string(traffic.get("serving_candidate_id"), "observed.traffic.serving_candidate_id")
    route_state = _string(traffic.get("route_state"), "observed.traffic.route_state")
    if serving_candidate_id != intent_identity["candidate_id"]:
        reasons.append("serving_candidate_mismatch")
    if route_state != "serving":
        reasons.append("traffic_not_serving")

    reasons = _unique_reasons(reasons)
    identity_fields = (
        "intent_id_mismatch",
        "run_id_mismatch",
        "candidate_id_mismatch",
        "source_commit_mismatch",
        "input_digest_mismatch",
        "environment_id_mismatch",
        "target_mismatch",
    )
    deployment_identity_reasons = {
        "deployment_candidate_mismatch",
        "deployment_artifact_digest_mismatch",
        "deployment_version_mismatch",
        "deployment_config_digest_mismatch",
        "deployment_replica_expectation_mismatch",
    }
    return {
        "allowed": not reasons,
        "state": "deployment_verified" if not reasons else "blocked",
        "reasons": reasons,
        "intent": copy.deepcopy(intent),
        "input": copy.deepcopy(observed),
        "checks": {
            "identity": not any(reason in identity_fields for reason in reasons),
            "deployment_status": deployment_status == "available",
            "rollout": rollout_state == "complete",
            "serving_identity": not any(reason in deployment_identity_reasons or reason == "serving_candidate_mismatch" for reason in reasons),
            "required_checks": not any(reason.startswith(("check_missing:", "check_not_passed:")) for reason in reasons),
            "replica_health": replicas_ready >= expected_replicas,
            "traffic": route_state == "serving" and serving_candidate_id == intent_identity["candidate_id"],
            "candidate_id": intent_identity["candidate_id"],
            "run_id": intent_identity["run_id"],
        },
    }


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise DeploymentVerificationError(f"file does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise DeploymentVerificationError(f"invalid JSON: {path}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify a deployed release candidate without changing it")
    parser.add_argument("intent_json", type=Path)
    parser.add_argument("observation_json", type=Path)
    args = parser.parse_args()
    try:
        report = evaluate_deployment(load_json(args.intent_json), load_json(args.observation_json))
    except DeploymentVerificationError as exc:
        parser.error(str(exc))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["allowed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
