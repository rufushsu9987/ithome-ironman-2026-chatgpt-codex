#!/usr/bin/env python3
"""Read-only, fail-closed evidence binding gate for an AI change run."""
from __future__ import annotations

import argparse
import copy
import fnmatch
import json
from pathlib import Path
from typing import Any


class BindingError(ValueError):
    """Raised when an intent or evidence bundle is malformed."""


def _string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BindingError(f"{field} must be a non-empty string")
    return value


def _strings(value: Any, field: str, *, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise BindingError(f"{field} must be a list of non-empty strings")
    if not allow_empty and not value:
        raise BindingError(f"{field} must not be empty")
    return list(value)


def _object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise BindingError(f"{field} must be an object")
    return value


def _matches_any(value: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(value, pattern) for pattern in patterns)


def evaluate_binding(intent: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    """Compare a frozen intent with one immutable evidence bundle.

    The runner creates the evidence. This function only validates identity,
    scope, required evidence and artifact metadata, returning deterministic
    reason codes without modifying either input.
    """
    if not isinstance(intent, dict):
        raise BindingError("intent must be an object")
    if not isinstance(evidence, dict):
        raise BindingError("evidence must be an object")

    intent_id = _string(intent.get("intent_id"), "intent.intent_id")
    context_id = _string(intent.get("context_id"), "intent.context_id")
    source_commit = _string(intent.get("source_commit"), "intent.source_commit")
    allowed_paths = _strings(intent.get("allowed_paths"), "intent.allowed_paths")
    forbidden_paths = _strings(intent.get("forbidden_paths", []), "intent.forbidden_paths", allow_empty=True)
    required_kinds = _strings(intent.get("required_evidence"), "intent.required_evidence")
    acceptance_ids = _strings(intent.get("acceptance_ids"), "intent.acceptance_ids")

    evidence_id = _string(evidence.get("evidence_id"), "evidence.evidence_id")
    evidence_intent = _string(evidence.get("intent_id"), "evidence.intent_id")
    evidence_context = _string(evidence.get("context_id"), "evidence.context_id")
    evidence_commit = _string(evidence.get("source_commit"), "evidence.source_commit")
    observation_id = _string(evidence.get("observation_id"), "evidence.observation_id")
    _string(evidence.get("captured_at"), "evidence.captured_at")

    diff = _object(evidence.get("diff"), "evidence.diff")
    diff_paths = _strings(diff.get("paths"), "evidence.diff.paths")
    tests = _object(evidence.get("tests"), "evidence.tests")
    test_status = _string(tests.get("status"), "evidence.tests.status")
    test_digest = _string(tests.get("result_digest"), "evidence.tests.result_digest")
    _string(tests.get("run_id"), "evidence.tests.run_id")
    review = _object(evidence.get("review"), "evidence.review")
    review_status = _string(review.get("status"), "evidence.review.status")
    _string(review.get("review_id"), "evidence.review.review_id")
    artifacts = evidence.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise BindingError("evidence.artifacts must be a non-empty list")

    reasons: list[str] = []
    if intent_id != evidence_intent:
        reasons.append("intent_id_mismatch")
    if context_id != evidence_context:
        reasons.append("context_id_mismatch")
    if source_commit != evidence_commit:
        reasons.append("source_commit_mismatch")

    for path in diff_paths:
        if _matches_any(path, forbidden_paths):
            reasons.append(f"path_forbidden:{path}")
        elif not _matches_any(path, allowed_paths):
            reasons.append(f"path_out_of_scope:{path}")

    if test_status != "passed":
        reasons.append("test_not_passed")
    if not test_digest.strip().startswith("sha256:"):
        reasons.append("test_result_digest_missing")
    if review_status != "approved":
        reasons.append("review_not_approved")

    artifact_kinds: list[str] = []
    artifact_ids: list[str] = []
    for index, artifact in enumerate(artifacts):
        item = _object(artifact, f"evidence.artifacts[{index}]")
        kind = _string(item.get("kind"), f"evidence.artifacts[{index}].kind")
        artifact_id = _string(item.get("artifact_id"), f"evidence.artifacts[{index}].artifact_id")
        artifact_commit = _string(item.get("source_commit"), f"evidence.artifacts[{index}].source_commit")
        artifact_kinds.append(kind)
        artifact_ids.append(artifact_id)
        if artifact_commit != source_commit:
            reasons.append(f"artifact_source_commit_mismatch:{artifact_id}")
    if len(artifact_ids) != len(set(artifact_ids)):
        reasons.append("duplicate_artifact_id")
    for kind in required_kinds:
        if kind not in artifact_kinds:
            reasons.append(f"required_evidence_missing:{kind}")

    reasons = list(dict.fromkeys(reasons))
    return {
        "allowed": not reasons,
        "state": "bound" if not reasons else "blocked",
        "reasons": reasons,
        "intent": copy.deepcopy(intent),
        "input": copy.deepcopy(evidence),
        "checks": {
            "intent_id": intent_id == evidence_intent,
            "context_id": context_id == evidence_context,
            "source_commit": source_commit == evidence_commit,
            "paths_in_scope": all(
                _matches_any(path, allowed_paths) and not _matches_any(path, forbidden_paths)
                for path in diff_paths
            ),
            "tests_passed": test_status == "passed",
            "test_result_digest": test_digest.startswith("sha256:"),
            "review_approved": review_status == "approved",
            "required_evidence": sorted(set(required_kinds).intersection(artifact_kinds)) == sorted(set(required_kinds)),
            "artifact_ids_unique": len(artifact_ids) == len(set(artifact_ids)),
            "evidence_id": evidence_id,
            "observation_id": observation_id,
            "acceptance_ids": list(acceptance_ids),
            "artifact_count": len(artifacts),
        },
    }


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise BindingError(f"file does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise BindingError(f"invalid JSON: {path}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description="Bind diff, tests and review to one Change Intent")
    parser.add_argument("intent_json", type=Path)
    parser.add_argument("evidence_json", type=Path)
    args = parser.parse_args()
    try:
        intent = load_json(args.intent_json)
        evidence = load_json(args.evidence_json)
        report = evaluate_binding(intent, evidence)
    except BindingError as exc:
        parser.error(str(exc))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["allowed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
