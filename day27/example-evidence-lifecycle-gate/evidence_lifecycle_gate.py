#!/usr/bin/env python3
"""Day 27 read-only Incident Evidence Lifecycle Gate."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

IDENTITY_FIELDS = (
    "incident_id",
    "closeout_id",
    "run_id",
    "evidence_digest",
    "environment_id",
    "target",
)
DEFAULT_STAGE_ORDER = ("closeout", "retention", "access")
EXPECTED_STAGE_STATES = {
    "closeout": "closed",
    "retention": "retention_ready",
    "access": "access_eligible",
}


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def identity_mismatches(intent: dict[str, Any], observed: dict[str, Any]) -> list[str]:
    return [field for field in IDENTITY_FIELDS if intent.get(field) != observed.get(field)]


def _stage_order(intent: dict[str, Any]) -> list[str]:
    configured = intent.get("required_stages")
    if not isinstance(configured, list) or not configured:
        return list(DEFAULT_STAGE_ORDER)
    return [str(stage) for stage in configured]


def _reason_for_order(stage_names: list[str], order: list[str]) -> str | None:
    positions = {stage: index for index, stage in enumerate(order)}
    previous: str | None = None
    previous_position = -1
    for stage in stage_names:
        position = positions.get(stage)
        if position is None:
            previous = stage
            previous_position = len(order)
            continue
        if position < previous_position and previous is not None:
            return f"stage_order_invalid:{stage}_before_{previous}"
        previous = stage
        previous_position = position
    return None


def evaluate_lifecycle(intent: dict[str, Any], observed: dict[str, Any]) -> dict[str, Any]:
    """Return a deterministic, side-effect-free lifecycle readiness report."""
    mismatches = identity_mismatches(intent, observed)
    if mismatches:
        return {
            "allowed": False,
            "state": "blocked_identity",
            "reasons": [f"identity_mismatch:{field}" for field in mismatches],
        }

    order = _stage_order(intent)
    reasons: list[str] = []
    stages = observed.get("stages")
    if not isinstance(stages, dict):
        return {
            "allowed": False,
            "state": "blocked_pipeline",
            "reasons": ["stages_missing"],
        }

    allowed_stages = set(order)
    for name in stages:
        if name not in allowed_stages:
            reasons.append(f"stage_unknown:{name}")

    for required in order:
        if required not in stages:
            reasons.append(f"stage_missing:{required}")

    order_reason = _reason_for_order(list(stages.keys()), order)
    if order_reason:
        reasons.append(order_reason)

    for name in order:
        stage = stages.get(name)
        if not isinstance(stage, dict):
            reasons.append(f"stage_invalid:{name}")
            continue
        if stage.get("state") != EXPECTED_STAGE_STATES.get(name):
            reasons.append(f"stage_state_invalid:{name}")
        if stage.get("evidence_digest") != intent.get("evidence_digest"):
            reasons.append(f"stage_digest_mismatch:{name}")
        if not stage.get("audit_event_id"):
            reasons.append(f"audit_event_missing:{name}")
        if name == "retention" and stage.get("readback_passed") is not True:
            reasons.append("retention_readback_missing")
        if name == "access" and stage.get("approval_bound") is not True:
            reasons.append("access_approval_unbound")

    return {
        "allowed": not reasons,
        "state": "pipeline_ready" if not reasons else "blocked_pipeline",
        "reasons": reasons,
    }


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: evidence_lifecycle_gate.py <intent.json> <observation.json>", file=sys.stderr)
        return 2
    result = evaluate_lifecycle(load_json(Path(sys.argv[1])), load_json(Path(sys.argv[2])))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
