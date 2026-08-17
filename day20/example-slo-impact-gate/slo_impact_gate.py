#!/usr/bin/env python3
"""Read-only, deterministic gate for checking whether a change harmed user-facing SLOs."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any


class SloImpactGateError(ValueError):
    """Raised when an intent or observation is malformed."""


def _string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SloImpactGateError(f"{field} must be a non-empty string")
    return value


def _object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SloImpactGateError(f"{field} must be an object")
    return value


def _number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SloImpactGateError(f"{field} must be a number")
    if value < 0:
        raise SloImpactGateError(f"{field} must not be negative")
    return float(value)


def _identity(value: Any, prefix: str) -> dict[str, str]:
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


def evaluate_impact(intent: dict[str, Any], observed: dict[str, Any]) -> dict[str, Any]:
    """Evaluate user-facing impact without mutating either input object."""
    intent_identity = _identity(intent, "intent")
    observed_identity = _identity(observed, "observed")
    reasons: list[str] = []

    for field, expected in intent_identity.items():
        if observed_identity[field] != expected:
            reasons.append(f"{field}_mismatch")

    window_policy = _object(intent.get("observation_window"), "intent.observation_window")
    minimum_seconds = _number(window_policy.get("minimum_seconds"), "intent.observation_window.minimum_seconds")
    minimum_samples = _number(window_policy.get("minimum_samples"), "intent.observation_window.minimum_samples")
    if not minimum_samples.is_integer():
        raise SloImpactGateError("intent.observation_window.minimum_samples must be an integer")
    minimum_samples = int(minimum_samples)

    window = _object(observed.get("observation_window"), "observed.observation_window")
    window_state = _string(window.get("state"), "observed.observation_window.state")
    duration_seconds = _number(window.get("duration_seconds"), "observed.observation_window.duration_seconds")
    samples = _number(window.get("samples"), "observed.observation_window.samples")
    if not samples.is_integer():
        raise SloImpactGateError("observed.observation_window.samples must be an integer")
    samples = int(samples)
    if window_state != "complete":
        reasons.append("observation_window_incomplete")
    if duration_seconds < minimum_seconds:
        reasons.append("observation_window_too_short")
    if samples < minimum_samples:
        reasons.append("sample_count_shortfall")

    slo = _object(intent.get("slo"), "intent.slo")
    minimum_availability = _number(slo.get("minimum_availability"), "intent.slo.minimum_availability")
    max_latency = _number(slo.get("max_p95_latency_ms"), "intent.slo.max_p95_latency_ms")
    max_burn = _number(slo.get("max_error_budget_burn_rate"), "intent.slo.max_error_budget_burn_rate")
    metrics = _object(observed.get("metrics"), "observed.metrics")
    availability = _number(metrics.get("availability"), "observed.metrics.availability")
    latency = _number(metrics.get("p95_latency_ms"), "observed.metrics.p95_latency_ms")
    burn = _number(metrics.get("error_budget_burn_rate"), "observed.metrics.error_budget_burn_rate")
    if availability < minimum_availability:
        reasons.append("metric_availability_below_target")
    if latency > max_latency:
        reasons.append("metric_p95_latency_exceeded")
    if burn > max_burn:
        reasons.append("metric_error_budget_burn_exceeded")

    required_checks = intent.get("required_checks")
    if not isinstance(required_checks, list) or any(not isinstance(item, str) or not item.strip() for item in required_checks):
        raise SloImpactGateError("intent.required_checks must be a list of non-empty strings")
    if len(set(required_checks)) != len(required_checks):
        raise SloImpactGateError("intent.required_checks must not contain duplicates")
    checks = _object(observed.get("checks"), "observed.checks")
    for check_name in required_checks:
        result = checks.get(check_name)
        if result is None:
            reasons.append(f"check_missing:{check_name}")
        elif result != "passed":
            reasons.append(f"check_not_passed:{check_name}")

    traffic = _object(observed.get("traffic"), "observed.traffic")
    serving_candidate = _string(traffic.get("serving_candidate_id"), "observed.traffic.serving_candidate_id")
    route_state = _string(traffic.get("route_state"), "observed.traffic.route_state")
    if serving_candidate != intent_identity["candidate_id"]:
        reasons.append("serving_candidate_mismatch")
    if route_state != "serving":
        reasons.append("traffic_not_serving")

    reasons = _unique_reasons(reasons)
    identity_reasons = {
        "intent_id_mismatch",
        "run_id_mismatch",
        "candidate_id_mismatch",
        "source_commit_mismatch",
        "input_digest_mismatch",
        "environment_id_mismatch",
        "target_mismatch",
    }
    return {
        "allowed": not reasons,
        "state": "slo_impact_clear" if not reasons else "blocked",
        "reasons": reasons,
        "intent": copy.deepcopy(intent),
        "input": copy.deepcopy(observed),
        "checks": {
            "identity": not any(reason in identity_reasons for reason in reasons),
            "window": window_state == "complete" and duration_seconds >= minimum_seconds,
            "samples": samples >= minimum_samples,
            "slo_metrics": not any(reason.startswith("metric_") for reason in reasons),
            "error_budget": burn <= max_burn,
            "required_checks": not any(reason.startswith(("check_missing:", "check_not_passed:")) for reason in reasons),
            "traffic": route_state == "serving" and serving_candidate == intent_identity["candidate_id"],
            "candidate_id": intent_identity["candidate_id"],
            "run_id": intent_identity["run_id"],
        },
    }


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SloImpactGateError(f"file does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SloImpactGateError(f"invalid JSON: {path}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description="Check user-facing SLO impact without changing a deployment")
    parser.add_argument("intent_json", type=Path)
    parser.add_argument("observation_json", type=Path)
    args = parser.parse_args()
    try:
        report = evaluate_impact(load_json(args.intent_json), load_json(args.observation_json))
    except SloImpactGateError as exc:
        parser.error(str(exc))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["allowed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
