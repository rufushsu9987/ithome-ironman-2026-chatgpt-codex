#!/usr/bin/env python3
"""Build a small, fail-closed incident pack from an append-only audit trail.

The example deliberately uses only the Python standard library.  It is not a
production logging system: the point is to make the release-to-incident
contract executable and easy to inspect.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


class IncidentPackError(ValueError):
    """Raised when an audit trail cannot support a trustworthy incident pack."""


REQUIRED_FIELDS = {
    "event_id",
    "change_id",
    "timestamp",
    "actor",
    "action",
    "outcome",
    "source_commit",
}
ALLOWED_ACTIONS = {
    "release_approved",
    "deployed",
    "health_check_passed",
    "health_check_failed",
    "incident_opened",
    "rollback_started",
    "rollback_completed",
    "incident_resolved",
}


def _parse_timestamp(value: Any) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise IncidentPackError("timestamp must be a non-empty ISO-8601 string")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise IncidentPackError(f"invalid timestamp: {value}") from exc


def _validate_event(event: dict[str, Any]) -> None:
    if not isinstance(event, dict):
        raise IncidentPackError("event must be an object")

    missing = sorted(REQUIRED_FIELDS - event.keys())
    if missing:
        raise IncidentPackError("event is missing fields: " + ", ".join(missing))

    for field in ("event_id", "change_id", "actor", "source_commit"):
        if not isinstance(event[field], str) or not event[field].strip():
            raise IncidentPackError(f"{field} must be a non-empty string")

    _parse_timestamp(event["timestamp"])
    if event["action"] not in ALLOWED_ACTIONS:
        raise IncidentPackError(f"unsupported action: {event['action']}")
    if event["outcome"] not in {"pass", "fail", "info"}:
        raise IncidentPackError("outcome must be pass, fail, or info")


def _validated_events(events: Iterable[dict[str, Any]], change_id: str) -> list[dict[str, Any]]:
    result = list(events)
    if not result:
        raise IncidentPackError("audit trail is empty")

    seen: set[str] = set()
    for event in result:
        _validate_event(event)
        event_id = event["event_id"]
        if event_id in seen:
            raise IncidentPackError(f"duplicate event_id: {event_id}")
        seen.add(event_id)
        if event["change_id"] != change_id:
            raise IncidentPackError("events contain a different change_id")

    return sorted(result, key=lambda item: _parse_timestamp(item["timestamp"]))


def append_event(path: Path, event: dict[str, Any]) -> dict[str, Any]:
    """Append one validated event, refusing duplicate event IDs."""
    _validate_event(event)
    path = Path(path)
    existing_ids: set[str] = set()
    if path.exists():
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                previous = json.loads(line)
            except json.JSONDecodeError as exc:
                raise IncidentPackError(f"invalid JSON at line {line_number}") from exc
            _validate_event(previous)
            if previous["event_id"] in existing_ids:
                raise IncidentPackError(f"duplicate event_id: {previous['event_id']}")
            existing_ids.add(previous["event_id"])

    if event["event_id"] in existing_ids:
        raise IncidentPackError(f"duplicate event_id: {event['event_id']}")

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
    return event


def load_events(path: Path) -> list[dict[str, Any]]:
    """Read and validate a JSONL audit trail."""
    path = Path(path)
    if not path.exists():
        raise IncidentPackError(f"audit trail does not exist: {path}")
    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise IncidentPackError(f"invalid JSON at line {line_number}") from exc
        if not isinstance(event, dict):
            raise IncidentPackError(f"line {line_number} is not an event object")
        events.append(event)
    return events


def build_incident_pack(events: Iterable[dict[str, Any]], change_id: str) -> dict[str, Any]:
    """Summarize release and incident evidence without hiding an open failure."""
    if not isinstance(change_id, str) or not change_id.strip():
        raise IncidentPackError("change_id must be a non-empty string")

    ordered = _validated_events(events, change_id)
    actions = {event["action"] for event in ordered}
    required_actions = {"release_approved", "deployed"}
    missing = sorted(required_actions - actions)
    if missing:
        raise IncidentPackError("missing required event: " + ", ".join(missing))

    failure_seen = bool(actions & {"health_check_failed", "incident_opened"})
    last = ordered[-1]
    if last["action"] == "rollback_completed":
        status = "resolved"
        resolution = "rollback"
        next_action = "none"
    elif last["action"] == "incident_resolved":
        status = "resolved"
        resolution = "fix"
        next_action = "none"
    elif failure_seen:
        status = "open"
        resolution = None
        next_action = "rollback_or_fix"
    elif last["action"] == "health_check_passed":
        status = "healthy"
        resolution = None
        next_action = "none"
    else:
        status = "in_progress"
        resolution = None
        next_action = "observe_and_verify"

    return {
        "change_id": change_id,
        "source_commit": ordered[-1]["source_commit"],
        "status": status,
        "resolution": resolution,
        "next_action": next_action,
        "incident_detected": failure_seen,
        "timeline": [event["event_id"] for event in ordered],
        "evidence": [event.get("evidence") for event in ordered if event.get("evidence")],
        "first_event_id": ordered[0]["event_id"],
        "last_event_id": last["event_id"],
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build an incident pack from a JSONL audit trail")
    parser.add_argument("audit_log", type=Path)
    parser.add_argument("change_id")
    args = parser.parse_args()
    try:
        print(json.dumps(build_incident_pack(load_events(args.audit_log), args.change_id), ensure_ascii=False, indent=2))
    except IncidentPackError as exc:
        parser.error(str(exc))
