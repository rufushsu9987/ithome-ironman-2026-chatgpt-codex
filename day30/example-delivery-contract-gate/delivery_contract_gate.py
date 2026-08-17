#!/usr/bin/env python3
"""Day 30 read-only Delivery Contract Gate."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

EXPECTED_STAGES = ("context", "plan", "execute", "verify", "review", "deliver")
EXPECTED_STATES = {
    "context": "context_bound",
    "plan": "plan_approved",
    "execute": "executed_scoped",
    "verify": "verified",
    "review": "review_complete",
    "deliver": "deliverable_bound",
}
IDENTITY_FIELDS = (
    "series_id",
    "day",
    "contract_id",
    "run_id",
    "source_digest",
    "evidence_digest",
    "policy_version",
    "owner",
    "target",
)


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
    return [field for field in IDENTITY_FIELDS if expected.get(field) != actual.get(field)]


def evaluate_delivery(intent: dict[str, Any], observed: dict[str, Any]) -> dict[str, Any]:
    """Return a deterministic, side-effect-free delivery readiness report."""
    mismatches = identity_mismatches(intent, observed)
    if mismatches:
        return {
            "allowed": False,
            "state": "blocked_identity",
            "reasons": [f"identity_mismatch:{field}" for field in mismatches],
        }

    identity = intent["identity"]
    reasons: list[str] = []
    stages = observed.get("stages")
    if not isinstance(stages, dict):
        return {"allowed": False, "state": "blocked_delivery", "reasons": ["stages_missing"]}

    for name in stages:
        if name not in EXPECTED_STAGES:
            reasons.append(f"stage_unknown:{name}")
    for name in EXPECTED_STAGES:
        if name not in stages:
            reasons.append(f"stage_missing:{name}")

    stage_order = observed.get("stage_order")
    if not isinstance(stage_order, list) or stage_order != list(EXPECTED_STAGES):
        reasons.append("stage_order_invalid")

    digest = identity.get("evidence_digest")
    for name, stage in stages.items():
        if name not in EXPECTED_STAGES or not isinstance(stage, dict):
            continue
        if stage.get("state") != EXPECTED_STATES[name]:
            reasons.append(f"stage_state_invalid:{name}")
        if stage.get("evidence_digest") != digest:
            reasons.append(f"stage_digest_mismatch:{name}")
        if not stage.get("audit_event_id"):
            reasons.append(f"audit_event_missing:{name}")

    required = intent.get("required_deliverables", [])
    deliverables = observed.get("deliverables")
    if not isinstance(required, list) or not isinstance(deliverables, dict):
        reasons.append("deliverables_missing")
    else:
        for name in required:
            item = deliverables.get(name)
            if not isinstance(item, dict):
                reasons.append(f"deliverable_missing:{name}")
                continue
            if item.get("status") != "verified":
                reasons.append(f"deliverable_not_verified:{name}")
            if item.get("evidence_digest") != digest:
                reasons.append(f"deliverable_digest_mismatch:{name}")
            if not isinstance(item.get("bytes"), int) or item.get("bytes", 0) <= 0:
                reasons.append(f"deliverable_empty:{name}")
            path = item.get("path")
            if not isinstance(path, str) or not path:
                reasons.append(f"deliverable_path_missing:{name}")
            elif Path(path).is_absolute():
                reasons.append(f"deliverable_path_absolute:{name}")
            if name == "media_qa" and item.get("qa_status") != "PASS":
                reasons.append("media_qa_not_pass")

    if observed.get("external_boundary") != intent.get("external_boundary"):
        reasons.append("external_boundary_mismatch")
    if observed.get("publication_status") != "not_started":
        reasons.append("publication_evidence_missing")

    handoff = observed.get("handoff")
    if not isinstance(handoff, dict) or any(
        not handoff.get(key) for key in ("next_owner", "decision", "idempotency_key")
    ):
        reasons.append("handoff_incomplete")
    elif handoff.get("idempotency_key") != identity.get("contract_id"):
        reasons.append("handoff_idempotency_mismatch")

    executed = observed.get("executed_contracts", [])
    if isinstance(executed, list) and identity.get("contract_id") in executed:
        reasons.append("duplicate_delivery")

    return {
        "allowed": not reasons,
        "state": "delivery_ready" if not reasons else "blocked_delivery",
        "reasons": reasons,
    }


def check_delivery(intent_path: Path, observation_path: Path) -> dict[str, Any]:
    return evaluate_delivery(load_json(intent_path), load_json(observation_path))


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: delivery_contract_gate.py <intent.json> <observation.json>", file=sys.stderr)
        return 2
    result = check_delivery(Path(sys.argv[1]), Path(sys.argv[2]))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
