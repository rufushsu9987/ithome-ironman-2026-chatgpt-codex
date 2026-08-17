#!/usr/bin/env python3
"""Read-only, deterministic gate for a release candidate.

The gate verifies that an already-promoted artifact bundle is safe to offer to a
release owner. It never deploys, changes traffic, copies artifacts, or changes
its input objects.
"""
from __future__ import annotations

import argparse
import copy
import json
from datetime import datetime
from pathlib import Path
from typing import Any


class ReleaseCandidateError(ValueError):
    """Raised when an intent or observation is malformed."""


def _string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReleaseCandidateError(f"{field} must be a non-empty string")
    return value


def _object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ReleaseCandidateError(f"{field} must be an object")
    return value


def _list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise ReleaseCandidateError(f"{field} must be a list")
    return list(value)


def _parse_time(value: Any, field: str) -> datetime:
    text = _string(value, field)
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ReleaseCandidateError(f"{field} must be an ISO-8601 timestamp") from exc


def _same_identity(intent: dict[str, str], observed: dict[str, Any], reasons: list[str]) -> None:
    for field in ("intent_id", "run_id", "source_commit", "input_digest", "environment_id", "candidate_id"):
        if intent[field] != observed[field]:
            reasons.append(f"{field}_mismatch")


def evaluate_release_candidate(intent: dict[str, Any], observed: dict[str, Any]) -> dict[str, Any]:
    """Return a deterministic release-candidate decision without mutation."""
    if not isinstance(intent, dict):
        raise ReleaseCandidateError("intent must be an object")
    if not isinstance(observed, dict):
        raise ReleaseCandidateError("observed must be an object")

    intent_fields = {
        field: _string(intent.get(field), f"intent.{field}")
        for field in (
            "intent_id",
            "run_id",
            "source_commit",
            "input_digest",
            "environment_id",
            "candidate_id",
            "target",
            "owner",
            "rollback_artifact_id",
            "rollback_digest",
        )
    }
    window = _object(intent.get("release_window"), "intent.release_window")
    window_start = _parse_time(window.get("start"), "intent.release_window.start")
    window_end = _parse_time(window.get("end"), "intent.release_window.end")
    if window_end <= window_start:
        raise ReleaseCandidateError("intent.release_window.end must be after start")

    required_checks_raw = _list(intent.get("required_checks"), "intent.required_checks")
    required_checks = [_string(value, "intent.required_checks item") for value in required_checks_raw]
    expected_raw = _list(intent.get("expected_artifacts"), "intent.expected_artifacts")
    expected: dict[str, dict[str, str]] = {}
    expected_ids: list[str] = []
    for index, raw in enumerate(expected_raw):
        item = _object(raw, f"intent.expected_artifacts[{index}]")
        artifact_id = _string(item.get("artifact_id"), f"intent.expected_artifacts[{index}].artifact_id")
        digest = _string(item.get("artifact_digest"), f"intent.expected_artifacts[{index}].artifact_digest")
        if artifact_id in expected:
            raise ReleaseCandidateError(f"duplicate expected artifact: {artifact_id}")
        expected[artifact_id] = {"artifact_digest": digest}
        expected_ids.append(artifact_id)

    observed_identity = {
        field: _string(observed.get(field), f"observed.{field}")
        for field in (
            "intent_id",
            "run_id",
            "source_commit",
            "input_digest",
            "environment_id",
            "candidate_id",
        )
    }
    reasons: list[str] = []
    _same_identity(intent_fields, observed_identity, reasons)
    if observed.get("target") != intent_fields["target"]:
        reasons.append("target_mismatch")

    observed_now = _parse_time(observed.get("now"), "observed.now")
    if observed_now < window_start:
        reasons.append("release_window_not_open")
    elif observed_now >= window_end:
        reasons.append("release_window_expired")

    checks = _object(observed.get("checks"), "observed.checks")
    for check_name in required_checks:
        result = checks.get(check_name)
        if result is None:
            reasons.append(f"check_missing:{check_name}")
        elif result != "passed":
            reasons.append(f"check_not_passed:{check_name}")

    artifacts_raw = _list(observed.get("artifacts"), "observed.artifacts")
    artifact_by_id: dict[str, dict[str, Any]] = {}
    observed_ids: list[str] = []
    for index, raw in enumerate(artifacts_raw):
        item = _object(raw, f"observed.artifacts[{index}]")
        artifact_id = _string(item.get("artifact_id"), f"observed.artifacts[{index}].artifact_id")
        status = _string(item.get("status"), f"observed.artifacts[{index}].status")
        digest = _string(item.get("artifact_digest"), f"observed.artifacts[{index}].artifact_digest")
        produced_by_run = _string(item.get("produced_by_run"), f"observed.artifacts[{index}].produced_by_run")
        source_commit = _string(item.get("source_commit"), f"observed.artifacts[{index}].source_commit")
        input_digest = _string(item.get("input_digest"), f"observed.artifacts[{index}].input_digest")
        environment_id = _string(item.get("environment_id"), f"observed.artifacts[{index}].environment_id")
        target = _string(item.get("target"), f"observed.artifacts[{index}].target")
        observed_ids.append(artifact_id)
        if artifact_id in artifact_by_id:
            reasons.append(f"artifact_duplicate:{artifact_id}")
        else:
            artifact_by_id[artifact_id] = item
        if artifact_id not in expected:
            reasons.append(f"artifact_unknown:{artifact_id}")
            continue
        if status != "ready":
            reasons.append(f"artifact_not_ready:{artifact_id}")
        if produced_by_run != intent_fields["run_id"]:
            reasons.append(f"artifact_run_mismatch:{artifact_id}")
        if digest != expected[artifact_id]["artifact_digest"]:
            reasons.append(f"artifact_digest_mismatch:{artifact_id}")
        if source_commit != intent_fields["source_commit"]:
            reasons.append(f"artifact_source_mismatch:{artifact_id}")
        if input_digest != intent_fields["input_digest"]:
            reasons.append(f"artifact_input_mismatch:{artifact_id}")
        if environment_id != intent_fields["environment_id"]:
            reasons.append(f"artifact_environment_mismatch:{artifact_id}")
        if target != intent_fields["target"]:
            reasons.append(f"artifact_target_mismatch:{artifact_id}")

    for artifact_id in expected_ids:
        if artifact_id not in artifact_by_id:
            reasons.append(f"artifact_missing:{artifact_id}")

    rollback = _object(observed.get("rollback"), "observed.rollback")
    if rollback.get("ready") is not True:
        reasons.append("rollback_not_ready")
    if rollback.get("artifact_id") != intent_fields["rollback_artifact_id"]:
        reasons.append("rollback_artifact_mismatch")
    if rollback.get("artifact_digest") != intent_fields["rollback_digest"]:
        reasons.append("rollback_digest_mismatch")

    approval = _object(observed.get("approval"), "observed.approval")
    if approval.get("requested") is not True:
        reasons.append("approval_not_requested")
    if approval.get("granted") is not True:
        reasons.append("approval_not_granted")
    if approval.get("target") != intent_fields["target"]:
        reasons.append("approval_target_mismatch")
    if approval.get("owner") != intent_fields["owner"]:
        reasons.append("approval_owner_mismatch")

    reasons = list(dict.fromkeys(reasons))
    return {
        "allowed": not reasons,
        "state": "releasable" if not reasons else "blocked",
        "reasons": reasons,
        "intent": copy.deepcopy(intent),
        "input": copy.deepcopy(observed),
        "checks": {
            "identity": not any(reason.endswith("_mismatch") for reason in reasons if not reason.startswith(("artifact_", "approval_", "rollback_", "target_"))),
            "exact_artifact_set": all(artifact_id in artifact_by_id for artifact_id in expected_ids) and all(artifact_id in expected for artifact_id in observed_ids),
            "required_checks": not any(reason.startswith(("check_missing:", "check_not_passed:")) for reason in reasons),
            "release_window": not any(reason.startswith("release_window_") for reason in reasons),
            "rollback": not any(reason.startswith("rollback_") for reason in reasons),
            "approval": not any(reason.startswith("approval_") for reason in reasons),
            "artifact_count": {"expected": len(expected_ids), "observed": len(observed_ids)},
            "run_id": intent_fields["run_id"],
            "candidate_id": intent_fields["candidate_id"],
        },
    }


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ReleaseCandidateError(f"file does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ReleaseCandidateError(f"invalid JSON: {path}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify a release candidate without deploying it")
    parser.add_argument("intent_json", type=Path)
    parser.add_argument("observation_json", type=Path)
    args = parser.parse_args()
    try:
        report = evaluate_release_candidate(load_json(args.intent_json), load_json(args.observation_json))
    except ReleaseCandidateError as exc:
        parser.error(str(exc))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["allowed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
