#!/usr/bin/env python3
"""Read-only, fail-closed traceability gate for an AI change run."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any


class TraceabilityError(ValueError):
    """Raised when an intent or trace bundle is malformed."""


def _string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TraceabilityError(f"{field} must be a non-empty string")
    return value


def _strings(value: Any, field: str, *, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise TraceabilityError(f"{field} must be a list of non-empty strings")
    if not allow_empty and not value:
        raise TraceabilityError(f"{field} must not be empty")
    return list(value)


def _object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TraceabilityError(f"{field} must be an object")
    return value


def _unique(values: list[str], reason: str, reasons: list[str]) -> None:
    if len(values) != len(set(values)):
        reasons.append(reason)


def evaluate_traceability(intent: dict[str, Any], trace: dict[str, Any]) -> dict[str, Any]:
    """Check that requirements, changes, evidence, and release approval share identity.

    The gate does not run tests, infer links, mutate inputs, or grant approval. It
    only evaluates the immutable facts supplied by the runner and returns stable
    reason codes for missing or mismatched links.
    """
    if not isinstance(intent, dict):
        raise TraceabilityError("intent must be an object")
    if not isinstance(trace, dict):
        raise TraceabilityError("trace must be an object")

    intent_id = _string(intent.get("intent_id"), "intent.intent_id")
    context_id = _string(intent.get("context_id"), "intent.context_id")
    source_commit = _string(intent.get("source_commit"), "intent.source_commit")
    acceptance_ids = _strings(intent.get("acceptance_ids"), "intent.acceptance_ids")
    change_ids = _strings(intent.get("change_ids"), "intent.change_ids")
    release_owner = _string(intent.get("release_owner"), "intent.release_owner")

    trace_id = _string(trace.get("trace_id"), "trace.trace_id")
    trace_intent = _string(trace.get("intent_id"), "trace.intent_id")
    trace_context = _string(trace.get("context_id"), "trace.context_id")
    trace_commit = _string(trace.get("source_commit"), "trace.source_commit")
    observation_id = _string(trace.get("observation_id"), "trace.observation_id")
    _string(trace.get("captured_at"), "trace.captured_at")

    results = trace.get("acceptance_results")
    if not isinstance(results, list) or not results:
        raise TraceabilityError("trace.acceptance_results must be a non-empty list")
    changes = trace.get("changes")
    if not isinstance(changes, list):
        raise TraceabilityError("trace.changes must be a list")
    artifacts = trace.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise TraceabilityError("trace.artifacts must be a non-empty list")
    release = _object(trace.get("release"), "trace.release")
    release_status = _string(release.get("status"), "trace.release.status")
    approved_by = _string(release.get("approved_by"), "trace.release.approved_by")
    _string(release.get("approval_id"), "trace.release.approval_id")
    release_commit = _string(release.get("source_commit"), "trace.release.source_commit")

    reasons: list[str] = []
    if intent_id != trace_intent:
        reasons.append("intent_id_mismatch")
    if context_id != trace_context:
        reasons.append("context_id_mismatch")
    if source_commit != trace_commit:
        reasons.append("source_commit_mismatch")
    if release_commit != source_commit:
        reasons.append("release_source_commit_mismatch")
    if release_status != "approved":
        reasons.append("release_not_approved")
    if approved_by != release_owner:
        reasons.append("release_owner_mismatch")

    artifact_by_id: dict[str, dict[str, Any]] = {}
    artifact_ids: list[str] = []
    for index, raw in enumerate(artifacts):
        item = _object(raw, f"trace.artifacts[{index}]")
        artifact_id = _string(item.get("artifact_id"), f"trace.artifacts[{index}].artifact_id")
        artifact_commit = _string(item.get("source_commit"), f"trace.artifacts[{index}].source_commit")
        artifact_acceptance_ids = _strings(
            item.get("acceptance_ids"), f"trace.artifacts[{index}].acceptance_ids"
        )
        artifact_change_ids = _strings(item.get("change_ids", []), f"trace.artifacts[{index}].change_ids", allow_empty=True)
        artifact_ids.append(artifact_id)
        artifact_by_id.setdefault(artifact_id, item)
        if artifact_commit != source_commit:
            reasons.append(f"artifact_source_commit_mismatch:{artifact_id}")
        for acceptance_id in artifact_acceptance_ids:
            if acceptance_id not in acceptance_ids:
                reasons.append(f"acceptance_unknown:{acceptance_id}")
        for change_id in artifact_change_ids:
            if change_id not in change_ids:
                reasons.append(f"change_unknown:{change_id}")
    _unique(artifact_ids, "duplicate_artifact_id", reasons)

    result_by_id: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(results):
        item = _object(raw, f"trace.acceptance_results[{index}]")
        acceptance_id = _string(item.get("acceptance_id"), f"trace.acceptance_results[{index}].acceptance_id")
        status = _string(item.get("status"), f"trace.acceptance_results[{index}].status")
        evidence_ids = item.get("evidence_ids")
        if not isinstance(evidence_ids, list) or not all(isinstance(ref, str) and ref.strip() for ref in evidence_ids):
            raise TraceabilityError(f"trace.acceptance_results[{index}].evidence_ids must be a list of strings")
        if acceptance_id in result_by_id:
            reasons.append(f"acceptance_duplicate:{acceptance_id}")
        else:
            result_by_id[acceptance_id] = item
        if acceptance_id not in acceptance_ids:
            reasons.append(f"acceptance_unknown:{acceptance_id}")
            continue
        if status != "passed":
            reasons.append(f"acceptance_not_passed:{acceptance_id}")
        if not evidence_ids:
            reasons.append(f"artifact_missing:{acceptance_id}")
        for artifact_id in evidence_ids:
            artifact = artifact_by_id.get(artifact_id)
            if artifact is None:
                reasons.append(f"artifact_missing:{acceptance_id}:{artifact_id}")
            elif acceptance_id not in artifact.get("acceptance_ids", []):
                reasons.append(f"artifact_not_linked:{acceptance_id}:{artifact_id}")

    for acceptance_id in acceptance_ids:
        if acceptance_id not in result_by_id:
            reasons.append(f"acceptance_missing:{acceptance_id}")

    change_by_id: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(changes):
        item = _object(raw, f"trace.changes[{index}]")
        change_id = _string(item.get("change_id"), f"trace.changes[{index}].change_id")
        artifact_refs = item.get("artifact_ids")
        if not isinstance(artifact_refs, list) or not all(isinstance(ref, str) and ref.strip() for ref in artifact_refs):
            raise TraceabilityError(f"trace.changes[{index}].artifact_ids must be a list of strings")
        if change_id in change_by_id:
            reasons.append(f"change_duplicate:{change_id}")
        else:
            change_by_id[change_id] = item
        if change_id not in change_ids:
            reasons.append(f"change_unknown:{change_id}")
        if not artifact_refs:
            reasons.append(f"change_artifact_missing:{change_id}")
        for artifact_id in artifact_refs:
            artifact = artifact_by_id.get(artifact_id)
            if artifact is None:
                reasons.append(f"change_artifact_missing:{change_id}:{artifact_id}")
            elif change_id not in artifact.get("change_ids", []):
                reasons.append(f"change_artifact_not_linked:{change_id}:{artifact_id}")

    for change_id in change_ids:
        if change_id not in change_by_id:
            reasons.append(f"change_missing:{change_id}")

    reasons = list(dict.fromkeys(reasons))
    all_acceptances_present = all(item in result_by_id for item in acceptance_ids)
    all_acceptances_traceable = all(
        result_by_id.get(item, {}).get("status") == "passed"
        and bool(result_by_id.get(item, {}).get("evidence_ids"))
        and all(
            item in artifact_by_id.get(ref, {}).get("acceptance_ids", [])
            for ref in result_by_id.get(item, {}).get("evidence_ids", [])
        )
        for item in acceptance_ids
        if item in result_by_id
    ) and all_acceptances_present
    all_changes_present = all(item in change_by_id for item in change_ids)
    all_changes_traceable = all(
        bool(change_by_id.get(item, {}).get("artifact_ids"))
        and all(
            item in artifact_by_id.get(ref, {}).get("change_ids", [])
            for ref in change_by_id.get(item, {}).get("artifact_ids", [])
        )
        for item in change_ids
        if item in change_by_id
    ) and all_changes_present
    release_approved = (
        release_status == "approved"
        and approved_by == release_owner
        and release_commit == source_commit
    )

    return {
        "allowed": not reasons,
        "state": "traceable" if not reasons else "blocked",
        "reasons": reasons,
        "intent": copy.deepcopy(intent),
        "input": copy.deepcopy(trace),
        "checks": {
            "intent_id": intent_id == trace_intent,
            "context_id": context_id == trace_context,
            "source_commit": source_commit == trace_commit,
            "release_source_commit": release_commit == source_commit,
            "all_acceptances_present": all_acceptances_present,
            "all_acceptances_traceable": all_acceptances_traceable,
            "all_changes_present": all_changes_present,
            "all_changes_traceable": all_changes_traceable,
            "release_approved": release_approved,
            "artifact_ids_unique": len(artifact_ids) == len(set(artifact_ids)),
            "trace_id": trace_id,
            "observation_id": observation_id,
            "acceptance_count": len(acceptance_ids),
            "change_count": len(change_ids),
            "artifact_count": len(artifacts),
        },
    }


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise TraceabilityError(f"file does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise TraceabilityError(f"invalid JSON: {path}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify requirements, changes, evidence, and release approval share one identity")
    parser.add_argument("intent_json", type=Path)
    parser.add_argument("trace_json", type=Path)
    args = parser.parse_args()
    try:
        report = evaluate_traceability(load_json(args.intent_json), load_json(args.trace_json))
    except TraceabilityError as exc:
        parser.error(str(exc))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["allowed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
