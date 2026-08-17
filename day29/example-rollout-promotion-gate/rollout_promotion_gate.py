#!/usr/bin/env python3
"""Day 29 read-only Rollout Promotion Gate."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EXPECTED_STAGES = ("observe", "metrics", "policy", "approval", "handoff")
EXPECTED_STATES = {
    "observe": "window_complete",
    "metrics": "metrics_passed",
    "policy": "step_allowed",
    "approval": "approval_bound",
    "handoff": "handoff_ready",
}


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def identity_mismatches(intent: dict[str, Any], observed: dict[str, Any]) -> list[str]:
    expected = intent.get("identity")
    actual = observed.get("identity")
    if not isinstance(expected, dict) or not isinstance(actual, dict):
        return ["identity"]
    fields = (
        "release_id",
        "environment",
        "current_cohort",
        "target_cohort",
        "run_id",
        "promotion_id",
        "evidence_digest",
        "policy_version",
    )
    return [field for field in fields if expected.get(field) != actual.get(field)]


def parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def evaluate_promotion(intent: dict[str, Any], observed: dict[str, Any]) -> dict[str, Any]:
    """Return a deterministic, side-effect-free promotion readiness report."""
    mismatches = identity_mismatches(intent, observed)
    if mismatches:
        return {
            "allowed": False,
            "state": "blocked_identity",
            "reasons": [f"identity_mismatch:{field}" for field in mismatches],
        }

    identity = intent["identity"]
    raw_thresholds = intent.get("thresholds")
    thresholds: dict[str, Any] = raw_thresholds if isinstance(raw_thresholds, dict) else {}
    stages = observed.get("stages")
    if not isinstance(stages, dict):
        return {"allowed": False, "state": "blocked_promotion", "reasons": ["stages_missing"]}

    reasons: list[str] = []
    for name in stages:
        if name not in EXPECTED_STAGES:
            reasons.append(f"stage_unknown:{name}")
    for name in EXPECTED_STAGES:
        if name not in stages:
            reasons.append(f"stage_missing:{name}")

    observed_order = observed.get("stage_order")
    if not isinstance(observed_order, list):
        reasons.append("stage_order_missing")
    elif observed_order != list(EXPECTED_STAGES):
        reasons.append("stage_order_invalid")

    digest = identity.get("evidence_digest")
    observe = stages.get("observe")
    metrics = stages.get("metrics")
    policy = stages.get("policy")
    approval = stages.get("approval")
    handoff = stages.get("handoff")

    for name, stage in stages.items():
        if name not in EXPECTED_STAGES or not isinstance(stage, dict):
            continue
        if stage.get("state") != EXPECTED_STATES[name]:
            reasons.append(f"stage_state_invalid:{name}")
        if stage.get("evidence_digest") != digest:
            reasons.append(f"stage_digest_mismatch:{name}")
        if not stage.get("audit_event_id"):
            reasons.append(f"audit_event_missing:{name}")

    if isinstance(observe, dict):
        if observe.get("window_seconds", 0) < intent.get("minimum_window_seconds", 0):
            reasons.append("observation_window_incomplete")
        if observe.get("sample_count", 0) < intent.get("minimum_samples", 0):
            reasons.append("observation_samples_insufficient")
        if observe.get("run_id", identity.get("run_id")) != identity.get("run_id"):
            reasons.append("observation_run_mismatch")

    if isinstance(metrics, dict):
        if metrics.get("error_rate", 1.0) > thresholds.get("max_error_rate", 0.02):
            reasons.append("metric_error_rate_exceeded")
        if metrics.get("p95_ms", 10**9) > thresholds.get("max_p95_ms", 450):
            reasons.append("metric_p95_exceeded")
        if metrics.get("saturation", 1.0) > thresholds.get("max_saturation", 0.75):
            reasons.append("metric_saturation_exceeded")

    if isinstance(policy, dict):
        if policy.get("current_cohort") != identity.get("current_cohort"):
            reasons.append("current_cohort_mismatch")
        if policy.get("target_cohort") != identity.get("target_cohort"):
            reasons.append("target_cohort_mismatch")
        if policy.get("target_cohort") not in intent.get("allowed_target_cohorts", []):
            reasons.append("target_cohort_not_allowed")
        if policy.get("step_percent", 10**9) > intent.get("max_step_percent", 0):
            reasons.append("promotion_step_exceeded")

    expected_scope = f"{identity.get('current_cohort')}->{identity.get('target_cohort')}"
    if isinstance(approval, dict):
        if not approval.get("owner") or not approval.get("scope"):
            reasons.append("approval_missing")
        if approval.get("scope") != expected_scope:
            reasons.append("approval_scope_mismatch")
        expiry = parse_time(approval.get("expires_at"))
        policy_expiry = parse_time(intent.get("approval_expires_at"))
        evaluation_time = parse_time(intent.get("evaluation_time"))
        if expiry is None or policy_expiry is None or evaluation_time is None or expiry < evaluation_time or expiry > policy_expiry:
            reasons.append("approval_expired")
        if approval.get("evidence_digest") != digest:
            reasons.append("approval_digest_mismatch")

    if isinstance(handoff, dict):
        required = (handoff.get("next_owner"), handoff.get("decision"), handoff.get("idempotency_key"))
        if any(not value for value in required):
            reasons.append("handoff_incomplete")
        if handoff.get("idempotency_key") != identity.get("promotion_id"):
            reasons.append("handoff_idempotency_mismatch")

    executed = observed.get("executed_promotions", [])
    if isinstance(executed, list) and identity.get("promotion_id") in executed:
        reasons.append("duplicate_promotion")

    return {
        "allowed": not reasons,
        "state": "promotion_ready" if not reasons else "blocked_promotion",
        "reasons": reasons,
    }


def check_promotion(intent_path: Path, observation_path: Path) -> dict[str, Any]:
    return evaluate_promotion(load_json(intent_path), load_json(observation_path))


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: rollout_promotion_gate.py <intent.json> <observation.json>", file=sys.stderr)
        return 2
    result = check_promotion(Path(sys.argv[1]), Path(sys.argv[2]))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
