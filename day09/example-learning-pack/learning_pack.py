#!/usr/bin/env python3
"""Build and apply a small, fail-closed Learning Pack.

The example intentionally uses only the Python standard library.  It models the
boundary between an AI-generated proposed lesson and a human-approved rule that
may be referenced by a later Context Pack.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


class LearningPackError(ValueError):
    """Raised when a learning record cannot safely enter a Context Pack."""


REQUIRED_FIELDS = {
    "learning_id",
    "context_id",
    "incident_id",
    "change_id",
    "source_commit",
    "observed_at",
    "incident_status",
    "lesson",
    "evidence_refs",
    "scope",
    "status",
    "owner",
}
VALID_STATUSES = {"proposed", "approved", "applied", "rejected", "retired"}


def _parse_timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise LearningPackError(f"{field} must be a non-empty ISO-8601 string")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise LearningPackError(f"{field} is not a valid ISO-8601 timestamp") from exc


def _non_empty_string(value: Any, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise LearningPackError(f"{field} must be a non-empty string")


def _validate_record(record: dict[str, Any]) -> None:
    if not isinstance(record, dict):
        raise LearningPackError("learning record must be an object")

    missing = sorted(REQUIRED_FIELDS - record.keys())
    if missing:
        raise LearningPackError("learning record is missing fields: " + ", ".join(missing))

    for field in (
        "learning_id",
        "context_id",
        "incident_id",
        "change_id",
        "source_commit",
        "lesson",
        "owner",
    ):
        _non_empty_string(record[field], field)

    _parse_timestamp(record["observed_at"], "observed_at")
    if record["incident_status"] != "resolved":
        raise LearningPackError("incident_status must be resolved before learning can be reused")
    if record["status"] not in VALID_STATUSES:
        raise LearningPackError(f"unsupported learning status: {record['status']}")

    evidence_refs = record["evidence_refs"]
    if not isinstance(evidence_refs, list) or not evidence_refs or not all(
        isinstance(item, str) and item.strip() for item in evidence_refs
    ):
        raise LearningPackError("evidence_refs must contain at least one non-empty path")

    scope = record["scope"]
    if not isinstance(scope, list) or not scope or not all(
        isinstance(item, str) and item.strip() for item in scope
    ):
        raise LearningPackError("scope must contain at least one non-empty path pattern")

    if record["status"] in {"approved", "applied"}:
        _non_empty_string(record.get("approved_by"), "approved_by")
        _parse_timestamp(record.get("approved_at"), "approved_at")


def validate_records(records: Iterable[dict[str, Any]], context_id: str) -> list[dict[str, Any]]:
    _non_empty_string(context_id, "context_id")
    result = list(records)
    if not result:
        raise LearningPackError("learning records are empty")

    seen: set[str] = set()
    for record in result:
        _validate_record(record)
        learning_id = record["learning_id"]
        if learning_id in seen:
            raise LearningPackError(f"duplicate learning_id: {learning_id}")
        seen.add(learning_id)
        if record["context_id"] != context_id:
            raise LearningPackError("learning record belongs to a different context_id")
        if record["status"] not in {"approved", "applied"}:
            raise LearningPackError(
                f"learning {learning_id} is {record['status']}; only approved/applied records can be packed"
            )

    return sorted(result, key=lambda item: _parse_timestamp(item["observed_at"], "observed_at"))


def build_learning_pack(records: Iterable[dict[str, Any]], context_id: str) -> dict[str, Any]:
    """Create a deterministic pack from human-approved lessons."""
    ordered = validate_records(records, context_id)
    return {
        "context_id": context_id,
        "status": "approved",
        "learning_ids": [record["learning_id"] for record in ordered],
        "lessons": [
            {
                "learning_id": record["learning_id"],
                "lesson": record["lesson"],
                "evidence_refs": list(record["evidence_refs"]),
                "scope": list(record["scope"]),
                "source_commit": record["source_commit"],
                "approved_by": record["approved_by"],
                "approved_at": record["approved_at"],
            }
            for record in ordered
        ],
    }


def apply_learning(pack: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """Apply a pack once to the matching Context; retries are no-ops."""
    if not isinstance(pack, dict) or pack.get("status") != "approved":
        raise LearningPackError("only an approved learning pack can be applied")
    if not isinstance(context, dict):
        raise LearningPackError("context must be an object")
    _non_empty_string(context.get("context_id"), "context.context_id")
    if context["context_id"] != pack.get("context_id"):
        raise LearningPackError("learning pack and context have different context_id")

    learning_refs = context.setdefault("learning_refs", [])
    if not isinstance(learning_refs, list) or not all(isinstance(item, str) for item in learning_refs):
        raise LearningPackError("context.learning_refs must be a list of strings")

    for learning_id in pack.get("learning_ids", []):
        if not isinstance(learning_id, str) or not learning_id.strip():
            raise LearningPackError("pack contains an invalid learning_id")
        if learning_id not in learning_refs:
            learning_refs.append(learning_id)

    context["learning_refs"] = sorted(set(learning_refs))
    context["context_version"] = int(context.get("context_version", 0)) + (
        1 if context.get("last_applied_pack") != pack.get("learning_ids") else 0
    )
    context["last_applied_pack"] = list(pack.get("learning_ids", []))
    return context


def load_json(path: Path) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise LearningPackError(f"file does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise LearningPackError(f"invalid JSON: {path}") from exc


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build and apply a Learning Pack")
    parser.add_argument("learning_json", type=Path)
    parser.add_argument("context_json", type=Path)
    args = parser.parse_args()
    try:
        records = load_json(args.learning_json)
        context = load_json(args.context_json)
        if not isinstance(records, list):
            raise LearningPackError("learning_json must contain a list")
        pack = build_learning_pack(records, context["context_id"])
        updated = apply_learning(pack, context)
        print(json.dumps({"pack": pack, "context": updated}, ensure_ascii=False, indent=2))
    except LearningPackError as exc:
        parser.error(str(exc))
