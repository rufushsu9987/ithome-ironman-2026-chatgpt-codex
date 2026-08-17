#!/usr/bin/env python3
"""Day 28 read-only Progressive Rollout Gate."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

DEFAULT_STAGE_ORDER = ("identity", "canary", "flag", "rollback", "health")
EXPECTED_STAGE_STATES = {
    "identity": "identity_bound",
    "canary": "canary_passed",
    "flag": "flag_bound",
    "rollback": "rollback_ready",
    "health": "health_passed",
}


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def identity_mismatches(intent: dict[str, Any], observed: dict[str, Any]) -> list[str]:
    expected = intent.get("identity", {})
    actual = observed.get("identity", {})
    if not isinstance(expected, dict) or not isinstance(actual, dict):
        return ["identity"]
    fields = list(expected.keys())
    return [field for field in fields if expected.get(field) != actual.get(field)]


def required_stage_order(intent: dict[str, Any]) -> list[str]:
    configured = intent.get("required_stages")
    if not isinstance(configured, list) or not configured:
        return list(DEFAULT_STAGE_ORDER)
    return [str(stage) for stage in configured]


def order_reasons(stage_order: Any, expected: list[str]) -> list[str]:
    if not isinstance(stage_order, list):
        return ["stage_order_missing"]
    positions = {stage: index for index, stage in enumerate(expected)}
    reasons: list[str] = []
    previous_name: str | None = None
    previous_position = -1
    for raw_name in stage_order:
        name = str(raw_name)
        if name not in positions:
            continue
        position = positions[name]
        if position < previous_position and previous_name is not None:
            reasons.append(f"stage_order_invalid:{name}_before_{previous_name}")
        previous_name = name
        previous_position = position
    if len(stage_order) != len(set(stage_order)):
        reasons.append("stage_order_duplicate")
    return reasons


def evaluate_pipeline(intent: dict[str, Any], observed: dict[str, Any]) -> dict[str, Any]:
    """Return a deterministic, side-effect-free rollout readiness report."""
    mismatches = identity_mismatches(intent, observed)
    if mismatches:
        return {
            "allowed": False,
            "state": "blocked_identity",
            "reasons": [f"identity_mismatch:{field}" for field in mismatches],
        }

    expected_order = required_stage_order(intent)
    stages = observed.get("stages")
    if not isinstance(stages, dict):
        return {"allowed": False, "state": "blocked_pipeline", "reasons": ["stages_missing"]}

    reasons: list[str] = []
    expected_set = set(expected_order)
    for name in stages:
        if name not in expected_set:
            reasons.append(f"stage_unknown:{name}")
    for name in expected_order:
        if name not in stages:
            reasons.append(f"stage_missing:{name}")
    reasons.extend(order_reasons(observed.get("stage_order"), expected_order))

    intent_digest = intent.get("evidence_digest")
    identity = intent.get("identity", {})
    thresholds = intent.get("thresholds", {})
    max_p95 = thresholds.get("max_p95_ms", 450) if isinstance(thresholds, dict) else 450
    max_error = thresholds.get("max_error_rate", 0.02) if isinstance(thresholds, dict) else 0.02

    for name in expected_order:
        stage = stages.get(name)
        if not isinstance(stage, dict):
            if name in stages:
                reasons.append(f"stage_invalid:{name}")
            continue
        expected_state = EXPECTED_STAGE_STATES.get(name)
        if expected_state and stage.get("state") != expected_state:
            reasons.append(f"stage_state_invalid:{name}")
        if stage.get("evidence_digest") != intent_digest:
            reasons.append(f"stage_digest_mismatch:{name}")
        if not stage.get("audit_event_id"):
            reasons.append(f"audit_event_missing:{name}")

        if name == "canary":
            if stage.get("p95_ms", 10**9) > max_p95:
                reasons.append("canary_p95_exceeded")
            if stage.get("error_rate", 1.0) > max_error:
                reasons.append("canary_error_rate_exceeded")
            if stage.get("cohort_match") is not True:
                reasons.append("canary_cohort_mismatch")
        elif name == "flag":
            if stage.get("flag_key") != identity.get("flag_key"):
                reasons.append("flag_key_mismatch")
            if stage.get("mapping_match") is not True:
                reasons.append("flag_mapping_mismatch")
            if stage.get("kill_switch_ready") is not True:
                reasons.append("flag_kill_switch_unready")
        elif name == "rollback":
            if not stage.get("target"):
                reasons.append("rollback_target_missing")
            if not stage.get("trigger"):
                reasons.append("rollback_trigger_missing")
            if not isinstance(stage.get("timeout_seconds"), (int, float)) or stage.get("timeout_seconds") <= 0:
                reasons.append("rollback_timeout_invalid")
        elif name == "health":
            if stage.get("readback_match") is not True:
                reasons.append("health_readback_mismatch")
            if stage.get("run_id") != identity.get("run_id"):
                reasons.append("health_run_mismatch")

    return {
        "allowed": not reasons,
        "state": "pipeline_ready" if not reasons else "blocked_pipeline",
        "reasons": reasons,
    }


def check_pipeline(intent_path: Path, observation_path: Path) -> dict[str, Any]:
    return evaluate_pipeline(load_json(intent_path), load_json(observation_path))


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: evidence_rollout_gate.py <intent.json> <observation.json>", file=sys.stderr)
        return 2
    result = check_pipeline(Path(sys.argv[1]), Path(sys.argv[2]))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
