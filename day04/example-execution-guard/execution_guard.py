#!/usr/bin/env python3
"""A small, dependency-free execution boundary gate for agent tasks.

This example does not execute Codex or any other agent. It validates the
contract that must be true before an execution process is allowed to start.
The design is intentionally fail-closed: an omitted field is an error.
"""
from __future__ import annotations

import fnmatch
import json
import re
import sys
from pathlib import PurePosixPath
from typing import Any


class GuardError(ValueError):
    """Raised when an execution policy or plan violates the contract."""


REQUIRED_STOP_CONDITIONS = {
    "context_drift",
    "path_violation",
    "verification_failure",
    "timeout",
}
BRANCH_RE = re.compile(r"^agent/[a-z0-9][a-z0-9-]*$")
FORBIDDEN_SNIPPETS = (
    "curl",
    "wget",
    "ssh",
    "scp",
    "nc ",
    "git push",
    "git reset --hard",
    "npm publish",
    "gh pr merge",
    "rm -rf",
    "rm -r ",
)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise GuardError(message)


def _string(value: Any, name: str) -> str:
    _require(isinstance(value, str) and bool(value.strip()), f"{name} 必須是非空字串")
    return value.strip()


def _list(value: Any, name: str) -> list[Any]:
    _require(isinstance(value, list), f"{name} 必須是陣列")
    return value


def normalize_path(value: Any, name: str = "path") -> str:
    """Return a safe repository-relative POSIX path, rejecting traversal."""
    raw = _string(value, name).replace("\\", "/")
    _require(not raw.startswith("/"), f"{name} 不可是絕對路徑：{raw}")
    parts = [part for part in raw.split("/") if part not in ("", ".")]
    _require(bool(parts) and ".." not in parts, f"{name} 不可包含路徑穿越：{raw}")
    return PurePosixPath(*parts).as_posix()


def path_matches(path: str, pattern: str) -> bool:
    """Match repository paths with a predictable '**' prefix rule."""
    pattern = pattern.replace("\\", "/").strip()
    if pattern.endswith("/**"):
        base = pattern[:-3].rstrip("/")
        return path == base or path.startswith(base + "/")
    return fnmatch.fnmatchcase(path, pattern)


def is_allowed(path: str, patterns: list[str]) -> bool:
    return any(path_matches(path, pattern) for pattern in patterns)


def is_sensitive(path: str, patterns: list[str]) -> bool:
    lowered = path.lower()
    for pattern in patterns:
        clean = pattern.replace("\\", "/").lower()
        if fnmatch.fnmatchcase(path.lower(), clean) or clean.strip("*") in lowered:
            return True
    return False


def validate_policy(policy: dict[str, Any]) -> None:
    """Validate the repository-level execution policy."""
    for key in (
        "context_id",
        "context_version",
        "source_commit",
        "allowed_paths",
        "read_only_paths",
        "sensitive_patterns",
        "max_runtime_seconds",
        "network",
        "approval",
        "stop_conditions",
    ):
        _require(key in policy, f"policy 缺少欄位：{key}")

    _string(policy["context_id"], "policy.context_id")
    _require(isinstance(policy["context_version"], int) and policy["context_version"] > 0,
             "policy.context_version 必須是正整數")
    _string(policy["source_commit"], "policy.source_commit")
    allowed = [_string(item, "policy.allowed_paths[]") for item in _list(policy["allowed_paths"], "policy.allowed_paths")]
    _require(bool(allowed), "policy.allowed_paths 不可為空")
    readonly = [_string(item, "policy.read_only_paths[]") for item in _list(policy["read_only_paths"], "policy.read_only_paths")]
    sensitive = [_string(item, "policy.sensitive_patterns[]") for item in _list(policy["sensitive_patterns"], "policy.sensitive_patterns")]
    _require(isinstance(policy["max_runtime_seconds"], int), "policy.max_runtime_seconds 必須是整數")
    _require(0 < policy["max_runtime_seconds"] <= 900,
             "policy.max_runtime_seconds 必須介於 1 到 900 秒")
    _require(policy["network"] == "disabled", "範例只允許 network=disabled")
    _require(policy["approval"] == "required_on_boundary",
             "approval 必須是 required_on_boundary")
    stops = set(_list(policy["stop_conditions"], "policy.stop_conditions"))
    _require(bool(REQUIRED_STOP_CONDITIONS <= stops),
             "stop_conditions 必須包含 context_drift、path_violation、verification_failure、timeout")

    # Check that policy patterns themselves do not contain traversal.
    for pattern in allowed + readonly + sensitive:
        _require(".." not in pattern.replace("\\", "/").split("/"),
                 f"policy pattern 不可包含 ..：{pattern}")


def _validate_command(command: Any, task_id: str) -> None:
    _require(isinstance(command, list) and command,
             f"task {task_id} 的 command 必須是非空 argv 陣列")
    _require(all(isinstance(part, str) and part for part in command),
             f"task {task_id} 的 command 只能包含非空字串")
    joined = " ".join(command).lower()
    _require("-c" not in command or command[0] not in {"sh", "bash", "zsh"},
             f"task {task_id} 不可用 shell -c 繞過命令檢查")
    for snippet in FORBIDDEN_SNIPPETS:
        _require(snippet not in joined, f"task {task_id} 含有禁止的命令片段：{snippet.strip()}")


