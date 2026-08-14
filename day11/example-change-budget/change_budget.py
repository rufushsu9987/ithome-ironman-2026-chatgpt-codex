#!/usr/bin/env python3
"""Read-only, fail-closed change budget gate for an AI execution run."""
from __future__ import annotations

import argparse
import copy
import fnmatch
import json
from pathlib import Path
from typing import Any


class BudgetError(ValueError):
    """Raised when a Change Intent or runtime observation is malformed."""


def _string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BudgetError(f"{field} must be a non-empty string")
    return value


def _strings(value: Any, field: str, *, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise BudgetError(f"{field} must be a list of non-empty strings")
    if not allow_empty and not value:
        raise BudgetError(f"{field} must not be empty")
    return list(value)


def _nonnegative_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise BudgetError(f"{field} must be a non-negative integer")
    return value


def _matches_any(value: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(value, pattern) for pattern in patterns)


def evaluate_budget(intent: dict[str, Any], observed: dict[str, Any]) -> dict[str, Any]:
    """Evaluate a runtime observation against a frozen Change Intent.

    The function is deliberately read-only.  The runner is responsible for
    collecting the observation; this gate only compares facts and returns a
    deterministic report with actionable reason codes.
    """
    if not isinstance(intent, dict):
        raise BudgetError("intent must be an object")
    if not isinstance(observed, dict):
        raise BudgetError("observed must be an object")

    intent_id = _string(intent.get("intent_id"), "intent.intent_id")
    intent_context = _string(intent.get("context_id"), "intent.context_id")
    intent_commit = _string(intent.get("source_commit"), "intent.source_commit")
    allowed_paths = _strings(intent.get("allowed_paths"), "intent.allowed_paths")
    forbidden_paths = _strings(intent.get("forbidden_paths", []), "intent.forbidden_paths", allow_empty=True)
    allowed_commands = _strings(intent.get("allowed_commands"), "intent.allowed_commands")
    acceptance_ids = _strings(intent.get("acceptance_ids"), "intent.acceptance_ids")
    max_files = _nonnegative_int(intent.get("max_files_changed"), "intent.max_files_changed")
    max_diff = _nonnegative_int(intent.get("max_diff_lines"), "intent.max_diff_lines")
    max_commands = _nonnegative_int(intent.get("max_commands"), "intent.max_commands")

    observed_context = _string(observed.get("context_id"), "observed.context_id")
    observed_commit = _string(observed.get("source_commit"), "observed.source_commit")
    paths = _strings(observed.get("paths_changed"), "observed.paths_changed")
    commands = _strings(observed.get("commands"), "observed.commands", allow_empty=True)
    diff_added = _nonnegative_int(observed.get("diff_added"), "observed.diff_added")
    diff_removed = _nonnegative_int(observed.get("diff_removed"), "observed.diff_removed")
    checked_at = _string(observed.get("checked_at"), "observed.checked_at")

    reasons: list[str] = []
    if intent_context != observed_context:
        reasons.append("context_id_mismatch")
    if intent_commit != observed_commit:
        reasons.append("source_commit_mismatch")

    for path in paths:
        if _matches_any(path, forbidden_paths):
            reasons.append(f"path_forbidden:{path}")
        elif not _matches_any(path, allowed_paths):
            reasons.append(f"path_out_of_scope:{path}")

    if len(paths) > max_files:
        reasons.append("max_files_changed_exceeded")

    diff_lines = diff_added + diff_removed
    if diff_lines > max_diff:
        reasons.append("max_diff_lines_exceeded")

    if len(commands) > max_commands:
        reasons.append("max_commands_exceeded")
    for command in commands:
        if not _matches_any(command, allowed_commands):
            reasons.append(f"command_not_allowed:{command}")

    # Preserve first occurrence while keeping reason ordering deterministic.
    reasons = list(dict.fromkeys(reasons))
    return {
        "allowed": not reasons,
        "state": "allowed" if not reasons else "blocked",
        "reasons": reasons,
        "intent": copy.deepcopy(intent),
        "input": copy.deepcopy(observed),
        "checks": {
            "context_id": intent_context == observed_context,
            "source_commit": intent_commit == observed_commit,
            "paths_in_scope": all(
                _matches_any(path, allowed_paths) and not _matches_any(path, forbidden_paths)
                for path in paths
            ),
            "files_changed": len(paths),
            "max_files_changed": max_files,
            "diff_lines": diff_lines,
            "max_diff_lines": max_diff,
            "commands": len(commands),
            "max_commands": max_commands,
            "acceptance_ids": list(acceptance_ids),
            "checked_at": checked_at,
            "intent_id": intent_id,
        },
    }


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise BudgetError(f"file does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise BudgetError(f"invalid JSON: {path}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate a runtime change observation against a Change Intent")
    parser.add_argument("intent_json", type=Path)
    parser.add_argument("observed_json", type=Path)
    args = parser.parse_args()
    try:
        intent = load_json(args.intent_json)
        observed = load_json(args.observed_json)
        report = evaluate_budget(intent, observed)
    except BudgetError as exc:
        parser.error(str(exc))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["allowed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
