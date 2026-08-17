#!/usr/bin/env python3
"""Day 26 read-only Evidence Access Gate with deterministic reasons."""
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
VALID_STORAGE_STATES = {"online", "archived"}


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def identity_mismatches(intent: dict[str, Any], observed: dict[str, Any]) -> list[str]:
    return [field for field in IDENTITY_FIELDS if intent.get(field) != observed.get(field)]


def _number(value: Any, default: float = 0.0) -> float:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else default


def _approval_scope(intent: dict[str, Any], request: dict[str, Any]) -> str:
    return "/".join(
        [
            str(intent.get("incident_id", "")),
            str(intent.get("target", "")),
            str(request.get("requester_id", "")),
            str(request.get("purpose", "")),
        ]
    )


def _requested_fields(request: dict[str, Any], name: str) -> list[str]:
    fields = (request.get("field_scope") or {}).get(name, [])
    return fields if isinstance(fields, list) else []


def evaluate_access(
    intent: dict[str, Any], observed: dict[str, Any], *, now_epoch: float | None = None
) -> dict[str, Any]:
    """Return a deterministic, side-effect-free access eligibility report."""
    mismatches = identity_mismatches(intent, observed)
    if mismatches:
        return {
            "allowed": False,
            "state": "blocked_identity",
            "reasons": [f"identity_mismatch:{field}" for field in mismatches],
        }

    now = _number(observed.get("observed_at_epoch"), 0.0) if now_epoch is None else now_epoch
    reasons: list[str] = []
    request = observed.get("access_request") or {}
    requester_role = request.get("requester_role")
    purpose = request.get("purpose")
    if requester_role not in intent.get("allowed_requester_roles", []):
        reasons.append("requester_role_not_allowed")
    if purpose not in intent.get("allowed_purposes", []):
        reasons.append("purpose_not_allowed")

    requested_names = request.get("evidence_names")
    if not isinstance(requested_names, list) or not requested_names:
        reasons.append("evidence_request_empty")
        requested_names = []
    permitted_fields = intent.get("permitted_fields") or {}
    inventory = observed.get("evidence_inventory") or {}
    for name in requested_names:
        if name not in permitted_fields:
            reasons.append(f"evidence_not_allowed:{name}")
            continue
        item = inventory.get(name)
        if not isinstance(item, dict):
            reasons.append(f"access_evidence_missing:{name}")
            continue
        if item.get("readable") is not True:
            reasons.append(f"access_evidence_not_readable:{name}")
        if item.get("storage_state") not in VALID_STORAGE_STATES:
            reasons.append(f"access_evidence_storage_invalid:{name}")
        if item.get("digest") != intent.get("evidence_digest"):
            reasons.append(f"access_evidence_digest_mismatch:{name}")

        allowed = set(permitted_fields.get(name, []))
        actual = set(item.get("fields", [])) if isinstance(item.get("fields"), list) else set()
        requested = _requested_fields(request, name)
        for field in requested:
            if field not in allowed:
                reasons.append(f"field_scope_exceeded:{name}:{field}")
            if field not in actual:
                reasons.append(f"field_not_available:{name}:{field}")
        if not requested:
            reasons.append(f"field_scope_empty:{name}")

    requested_at = request.get("requested_at_epoch")
    expires_at = request.get("expires_at_epoch")
    if not isinstance(requested_at, (int, float)) or isinstance(requested_at, bool):
        reasons.append("access_requested_at_missing")
    elif float(requested_at) > now:
        reasons.append("access_requested_at_future")
    if not isinstance(expires_at, (int, float)) or isinstance(expires_at, bool):
        reasons.append("access_expires_at_missing")
    else:
        expires_value = float(expires_at)
        if expires_value <= now:
            reasons.append("access_window_expired")
        if isinstance(requested_at, (int, float)) and not isinstance(requested_at, bool) and expires_value <= float(requested_at):
            reasons.append("access_window_invalid")
        if expires_value > now + _number(intent.get("max_access_seconds")):
            reasons.append("access_window_too_long")

    approval = observed.get("access_approval") or {}
    if not approval:
        reasons.append("access_approval_missing")
    else:
        if approval.get("decision") != "approved":
            reasons.append("access_approval_not_approved")
        if approval.get("scope") != _approval_scope(intent, request):
            reasons.append("approval_scope_mismatch")
        if approval.get("requester_id") != request.get("requester_id"):
            reasons.append("approval_requester_mismatch")
        if approval.get("purpose") != purpose:
            reasons.append("approval_purpose_mismatch")
        approved_at = approval.get("approved_at_epoch")
        if not isinstance(approved_at, (int, float)) or isinstance(approved_at, bool):
            reasons.append("approval_time_missing")
        elif now - float(approved_at) > _number(intent.get("approval_max_age_seconds")):
            reasons.append("approval_expired")
        for field in IDENTITY_FIELDS:
            if approval.get(field) != intent.get(field):
                reasons.append(f"approval_identity_mismatch:{field}")

    audit = observed.get("audit_anchor") or {}
    if not audit.get("event_id") or not audit.get("request_digest"):
        reasons.append("audit_anchor_missing")
    if audit.get("evidence_digest") != intent.get("evidence_digest"):
        reasons.append("audit_digest_mismatch")
    recorded_at = audit.get("recorded_at_epoch")
    if not isinstance(recorded_at, (int, float)) or isinstance(recorded_at, bool):
        reasons.append("audit_recorded_at_missing")
    elif float(recorded_at) > now:
        reasons.append("audit_recorded_at_future")

    return {
        "allowed": not reasons,
        "state": "access_eligible" if not reasons else "blocked_access",
        "reasons": reasons,
    }


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: evidence_access_gate.py <intent.json> <observation.json>", file=sys.stderr)
        return 2
    result = evaluate_access(load_json(Path(sys.argv[1])), load_json(Path(sys.argv[2])))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
