#!/usr/bin/env python3
"""Read-only, fail-closed freshness check for a versioned Context Pack."""
from __future__ import annotations

import argparse
import copy
import fnmatch
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VALID_LEARNING_STATUSES = {"approved", "applied"}


class FreshnessGateError(ValueError):
    """Raised when the gate input is malformed instead of being silently trusted."""


def _timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise FreshnessGateError(f"{field} must be a non-empty ISO-8601 string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise FreshnessGateError(f"{field} is not a valid ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise FreshnessGateError(f"{field} must be a non-empty string")
    return value


def _list_of_strings(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise FreshnessGateError(f"{field} must be a list of non-empty strings")
    return list(value)


def _scope_matches(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def evaluate_freshness(context: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    """Evaluate freshness without changing either input object.

    The caller supplies the current repository commit and a fixed check time so
    the same inputs always produce the same report. The function never updates a
    Context Pack or extends a learning record's lifetime.
    """
    if not isinstance(context, dict):
        raise FreshnessGateError("context must be an object")
    if not isinstance(request, dict):
        raise FreshnessGateError("request must be an object")

    context_id = _string(context.get("context_id"), "context.context_id")
    request_context_id = _string(request.get("context_id"), "request.context_id")
    context_commit = _string(context.get("source_commit"), "context.source_commit")
    request_commit = _string(request.get("source_commit"), "request.source_commit")
    checked_at = _timestamp(request.get("checked_at"), "request.checked_at")
    created_at = _timestamp(context.get("created_at"), "context.created_at")
    paths = _list_of_strings(request.get("paths"), "request.paths")

    max_age_hours = context.get("max_age_hours")
    if isinstance(max_age_hours, bool) or not isinstance(max_age_hours, (int, float)) or max_age_hours < 0:
        raise FreshnessGateError("context.max_age_hours must be a non-negative number")

    reasons: list[str] = []
    if context_id != request_context_id:
        reasons.append("context_id_mismatch")
    if context_commit != request_commit:
        reasons.append("source_commit_mismatch")

    age_hours = (checked_at - created_at).total_seconds() / 3600
    if age_hours < 0:
        reasons.append("checked_at_before_context_created_at")
    elif age_hours > float(max_age_hours):
        reasons.append("context_expired")

    learning_refs = context.get("learning_refs")
    if not isinstance(learning_refs, list) or not learning_refs:
        reasons.append("missing_learning_refs")
        learning_refs = []

    learning_results: list[dict[str, Any]] = []
    for learning in learning_refs:
        if not isinstance(learning, dict):
            reasons.append("learning_record_invalid")
            continue
        learning_id = learning.get("learning_id")
        if not isinstance(learning_id, str) or not learning_id.strip():
            reasons.append("learning_record_missing_id")
            learning_id = "<unknown>"

        prefix = f"learning:{learning_id}"
        status = learning.get("status")
        evidence_refs = learning.get("evidence_refs")
        scopes = learning.get("scope")
        expires_at_value = learning.get("expires_at")
        learning_reasons: list[str] = []

        if status not in VALID_LEARNING_STATUSES:
            reason = f"{prefix}:status_{status or 'missing'}"
            reasons.append(reason)
            learning_reasons.append(reason)
        if not isinstance(evidence_refs, list) or not evidence_refs or not all(
            isinstance(item, str) and item.strip() for item in evidence_refs
        ):
            reason = f"{prefix}:missing_evidence"
            reasons.append(reason)
            learning_reasons.append(reason)
        if not isinstance(scopes, list) or not scopes or not all(
            isinstance(item, str) and item.strip() for item in scopes
        ):
            reason = f"{prefix}:missing_scope"
            reasons.append(reason)
            learning_reasons.append(reason)
            scopes = []

        if expires_at_value is None:
            reason = f"{prefix}:missing_expiry"
            reasons.append(reason)
            learning_reasons.append(reason)
        else:
            try:
                expires_at = _timestamp(expires_at_value, f"learning[{learning_id}].expires_at")
            except FreshnessGateError:
                reason = f"{prefix}:invalid_expiry"
                reasons.append(reason)
                learning_reasons.append(reason)
            else:
                if expires_at <= checked_at:
                    reason = f"{prefix}:expired"
                    reasons.append(reason)
                    learning_reasons.append(reason)

        for path in paths:
            if scopes and not _scope_matches(path, scopes):
                reason = f"path_out_of_scope:{path}"
                if reason not in reasons:
                    reasons.append(reason)
                learning_reasons.append(reason)

        learning_results.append({
            "learning_id": learning_id,
            "status": status,
            "reasons": learning_reasons,
        })

    return {
        "allowed": not reasons,
        "state": "fresh" if not reasons else "blocked",
        "reasons": reasons,
        "input": copy.deepcopy(request),
        "checks": {
            "context_id": context_id == request_context_id,
            "source_commit": context_commit == request_commit,
            "context_age_hours": round(age_hours, 3),
            "max_age_hours": max_age_hours,
            "learning_count": len(learning_refs),
            "learning_results": learning_results,
        },
    }


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FreshnessGateError(f"file does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise FreshnessGateError(f"invalid JSON: {path}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Context Pack freshness")
    parser.add_argument("context_json", type=Path)
    parser.add_argument("request_json", type=Path)
    args = parser.parse_args()
    try:
        context = load_json(args.context_json)
        request = load_json(args.request_json)
        report = evaluate_freshness(context, request)
    except FreshnessGateError as exc:
        parser.error(str(exc))
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["allowed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
