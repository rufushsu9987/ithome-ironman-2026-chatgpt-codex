#!/usr/bin/env python3
"""Read-only, deterministic gate for promoting a verified artifact bundle."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any


class ArtifactPromotionError(ValueError):
    """Raised when an intent or observation is malformed."""


def _string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ArtifactPromotionError(f"{field} must be a non-empty string")
    return value


def _object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ArtifactPromotionError(f"{field} must be an object")
    return value


def _list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise ArtifactPromotionError(f"{field} must be a list")
    return list(value)


def _checks(value: Any, field: str) -> dict[str, str]:
    raw = _object(value, field)
    checks: dict[str, str] = {}
    for key, result in raw.items():
        checks[_string(key, f"{field} key")] = _string(result, f"{field}.{key}")
    return checks


def _identity_reasons(intent: dict[str, Any], observed: dict[str, Any], reasons: list[str]) -> None:
    for field in ("intent_id", "run_id", "source_commit", "input_digest", "environment_id"):
        if intent[field] != observed[field]:
            reasons.append(f"{field}_mismatch")


def evaluate_promotion(intent: dict[str, Any], observed: dict[str, Any]) -> dict[str, Any]:
    """Evaluate a promotion bundle without changing either input object."""
    if not isinstance(intent, dict):
        raise ArtifactPromotionError("intent must be an object")
    if not isinstance(observed, dict):
        raise ArtifactPromotionError("observed must be an object")

    intent_id = _string(intent.get("intent_id"), "intent.intent_id")
    run_id = _string(intent.get("run_id"), "intent.run_id")
    source_commit = _string(intent.get("source_commit"), "intent.source_commit")
    input_digest = _string(intent.get("input_digest"), "intent.input_digest")
    environment_id = _string(intent.get("environment_id"), "intent.environment_id")
    target = _string(intent.get("target"), "intent.target")
    owner = _string(intent.get("owner"), "intent.owner")

    expected_raw = _list(intent.get("expected_artifacts"), "intent.expected_artifacts")
    expected: dict[str, dict[str, Any]] = {}
    expected_ids: list[str] = []
    for index, raw in enumerate(expected_raw):
        item = _object(raw, f"intent.expected_artifacts[{index}]")
        artifact_id = _string(item.get("artifact_id"), f"intent.expected_artifacts[{index}].artifact_id")
        digest = _string(item.get("artifact_digest"), f"intent.expected_artifacts[{index}].artifact_digest")
        required = _list(item.get("required_checks"), f"intent.expected_artifacts[{index}].required_checks")
        required_checks = [_string(value, f"intent.expected_artifacts[{index}].required_checks") for value in required]
        if artifact_id in expected:
            raise ArtifactPromotionError(f"duplicate expected artifact: {artifact_id}")
        expected[artifact_id] = {"artifact_digest": digest, "required_checks": required_checks}
        expected_ids.append(artifact_id)

    observed_identity = {
        "intent_id": _string(observed.get("intent_id"), "observed.intent_id"),
        "run_id": _string(observed.get("run_id"), "observed.run_id"),
        "source_commit": _string(observed.get("source_commit"), "observed.source_commit"),
        "input_digest": _string(observed.get("input_digest"), "observed.input_digest"),
        "environment_id": _string(observed.get("environment_id"), "observed.environment_id"),
    }
    intent_identity = {
        "intent_id": intent_id,
        "run_id": run_id,
        "source_commit": source_commit,
        "input_digest": input_digest,
        "environment_id": environment_id,
    }
    reasons: list[str] = []
    _identity_reasons(intent_identity, observed_identity, reasons)

    promotion = _object(observed.get("promotion"), "observed.promotion")
    requested = promotion.get("requested")
    if requested is not True:
        reasons.append("promotion_not_requested")
    if promotion.get("target") != target:
        reasons.append("promotion_target_mismatch")
    if promotion.get("owner") != owner:
        reasons.append("promotion_owner_mismatch")

    artifacts_raw = _list(observed.get("artifacts"), "observed.artifacts")
    artifact_by_id: dict[str, dict[str, Any]] = {}
    observed_ids: list[str] = []
    for index, raw in enumerate(artifacts_raw):
        item = _object(raw, f"observed.artifacts[{index}]")
        artifact_id = _string(item.get("artifact_id"), f"observed.artifacts[{index}].artifact_id")
        status = _string(item.get("status"), f"observed.artifacts[{index}].status")
        digest = _string(item.get("artifact_digest"), f"observed.artifacts[{index}].artifact_digest")
        produced_by_run = _string(item.get("produced_by_run"), f"observed.artifacts[{index}].produced_by_run")
        artifact_source = _string(item.get("source_commit"), f"observed.artifacts[{index}].source_commit")
        artifact_input = _string(item.get("input_digest"), f"observed.artifacts[{index}].input_digest")
        artifact_environment = _string(item.get("environment_id"), f"observed.artifacts[{index}].environment_id")
        checks = _checks(item.get("checks"), f"observed.artifacts[{index}].checks")
        observed_ids.append(artifact_id)
        if artifact_id in artifact_by_id:
            reasons.append(f"artifact_duplicate:{artifact_id}")
        else:
            artifact_by_id[artifact_id] = item
        if artifact_id not in expected:
            reasons.append(f"artifact_unknown:{artifact_id}")
            continue
        spec = expected[artifact_id]
        if status != "ready":
            reasons.append(f"artifact_not_ready:{artifact_id}")
        if produced_by_run != run_id:
            reasons.append(f"artifact_run_mismatch:{artifact_id}")
        if digest != spec["artifact_digest"]:
            reasons.append(f"artifact_digest_mismatch:{artifact_id}")
        if artifact_source != source_commit:
            reasons.append(f"artifact_source_mismatch:{artifact_id}")
        if artifact_input != input_digest:
            reasons.append(f"artifact_input_mismatch:{artifact_id}")
        if artifact_environment != environment_id:
            reasons.append(f"artifact_environment_mismatch:{artifact_id}")
        for check_name in spec["required_checks"]:
            result = checks.get(check_name)
            if result is None:
                reasons.append(f"artifact_check_missing:{artifact_id}:{check_name}")
            elif result != "passed":
                reasons.append(f"artifact_check_not_passed:{artifact_id}:{check_name}")

    for artifact_id in expected_ids:
        if artifact_id not in artifact_by_id:
            reasons.append(f"artifact_missing:{artifact_id}")

    reasons = list(dict.fromkeys(reasons))
    return {
        "allowed": not reasons,
        "state": "promotable" if not reasons else "blocked",
        "reasons": reasons,
        "intent": copy.deepcopy(intent),
        "input": copy.deepcopy(observed),
        "checks": {
            "identity": not any(reason.endswith("_mismatch") for reason in reasons if reason.split(":", 1)[0] in {"intent_id_mismatch", "run_id_mismatch", "source_commit_mismatch", "input_digest_mismatch", "environment_id_mismatch"}),
            "exact_artifact_set": all(artifact_id in artifact_by_id for artifact_id in expected_ids) and all(artifact_id in expected for artifact_id in observed_ids),
            "artifact_count": {"expected": len(expected_ids), "observed": len(observed_ids)},
            "required_checks": not any(reason.startswith("artifact_check_") for reason in reasons),
            "promotion_request": not any(reason.startswith("promotion_") for reason in reasons),
            "run_id": run_id,
        },
    }


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ArtifactPromotionError(f"file does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ArtifactPromotionError(f"invalid JSON: {path}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify that an artifact bundle is safe to offer for promotion")
    parser.add_argument("intent_json", type=Path)
    parser.add_argument("observation_json", type=Path)
    args = parser.parse_args()
    try:
        report = evaluate_promotion(load_json(args.intent_json), load_json(args.observation_json))
    except ArtifactPromotionError as exc:
        parser.error(str(exc))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["allowed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
