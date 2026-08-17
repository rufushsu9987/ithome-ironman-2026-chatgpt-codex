#!/usr/bin/env python3
"""Read-only, fail-closed acceptance coverage gate for an AI change run."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any


class CoverageError(ValueError):
    """Raised when an intent or coverage bundle is malformed."""


def _string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CoverageError(f"{field} must be a non-empty string")
    return value


def _strings(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise CoverageError(f"{field} must be a list of non-empty strings")
    if not value:
        raise CoverageError(f"{field} must not be empty")
    return list(value)


def _object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CoverageError(f"{field} must be an object")
    return value


def evaluate_coverage(intent: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    """Compare acceptance requirements with immutable, runner-produced evidence.

    The gate does not execute tests, infer missing links, or mutate inputs. It
    only reports whether every declared acceptance criterion has a passing,
    identity-matched evidence artifact.
    """
    if not isinstance(intent, dict):
        raise CoverageError("intent must be an object")
    if not isinstance(evidence, dict):
        raise CoverageError("evidence must be an object")

    intent_id = _string(intent.get("intent_id"), "intent.intent_id")
    context_id = _string(intent.get("context_id"), "intent.context_id")
    source_commit = _string(intent.get("source_commit"), "intent.source_commit")
    acceptance_ids = _strings(intent.get("acceptance_ids"), "intent.acceptance_ids")

    evidence_id = _string(evidence.get("evidence_id"), "evidence.evidence_id")
    evidence_intent = _string(evidence.get("intent_id"), "evidence.intent_id")
    evidence_context = _string(evidence.get("context_id"), "evidence.context_id")
    evidence_commit = _string(evidence.get("source_commit"), "evidence.source_commit")
    observation_id = _string(evidence.get("observation_id"), "evidence.observation_id")
    _string(evidence.get("captured_at"), "evidence.captured_at")

    results = evidence.get("acceptance_results")
    if not isinstance(results, list) or not results:
        raise CoverageError("evidence.acceptance_results must be a non-empty list")
    artifacts = evidence.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise CoverageError("evidence.artifacts must be a non-empty list")

    reasons: list[str] = []
    if intent_id != evidence_intent:
        reasons.append("intent_id_mismatch")
    if context_id != evidence_context:
        reasons.append("context_id_mismatch")
    if source_commit != evidence_commit:
        reasons.append("source_commit_mismatch")

    artifact_by_id: dict[str, dict[str, Any]] = {}
    artifact_ids: list[str] = []
    for index, raw in enumerate(artifacts):
        artifact = _object(raw, f"evidence.artifacts[{index}]")
        artifact_id = _string(artifact.get("artifact_id"), f"evidence.artifacts[{index}].artifact_id")
        artifact_commit = _string(artifact.get("source_commit"), f"evidence.artifacts[{index}].source_commit")
        artifact_acceptance_ids = _strings(
            artifact.get("acceptance_ids"), f"evidence.artifacts[{index}].acceptance_ids"
        )
        artifact_ids.append(artifact_id)
        artifact_by_id.setdefault(artifact_id, artifact)
        if artifact_commit != source_commit:
            reasons.append(f"evidence_source_commit_mismatch:{artifact_id}")
        for acceptance_id in artifact_acceptance_ids:
            if acceptance_id not in acceptance_ids:
                reasons.append(f"acceptance_unknown:{acceptance_id}")
    if len(artifact_ids) != len(set(artifact_ids)):
        reasons.append("duplicate_evidence_id")

    result_by_id: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(results):
        result = _object(raw, f"evidence.acceptance_results[{index}]")
        acceptance_id = _string(result.get("acceptance_id"), f"evidence.acceptance_results[{index}].acceptance_id")
        status = _string(result.get("status"), f"evidence.acceptance_results[{index}].status")
        evidence_refs = result.get("evidence_ids")
        if not isinstance(evidence_refs, list) or not all(isinstance(item, str) and item.strip() for item in evidence_refs):
            raise CoverageError(f"evidence.acceptance_results[{index}].evidence_ids must be a list of strings")
        if acceptance_id in result_by_id:
            reasons.append(f"acceptance_duplicate:{acceptance_id}")
        else:
            result_by_id[acceptance_id] = result
        if acceptance_id not in acceptance_ids:
            reasons.append(f"acceptance_unknown:{acceptance_id}")
            continue
        if status != "passed":
            reasons.append(f"acceptance_not_passed:{acceptance_id}")
        if not evidence_refs:
            reasons.append(f"evidence_missing:{acceptance_id}")
        for evidence_ref in evidence_refs:
            artifact = artifact_by_id.get(evidence_ref)
            if artifact is None:
                reasons.append(f"evidence_missing:{acceptance_id}:{evidence_ref}")
            elif acceptance_id not in artifact.get("acceptance_ids", []):
                reasons.append(f"evidence_not_linked:{acceptance_id}:{evidence_ref}")

    for acceptance_id in acceptance_ids:
        if acceptance_id not in result_by_id:
            reasons.append(f"acceptance_missing:{acceptance_id}")

    reasons = list(dict.fromkeys(reasons))
    return {
        "allowed": not reasons,
        "state": "covered" if not reasons else "blocked",
        "reasons": reasons,
        "intent": copy.deepcopy(intent),
        "input": copy.deepcopy(evidence),
        "checks": {
            "intent_id": intent_id == evidence_intent,
            "context_id": context_id == evidence_context,
            "source_commit": source_commit == evidence_commit,
            "acceptance_count": len(acceptance_ids),
            "acceptance_results": len(result_by_id),
            "all_acceptances_present": all(item in result_by_id for item in acceptance_ids),
            "all_acceptances_passed": all(
                result_by_id.get(item, {}).get("status") == "passed" for item in acceptance_ids
            ),
            "all_acceptances_have_linked_evidence": all(
                bool(result_by_id.get(item, {}).get("evidence_ids"))
                and all(
                    item in artifact_by_id.get(ref, {}).get("acceptance_ids", [])
                    for ref in result_by_id.get(item, {}).get("evidence_ids", [])
                )
                for item in acceptance_ids
                if item in result_by_id
            ),
            "evidence_ids_unique": len(artifact_ids) == len(set(artifact_ids)),
            "evidence_id": evidence_id,
            "observation_id": observation_id,
        },
    }


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CoverageError(f"file does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CoverageError(f"invalid JSON: {path}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify every acceptance criterion has passing linked evidence")
    parser.add_argument("intent_json", type=Path)
    parser.add_argument("evidence_json", type=Path)
    args = parser.parse_args()
    try:
        report = evaluate_coverage(load_json(args.intent_json), load_json(args.evidence_json))
    except CoverageError as exc:
        parser.error(str(exc))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["allowed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
