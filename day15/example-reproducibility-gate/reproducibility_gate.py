#!/usr/bin/env python3
"""Read-only, deterministic gate for reproducible AI change runs."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any


class ReproducibilityError(ValueError):
    """Raised when an intent or run record is malformed."""


def _string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReproducibilityError(f"{field} must be a non-empty string")
    return value


def _strings(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item.strip() for item in value):
        raise ReproducibilityError(f"{field} must be a non-empty list of strings")
    return list(value)


def _object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ReproducibilityError(f"{field} must be an object")
    return value


def _unique(values: list[str], reason: str, reasons: list[str]) -> None:
    if len(values) != len(set(values)):
        reasons.append(reason)


def evaluate_reproducibility(intent: dict[str, Any], run: dict[str, Any]) -> dict[str, Any]:
    """Compare declared inputs with an observed run without mutating either object."""
    if not isinstance(intent, dict):
        raise ReproducibilityError("intent must be an object")
    if not isinstance(run, dict):
        raise ReproducibilityError("run must be an object")

    intent_id = _string(intent.get("intent_id"), "intent.intent_id")
    context_id = _string(intent.get("context_id"), "intent.context_id")
    source_commit = _string(intent.get("source_commit"), "intent.source_commit")
    input_digest = _string(intent.get("input_digest"), "intent.input_digest")
    environment_id = _string(intent.get("environment_id"), "intent.environment_id")
    toolchain = _object(intent.get("toolchain"), "intent.toolchain")
    lock_digest = _string(intent.get("dependencies_lock_digest"), "intent.dependencies_lock_digest")
    expected_outputs = _strings(intent.get("expected_outputs"), "intent.expected_outputs")

    run_id = _string(run.get("run_id"), "run.run_id")
    run_intent_id = _string(run.get("intent_id"), "run.intent_id")
    run_context_id = _string(run.get("context_id"), "run.context_id")
    run_source_commit = _string(run.get("source_commit"), "run.source_commit")
    run_input_digest = _string(run.get("input_digest"), "run.input_digest")
    run_environment_id = _string(run.get("environment_id"), "run.environment_id")
    run_toolchain = _object(run.get("toolchain"), "run.toolchain")
    run_lock_digest = _string(run.get("dependencies_lock_digest"), "run.dependencies_lock_digest")
    _string(run.get("captured_at"), "run.captured_at")

    outputs = run.get("outputs")
    if not isinstance(outputs, list):
        raise ReproducibilityError("run.outputs must be a list")

    reasons: list[str] = []
    if intent_id != run_intent_id:
        reasons.append("intent_id_mismatch")
    if context_id != run_context_id:
        reasons.append("context_id_mismatch")
    if source_commit != run_source_commit:
        reasons.append("source_commit_mismatch")
    if input_digest != run_input_digest:
        reasons.append("input_digest_mismatch")
    if environment_id != run_environment_id:
        reasons.append("environment_id_mismatch")
    if lock_digest != run_lock_digest:
        reasons.append("dependency_lock_mismatch")

    toolchain_keys = sorted(set(toolchain) | set(run_toolchain))
    toolchain_matches = True
    for key in toolchain_keys:
        if toolchain.get(key) != run_toolchain.get(key):
            toolchain_matches = False
            reasons.append(f"toolchain_mismatch:{key}")

    output_by_id: dict[str, dict[str, Any]] = {}
    output_ids: list[str] = []
    for index, raw in enumerate(outputs):
        item = _object(raw, f"run.outputs[{index}]")
        output_id = _string(item.get("output_id"), f"run.outputs[{index}].output_id")
        status = _string(item.get("status"), f"run.outputs[{index}].status")
        output_source = _string(item.get("source_commit"), f"run.outputs[{index}].source_commit")
        output_input = _string(item.get("input_digest"), f"run.outputs[{index}].input_digest")
        output_environment = _string(item.get("environment_id"), f"run.outputs[{index}].environment_id")
        _string(item.get("artifact_digest"), f"run.outputs[{index}].artifact_digest")
        output_ids.append(output_id)
        if output_id in output_by_id:
            reasons.append(f"output_duplicate:{output_id}")
        else:
            output_by_id[output_id] = item
        if status != "ready":
            reasons.append(f"output_not_ready:{output_id}")
        if output_source != source_commit:
            reasons.append(f"output_source_commit_mismatch:{output_id}")
        if output_input != input_digest:
            reasons.append(f"output_input_digest_mismatch:{output_id}")
        if output_environment != environment_id:
            reasons.append(f"output_environment_mismatch:{output_id}")
    _unique(output_ids, "output_ids_not_unique", reasons)

    for expected in expected_outputs:
        if expected not in output_by_id:
            reasons.append(f"output_missing:{expected}")
    for observed in output_ids:
        if observed not in expected_outputs:
            reasons.append(f"output_unknown:{observed}")

    reasons = list(dict.fromkeys(reasons))
    outputs_ready = all(
        output_by_id.get(expected, {}).get("status") == "ready"
        and output_by_id.get(expected, {}).get("source_commit") == source_commit
        and output_by_id.get(expected, {}).get("input_digest") == input_digest
        and output_by_id.get(expected, {}).get("environment_id") == environment_id
        for expected in expected_outputs
    ) and all(expected in output_by_id for expected in expected_outputs)

    return {
        "allowed": not reasons,
        "state": "reproducible" if not reasons else "blocked",
        "reasons": reasons,
        "intent": copy.deepcopy(intent),
        "input": copy.deepcopy(run),
        "checks": {
            "intent_id": intent_id == run_intent_id,
            "context_id": context_id == run_context_id,
            "source_commit": source_commit == run_source_commit,
            "input_digest": input_digest == run_input_digest,
            "environment_id": environment_id == run_environment_id,
            "toolchain": toolchain_matches,
            "dependency_lock": lock_digest == run_lock_digest,
            "outputs_ready": outputs_ready,
            "expected_output_count": len(expected_outputs),
            "observed_output_count": len(outputs),
            "run_id": run_id,
        },
    }


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ReproducibilityError(f"file does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ReproducibilityError(f"invalid JSON: {path}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify that an AI change run can be reproduced from declared identity")
    parser.add_argument("intent_json", type=Path)
    parser.add_argument("run_json", type=Path)
    args = parser.parse_args()
    try:
        report = evaluate_reproducibility(load_json(args.intent_json), load_json(args.run_json))
    except ReproducibilityError as exc:
        parser.error(str(exc))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["allowed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
