#!/usr/bin/env python3
"""Day 23 read-only Recovery Verification Gate with deterministic reasons."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


IDENTITY_FIELDS = (
    "rollback_id",
    "run_id",
    "source_candidate_id",
    "target_candidate_id",
    "source_commit",
    "input_digest",
    "environment_id",
    "target",
)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def identity_mismatches(intent: dict[str, Any], observed: dict[str, Any]) -> list[str]:
    return [field for field in IDENTITY_FIELDS if intent.get(field) != observed.get(field)]


def _number(value: Any, default: float = 0.0) -> float:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else default


def evaluate_recovery(intent: dict[str, Any], observed: dict[str, Any]) -> dict[str, Any]:
    """Return a deterministic, side-effect-free recovery verification report."""
    mismatches = identity_mismatches(intent, observed)
    if mismatches:
        return {
            "allowed": False,
            "state": "blocked_identity",
            "reasons": [f"identity_mismatch:{field}" for field in mismatches],
        }

    reasons: list[str] = []
    rollback = observed.get("rollback") or {}
    if rollback.get("status") != "completed":
        reasons.append("rollback_not_completed")
    if rollback.get("applied_target_candidate_id") != intent.get("target_candidate_id"):
        reasons.append("rollback_target_mismatch")

    window = observed.get("recovery_window") or {}
    if window.get("complete") is not True:
        reasons.append("recovery_window_incomplete")
    if _number(window.get("duration_seconds")) < _number(intent.get("min_recovery_window_seconds")):
        reasons.append("recovery_window_too_short")
    if _number(window.get("sample_count")) < _number(intent.get("min_samples")):
        reasons.append("recovery_sample_count_shortfall")

    metrics = observed.get("metrics") or {}
    thresholds = intent.get("recovery_thresholds") or {}
    if _number(metrics.get("availability"), -1.0) < _number(thresholds.get("availability_min"), 0.0):
        reasons.append("recovery_metric_availability_below_target")
    if _number(metrics.get("p95_latency_ms"), float("inf")) > _number(thresholds.get("p95_latency_max_ms"), float("inf")):
        reasons.append("recovery_metric_p95_latency_exceeded")
    if _number(metrics.get("error_rate"), float("inf")) > _number(thresholds.get("error_rate_max"), float("inf")):
        reasons.append("recovery_metric_error_rate_exceeded")
    if _number(metrics.get("queue_depth"), float("inf")) > _number(thresholds.get("queue_depth_max"), float("inf")):
        reasons.append("recovery_metric_queue_depth_exceeded")

    checks = observed.get("checks") or {}
    for name in intent.get("required_checks", []):
        if name not in checks:
            reasons.append(f"recovery_check_missing:{name}")
        elif checks[name] != "passed":
            reasons.append(f"recovery_check_not_passed:{name}")

    traffic = observed.get("traffic") or {}
    if traffic.get("state") != "serving":
        reasons.append("recovery_traffic_not_serving")
    if traffic.get("serving_candidate_id") != intent.get("target_candidate_id"):
        reasons.append("recovery_serving_candidate_mismatch")

    expected_evidence = intent.get("recovery_evidence") or {}
    actual_evidence = observed.get("recovery_evidence") or {}
    if not actual_evidence:
        reasons.append("recovery_evidence_missing")
    else:
        if actual_evidence.get("name") != expected_evidence.get("name"):
            reasons.append("recovery_evidence_name_mismatch")
        if actual_evidence.get("digest") != expected_evidence.get("digest"):
            reasons.append("recovery_evidence_digest_mismatch")

    return {
        "allowed": not reasons,
        "state": "recovery_verified" if not reasons else "blocked_recovery",
        "reasons": reasons,
    }


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: recovery_verification_gate.py <intent.json> <observation.json>", file=sys.stderr)
        return 2
    result = evaluate_recovery(load_json(Path(sys.argv[1])), load_json(Path(sys.argv[2])))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