def validate_plan(policy: dict[str, Any], plan: dict[str, Any]) -> list[dict[str, Any]]:
    """Validate a plan against a policy and return normalized task summaries."""
    validate_policy(policy)
    for key in ("context_id", "context_version", "source_commit", "status", "tasks"):
        _require(key in plan, f"plan 缺少欄位：{key}")
    _require(plan["context_id"] == policy["context_id"], "plan.context_id 與 policy 不一致")
    _require(plan["context_version"] == policy["context_version"], "plan.context_version 與 policy 不一致")
    _require(plan["source_commit"] == policy["source_commit"], "plan.source_commit 與 policy 不一致")
    _require(plan["status"] == "approved", "只有 status=approved 的 plan 可以執行")

    tasks = _list(plan["tasks"], "plan.tasks")
    _require(tasks, "plan.tasks 不可為空")
    seen_ids: set[str] = set()
    claimed_paths: dict[str, str] = {}
    summaries: list[dict[str, Any]] = []
    allowed = [_string(item, "policy.allowed_paths[]") for item in policy["allowed_paths"]]
    readonly = [_string(item, "policy.read_only_paths[]") for item in policy["read_only_paths"]]
    sensitive = [_string(item, "policy.sensitive_patterns[]") for item in policy["sensitive_patterns"]]

    for raw_task in tasks:
        _require(isinstance(raw_task, dict), "每個 task 必須是物件")
        task_id = _string(raw_task.get("id"), "task.id")
        _require(task_id not in seen_ids, f"task id 重複：{task_id}")
        seen_ids.add(task_id)
        branch = _string(raw_task.get("branch"), f"task {task_id}.branch")
        _require(bool(BRANCH_RE.fullmatch(branch)),
                 f"task {task_id}.branch 必須符合 agent/<小寫名稱>")
        worktree = normalize_path(raw_task.get("worktree"), f"task {task_id}.worktree")
        _require(worktree.startswith(".worktrees/"),
                 f"task {task_id} 必須在 .worktrees/ 下執行")
        _require(worktree == f".worktrees/{task_id}",
                 f"task {task_id} 的 worktree 必須是 .worktrees/{task_id}")

        paths = _list(raw_task.get("paths"), f"task {task_id}.paths")
        _require(paths, f"task {task_id}.paths 不可為空")
        normalized_paths: list[str] = []
        for raw_path in paths:
            path = normalize_path(raw_path, f"task {task_id}.paths[]")
            _require(is_allowed(path, allowed),
                     f"task {task_id} 越過 allowed_paths：{path}")
            _require(not is_allowed(path, readonly),
                     f"task {task_id} 觸碰 read_only_paths：{path}")
            _require(not is_sensitive(path, sensitive),
                     f"task {task_id} 觸碰 sensitive_patterns：{path}")
            _require(path not in normalized_paths, f"task {task_id} 重複宣告路徑：{path}")
            _require(path not in claimed_paths,
                     f"路徑 {path} 同時被 {claimed_paths.get(path)} 與 {task_id} 擁有")
            normalized_paths.append(path)
            claimed_paths[path] = task_id

        commands = _list(raw_task.get("commands"), f"task {task_id}.commands")
        _require(commands, f"task {task_id}.commands 不可為空")
        for command in commands:
            _validate_command(command, task_id)

        timeout = raw_task.get("timeout_seconds")
        _require(isinstance(timeout, int) and 0 < timeout <= policy["max_runtime_seconds"],
                 f"task {task_id}.timeout_seconds 必須不超過 policy 上限")
        _require(raw_task.get("network") == "disabled",
                 f"task {task_id} 必須明確關閉網路")
        _require(raw_task.get("stop_on_drift") is True,
                 f"task {task_id} 必須設定 stop_on_drift=true")
        _require(raw_task.get("requires_human_review") is True,
                 f"task {task_id} 必須保留人工 Review")
        acceptance = _list(raw_task.get("acceptance_refs"), f"task {task_id}.acceptance_refs")
        _require(bool(acceptance) and all(isinstance(item, str) and item for item in acceptance),
                 f"task {task_id}.acceptance_refs 不可為空")

        summaries.append({
            "id": task_id,
            "branch": branch,
            "worktree": worktree,
            "paths": normalized_paths,
            "timeout_seconds": timeout,
            "commands": commands,
        })
    return summaries


def load_json(path: str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as handle:
        value = json.load(handle)
    _require(isinstance(value, dict), f"{path} 必須是 JSON 物件")
    return value


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("用法：python3 execution_guard.py policy.json plan.json", file=sys.stderr)
        return 2
    try:
        policy = load_json(argv[1])
        plan = load_json(argv[2])
        summaries = validate_plan(policy, plan)
    except (OSError, json.JSONDecodeError, GuardError) as exc:
        print(f"EXECUTION_BLOCKED reason={exc}", file=sys.stderr)
        return 1

    print(f"EXECUTION_OK context={policy['context_id']} version={policy['context_version']} tasks={len(summaries)}")
    for task in summaries:
        print(
            f"TASK_OK id={task['id']} worktree={task['worktree']} "
            f"paths={len(task['paths'])} timeout={task['timeout_seconds']}s network=disabled"
        )
        for command in task["commands"]:
            print("VERIFY_COMMAND " + " ".join(command))
    print("STOP_CONDITIONS " + ",".join(sorted(REQUIRED_STOP_CONDITIONS)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
