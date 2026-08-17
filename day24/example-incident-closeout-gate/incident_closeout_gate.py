#!/usr/bin/env python3
"""Day 24 read-only Incident Closeout Gate with deterministic reasons."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

IDENTITY_FIELDS = (
    "incident_id",
    "recovery_id",
    "run_id",
    "candidate_id",
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


def _matches_identity(value: dict[str, Any], intent: dict[str, Any]) -> bool:
    return all(value.get(field) == intent.get(field) for field in IDENTITY_FIELDS)


def evaluate_closeout(intent: dict[str, Any], observed: dict[str, Any], *, now_epoch: float | None = None) -> dict[str, Any]:
    """Return a deterministic, side-effect-free closeout eligibility report."""
    mismatches = identity_mismatches(intent, observed)
    if mismatches:
        return {
            "allowed": False,
            "state": "blocked_identity",
            "reasons": [f"identity_mismatch:{field}" for field in mismatches],
        }

    now = _number(observed.get("observed_at_epoch"), 0.0) if now_epoch is None else now_epoch
    reasons: list[str] = []

    recovery = observed.get("recovery") or {}
    if recovery.get("state") != "recovery_verified":
        reasons.append("recovery_not_verified")
    if recovery.get("evidence_digest") != intent.get("evidence_digest"):
        reasons.append("recovery_evidence_digest_mismatch")

    impact = observed.get("customer_impact_window") or {}
    if impact.get("complete") is not True:
        reasons.append("impact_window_incomplete")
    if _number(impact.get("duration_seconds")) < _number(intent.get("min_impact_window_seconds")):
        reasons.append("impact_window_too_short")
    if _number(impact.get("sample_count")) < _number(intent.get("min_impact_samples")):
        reasons.append("impact_sample_count_shortfall")

    followups = observed.get("followups") or {}
    for name in intent.get("critical_followups", []):
        item = followups.get(name)
        if not isinstance(item, dict):
            reasons.append(f"followup_missing:{name}")
            continue
        if not item.get("owner_id"):
            reasons.append(f"followup_owner_missing:{name}")
        due = item.get("due_at_epoch")
        if not isinstance(due, (int, float)) or isinstance(due, bool):
            reasons.append(f"followup_due_missing:{name}")
        elif float(due) < now:
            reasons.append(f"followup_overdue:{name}")
        if item.get("status") not in {"completed", "accepted"}:
            reasons.append(f"followup_not_complete:{name}")
        if item.get("evidence_digest") != intent.get("evidence_digest"):
            reasons.append(f"followup_digest_mismatch:{name}")

    postmortem = observed.get("postmortem") or {}
    if not postmortem:
        reasons.append("postmortem_missing")
    else:
        if postmortem.get("status") not in {"published", "accepted"}:
            reasons.append("postmortem_not_ready")
        if postmortem.get("incident_id") != intent.get("incident_id"):
            reasons.append("postmortem_identity_mismatch")
        if postmortem.get("evidence_digest") != intent.get("evidence_digest"):
            reasons.append("postmortem_digest_mismatch")

    learning = observed.get("learning_pack") or {}
    if not learning:
        reasons.append("learning_pack_missing")
    else:
        if learning.get("status") != "ready":
            reasons.append("learning_pack_not_ready")
        if learning.get("incident_id") != intent.get("incident_id"):
            reasons.append("learning_pack_identity_mismatch")
        if learning.get("evidence_digest") != intent.get("evidence_digest"):
            reasons.append("learning_pack_digest_mismatch")

    approval = observed.get("closeout_approval") or {}
    if not approval:
        reasons.append("closeout_approval_missing")
    else:
        if approval.get("decision") != "approved":
            reasons.append("closeout_approval_not_approved")
        if approval.get("role") not in intent.get("allowed_approval_roles", []):
            reasons.append("closeout_approval_role_mismatch")
        expected_scope = f"{intent.get('incident_id')}/{intent.get('target')}"
        if approval.get("scope") != expected_scope:
            reasons.append("closeout_approval_scope_mismatch")
        approved_at = approval.get("approved_at_epoch")
        if not isinstance(approved_at, (int, float)) or isinstance(approved_at, bool):
            reasons.append("closeout_approval_time_missing")
        elif now - float(approved_at) > _number(intent.get("approval_max_age_seconds")):
            reasons.append("closeout_approval_expired")
        if not _matches_identity(approval, intent):
            reasons.append("closeout_approval_identity_mismatch")

    return {
        "allowed": not reasons,
        "state": "closeout_eligible" if not reasons else "blocked_closeout",
        "reasons": reasons,
    }


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: incident_closeout_gate.py <intent.json> <observation.json>", file=sys.stderr)
        return 2
    result = evaluate_closeout(load_json(Path(sys.argv[1])), load_json(Path(sys.argv[2])))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
