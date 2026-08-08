#!/usr/bin/env python3
"""Fail-closed verification evidence matrix for AI-assisted changes.

The example does not run tests or approve a diff. It validates the evidence
manifest produced after execution, so a release decision cannot rely on a
single green command or an agent's unstructured "done" message.
"""
from __future__ import annotations

import fnmatch
import json
import sys
from pathlib import PurePosixPath
from typing import Any


class VerifyError(ValueError):
    """Raised when a verification report is incomplete or out of scope."""


REQUIRED_LAYERS = ("contract", "process", "behavior", "review")


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise VerifyError(message)


def _string(value: Any, name: str) -> str:
    _require(isinstance(value, str) and value.strip() != "", f"{name} 必須是非空字串")
    return value.strip()


def _list(value: Any, name: str) -> list[Any]:
    _require(isinstance(value, list), f"{name} 必須是陣列")
    return value


def normalize_path(value: Any, name: str = "path") -> str:
    raw = _string(value, name).replace("\\", "/")
    _require(not raw.startswith("/"), f"{name} 不可是絕對路徑：{raw}")
    parts = [part for part in raw.split("/") if part not in ("", ".")]
    _require(bool(parts) and ".." not in parts, f"{name} 不可包含路徑穿越：{raw}")
    return PurePosixPath(*parts).as_posix()


def path_matches(path: str, pattern: str) -> bool:
    pattern = pattern.replace("\\", "/").strip()
    if pattern.endswith("/**"):
        base = pattern[:-3].rstrip("/")
        return path == base or path.startswith(base + "/")
    return fnmatch.fnmatchcase(path, pattern)


def is_allowed(path: str, patterns: list[str]) -> bool:
    return any(path_matches(path, pattern) for pattern in patterns)


def load_json(path: str) -> dict[str, Any]:
    try:
        with open(path, encoding="utf-8") as handle:
            value = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise VerifyError(f"無法讀取 JSON：{path}：{exc}") from exc
    _require(isinstance(value, dict), f"{path} 必須是 JSON 物件")
    return value


def _identity_matches(policy: dict[str, Any], plan: dict[str, Any], report: dict[str, Any]) -> None:
    for key in ("context_id", "context_version", "source_commit"):
        _require(key in policy, f"policy 缺少欄位：{key}")
        _require(key in plan, f"plan 缺少欄位：{key}")
        _require(key in report, f"report 缺少欄位：{key}")
        _require(plan[key] == policy[key], f"plan.{key} 與 policy 不一致")
        _require(report[key] == policy[key], f"report.{key} 與 policy 不一致")


