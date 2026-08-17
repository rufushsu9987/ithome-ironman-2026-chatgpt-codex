#!/usr/bin/env python3
"""Day 25 read-only Evidence Retention Gate with deterministic reasons."""
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


def evaluate_retention(
    intent: dict[str, Any], observed: dict[str, Any], *, now_epoch: float | None = None
) -> dict[str, Any]:
    """Return a deterministic, side-effect-free evidence retention report."""
    mismatches = identity_mismatches(intent, observed)
    if mismatches:
        return {
            "allowed": False,
            "state": "blocked_identity",
            "reasons": [f"identity_mismatch:{field}" for field in mismatches],
        }

    now = _number(observed.get("observed_at_epoch"), 0.0) if now_epoch is None else now_epoch
    reasons: list[str] = []

    retention = observed.get("retention") or {}
    if retention.get("state") != "inventory_verified":
        reasons.append("retention_inventory_not_verified")
    if retention.get("archive_complete") is not True:
        reasons.append("retention_archive_incomplete")

    legal_hold = observed.get("legal_hold") or {}
    if intent.get("legal_hold_required") is True and legal_hold.get("state") != "active":
        reasons.append("legal_hold_missing")

    if observed.get("access_scope") != intent.get("required_access_scope"):
        reasons.append("access_scope_mismatch")

    evidence = observed.get("evidence") or {}
    minimum_retention = _number(intent.get("min_retention_seconds"))
    for name in intent.get("required_evidence", []):
        item = evidence.get(name)
        if not isinstance(item, dict):
            reasons.append(f"evidence_missing:{name}")
            continue
        if item.get("readable") is not True:
            reasons.append(f"evidence_not_readable:{name}")
        if item.get("storage_state") not in VALID_STORAGE_STATES:
            reasons.append(f"evidence_storage_invalid:{name}")
        if item.get("digest") != intent.get("evidence_digest"):
            reasons.append(f"evidence_digest_mismatch:{name}")

        created_at = item.get("created_at_epoch")
        if not isinstance(created_at, (int, float)) or isinstance(created_at, bool):
            reasons.append(f"evidence_created_at_missing:{name}")
        else:
            if float(created_at) > now:
                reasons.append(f"evidence_created_at_future:{name}")

        retain_until = item.get("retain_until_epoch")
        if not isinstance(retain_until, (int, float)) or isinstance(retain_until, bool):
            reasons.append(f"evidence_retain_until_missing:{name}")
        else:
            retain_until_value = float(retain_until)
            if retain_until_value < now:
                reasons.append(f"evidence_retention_expired:{name}")
            if retain_until_value < now + minimum_retention:
                reasons.append(f"evidence_retention_too_short:{name}")

    return {
        "allowed": not reasons,
        "state": "retention_ready" if not reasons else "blocked_retention",
        "reasons": reasons,
    }


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: evidence_retention_gate.py <intent.json> <observation.json>", file=sys.stderr)
        return 2
    result = evaluate_retention(load_json(Path(sys.argv[1])), load_json(Path(sys.argv[2])))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
