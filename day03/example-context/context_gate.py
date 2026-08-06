from __future__ import annotations

import fnmatch
import json
import sys
from pathlib import Path
from typing import Any


class GateError(ValueError):
    """Raised when a Context Pack or Plan violates the execution contract."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GateError(f"cannot read JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise GateError(f"top-level JSON value must be an object: {path}")
    return value


def _require_string(obj: dict[str, Any], key: str) -> str:
    value = obj.get(key)
    if not isinstance(value, str) or not value.strip():
        raise GateError(f"{key} must be a non-empty string")
    return value


def _require_string_list(obj: dict[str, Any], key: str) -> list[str]:
    value = obj.get(key)
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item.strip() for item in value):
        raise GateError(f"{key} must be a non-empty list of strings")
    return value


def validate_context(context: dict[str, Any]) -> dict[str, Any]:
    context_id = _require_string(context, "context_id")
    version = context.get("version")
    if not isinstance(version, int) or version < 1:
        raise GateError("version must be a positive integer")
    _require_string(context, "source_commit")
    allowed = _require_string_list(context, "allowed_paths")
    read_only = context.get("read_only_paths", [])
    if not isinstance(read_only, list) or not all(isinstance(item, str) and item.strip() for item in read_only):
        raise GateError("read_only_paths must be a list of strings")
    verification = _require_string_list(context, "verification")
    open_questions = context.get("open_questions", [])
    if not isinstance(open_questions, list) or not all(isinstance(item, str) and item.strip() for item in open_questions):
        raise GateError("open_questions must be a list of strings")
    if open_questions:
        raise GateError("open_questions must be empty before execution")
    if len(set(allowed)) != len(allowed):
        raise GateError("allowed_paths contains duplicates")
    if len(set(read_only)) != len(read_only):
        raise GateError("read_only_paths contains duplicates")
    for path in allowed + read_only:
        lowered = path.lower()
        if any(marker in lowered for marker in (".env", "secret", "credential", "token")):
            raise GateError(f"sensitive path cannot be in execution scope: {path}")
    return {
        "context_id": context_id,
        "version": version,
        "allowed_paths": allowed,
        "read_only_paths": read_only,
        "verification": verification,
    }


def _matches(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def _assert_acyclic(tasks: list[dict[str, Any]]) -> None:
    graph = {task["id"]: task.get("depends_on", []) for task in tasks}
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(task_id: str) -> None:
        if task_id in visiting:
            raise GateError(f"dependency cycle detected at task: {task_id}")
        if task_id in visited:
            return
        visiting.add(task_id)
        for dependency in graph[task_id]:
            if dependency not in graph:
                raise GateError(f"unknown dependency: {task_id} -> {dependency}")
            visit(dependency)
        visiting.remove(task_id)
        visited.add(task_id)

    for task_id in graph:
        visit(task_id)


def validate_plan(plan: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    if plan.get("plan_version") != 1:
        raise GateError("plan_version must be 1")
    if plan.get("context_id") != context["context_id"]:
        raise GateError("plan context_id does not match Context Pack")
    if plan.get("context_version") != context["version"]:
        raise GateError("plan context_version does not match Context Pack")
    if plan.get("status") != "approved":
        raise GateError("Plan must be approved before execution")
    tasks = plan.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise GateError("tasks must be a non-empty list")
    ids: set[str] = set()
    for task in tasks:
        if not isinstance(task, dict):
            raise GateError("each task must be an object")
        task_id = _require_string(task, "id")
        if task_id in ids:
            raise GateError(f"duplicate task id: {task_id}")
        ids.add(task_id)
        _require_string(task, "goal")
        paths = _require_string_list(task, "paths")
        acceptance_refs = _require_string_list(task, "acceptance_refs")
        _require_string_list(task, "verification")
        dependencies = task.get("depends_on", [])
        if not isinstance(dependencies, list) or not all(isinstance(item, str) and item.strip() for item in dependencies):
            raise GateError(f"depends_on must be a list of strings: {task_id}")
        for path in paths:
            if not _matches(path, context["allowed_paths"]):
                raise GateError(f"task path is outside allowlist: {task_id}: {path}")
            if _matches(path, context["read_only_paths"]):
                raise GateError(f"task path is read-only: {task_id}: {path}")
        if len(acceptance_refs) != len(set(acceptance_refs)):
            raise GateError(f"duplicate acceptance reference: {task_id}")
    _assert_acyclic(tasks)
    return {"task_count": len(tasks), "task_ids": sorted(ids)}


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("usage: python3 context_gate.py context_pack.json plan.json", file=sys.stderr)
        return 2
    context = validate_context(load_json(Path(argv[1])))
    plan = validate_plan(load_json(Path(argv[2])), context)
    print(f"CONTEXT_OK id={context['context_id']} version={context['version']}")
    print(f"PLAN_OK tasks={plan['task_count']} ids={','.join(plan['task_ids'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