def _index_tasks(plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw_tasks = _list(plan.get("tasks"), "plan.tasks")
    _require(bool(raw_tasks), "plan.tasks 不可為空")
    result: dict[str, dict[str, Any]] = {}
    for raw_task in raw_tasks:
        _require(isinstance(raw_task, dict), "plan.tasks[] 必須是物件")
        task_id = _string(raw_task.get("id"), "plan task.id")
        _require(task_id not in result, f"plan task id 重複：{task_id}")
        paths = [_string(item, f"plan task {task_id}.paths[]") for item in _list(raw_task.get("paths"), f"plan task {task_id}.paths")]
        acceptance_refs = [_string(item, f"plan task {task_id}.acceptance_refs[]") for item in _list(raw_task.get("acceptance_refs"), f"plan task {task_id}.acceptance_refs")]
        _require(bool(paths), f"plan task {task_id}.paths 不可為空")
        _require(bool(acceptance_refs), f"plan task {task_id}.acceptance_refs 不可為空")
        result[task_id] = {
            "id": task_id,
            "paths": [normalize_path(path, f"plan task {task_id}.paths[]") for path in paths],
            "acceptance_refs": acceptance_refs,
            "requires_human_review": raw_task.get("requires_human_review") is True,
        }
    return result


def _validate_layer_status(layer: Any, name: str) -> dict[str, Any]:
    _require(isinstance(layer, dict), f"{name} 必須是物件")
    _require(layer.get("status") == "pass", f"{name}.status 必須是 pass")
    return layer


def _validate_evidence_items(items: Any, name: str) -> int:
    values = _list(items, name)
    _require(bool(values), f"{name} 不可為空")
    count = 0
    for index, item in enumerate(values):
        if isinstance(item, str):
            _string(item, f"{name}[{index}]")
            count += 1
            continue
        _require(isinstance(item, dict), f"{name}[{index}] 必須是字串或物件")
        _string(item.get("evidence"), f"{name}[{index}].evidence")
        count += 1
    return count


def _validate_task(
    task: dict[str, Any],
    expected: dict[str, Any],
    policy: dict[str, Any],
) -> tuple[int, int]:
    task_id = _string(task.get("id"), "report task.id")
    _require(task_id == expected["id"], f"report task 順序或 id 不一致：{task_id}")
    layers = task.get("layers")
    if not isinstance(layers, dict):
        raise VerifyError(f"task {task_id}.layers 必須是物件")
    for layer_name in REQUIRED_LAYERS:
        _require(layer_name in layers, f"task {task_id} 缺少 {layer_name} layer")

    contract = _validate_layer_status(layers["contract"], f"task {task_id}.contract")
    evidence_count = _validate_evidence_items(contract.get("evidence"), f"task {task_id}.contract.evidence")

    process = _validate_layer_status(layers["process"], f"task {task_id}.process")
    commands = _list(process.get("commands"), f"task {task_id}.process.commands")
    _require(bool(commands), f"task {task_id}.process.commands 不可為空")
    for index, command in enumerate(commands):
        if not isinstance(command, dict):
            raise VerifyError(f"task {task_id}.process.commands[{index}] 必須是物件")
        argv = command.get("argv")
        if not isinstance(argv, list) or not argv or not all(isinstance(part, str) and part for part in argv):
            raise VerifyError(f"task {task_id}.process.commands[{index}].argv 必須是非空 argv")
        _require(command.get("exit_code") == 0, f"task {task_id} 驗證命令未通過：{' '.join(str(part) for part in argv)}")
        evidence_count += _validate_evidence_items([command.get("evidence")], f"task {task_id}.process.commands[{index}].evidence")

    behavior = _validate_layer_status(layers["behavior"], f"task {task_id}.behavior")
    acceptance = _list(behavior.get("acceptance"), f"task {task_id}.behavior.acceptance")
    expected_refs = expected["acceptance_refs"]
    actual_refs: list[str] = []
    for index, item in enumerate(acceptance):
        _require(isinstance(item, dict), f"task {task_id}.behavior.acceptance[{index}] 必須是物件")
        ref = _string(item.get("ref"), f"task {task_id}.behavior.acceptance[{index}].ref")
        _require(ref not in actual_refs, f"task {task_id} acceptance ref 重複：{ref}")
        actual_refs.append(ref)
        _require(item.get("status") == "pass", f"task {task_id} {ref} 未通過")
        evidence_count += _validate_evidence_items([item.get("evidence")], f"task {task_id}.{ref}.evidence")
    _require(set(actual_refs) == set(expected_refs), f"task {task_id} 的 acceptance refs 與 Plan 不一致")

    review = _validate_layer_status(layers["review"], f"task {task_id}.review")
    reviewer = _string(review.get("reviewer"), f"task {task_id}.review.reviewer")
    diff_paths = _list(review.get("diff_paths"), f"task {task_id}.review.diff_paths")
    _require(bool(diff_paths), f"task {task_id}.review.diff_paths 不可為空")
    allowed = [_string(item, "policy.allowed_paths[]") for item in _list(policy.get("allowed_paths"), "policy.allowed_paths")]
    readonly = [_string(item, "policy.read_only_paths[]") for item in _list(policy.get("read_only_paths"), "policy.read_only_paths")]
    for raw_path in diff_paths:
        path = normalize_path(raw_path, f"task {task_id}.review.diff_paths[]")
        _require(is_allowed(path, allowed), f"task {task_id} diff 越過 allowed_paths：{path}")
        _require(not is_allowed(path, readonly), f"task {task_id} diff 觸碰 read_only_paths：{path}")
    _require(isinstance(review.get("risks"), list), f"task {task_id}.review.risks 必須是陣列")
    _require(reviewer != "agent" or not expected["requires_human_review"],
             f"task {task_id} 需要人類 Review，不能只由 agent 自我核准")
    evidence_count += _validate_evidence_items([review.get("evidence")], f"task {task_id}.review.evidence")
    return len(acceptance), evidence_count


def validate_report(policy: dict[str, Any], plan: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    """Validate a complete contract/process/behavior/review evidence matrix."""
    _identity_matches(policy, plan, report)
    _require(report.get("final_status") == "verified", "report.final_status 必須是 verified")
    expected_tasks = _index_tasks(plan)
    raw_tasks = _list(report.get("tasks"), "report.tasks")
    _require(set(task.get("id") for task in raw_tasks if isinstance(task, dict)) == set(expected_tasks),
             "report.tasks 必須與 plan.tasks 完整對應")

    task_summaries: list[dict[str, Any]] = []
    total_acceptance = 0
    total_evidence = 0
    for index, raw_task in enumerate(raw_tasks):
        _require(isinstance(raw_task, dict), f"report.tasks[{index}] 必須是物件")
        task_id = _string(raw_task.get("id"), f"report.tasks[{index}].id")
        _require(task_id in expected_tasks, f"report 出現未知 task：{task_id}")
        acceptance_count, evidence_count = _validate_task(raw_task, expected_tasks[task_id], policy)
        total_acceptance += acceptance_count
        total_evidence += evidence_count
        task_summaries.append({"id": task_id, "acceptance": acceptance_count, "evidence": evidence_count})

    return {
        "context_id": policy["context_id"],
        "context_version": policy["context_version"],
        "tasks": task_summaries,
        "acceptance": total_acceptance,
        "evidence": total_evidence,
        "layers": list(REQUIRED_LAYERS),
    }


def main(argv: list[str]) -> int:
    if len(argv) != 4:
        print("用法：python3 verify_matrix.py policy.json plan.json verification.json", file=sys.stderr)
        return 2
    try:
        policy = load_json(argv[1])
        plan = load_json(argv[2])
        report = load_json(argv[3])
        summary = validate_report(policy, plan, report)
    except VerifyError as exc:
        print(f"VERIFY_BLOCKED reason={exc}", file=sys.stderr)
        return 1

    print(
        f"VERIFY_OK context={summary['context_id']} version={summary['context_version']} "
        f"tasks={len(summary['tasks'])} acceptance={summary['acceptance']} evidence={summary['evidence']}"
    )
    for task in summary["tasks"]:
        print(f"TASK_VERIFIED id={task['id']} acceptance={task['acceptance']} evidence={task['evidence']}")
    print("LAYERS " + ",".join(summary["layers"]))
    print("NEXT_STATE deliver")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
