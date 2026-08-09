#!/usr/bin/env python3
"""Build a fail-closed handoff pack from verified evidence."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import PurePosixPath
from typing import Any


REQUIRED_LAYERS = ("contract", "process", "behavior", "review")


class DeliverPackError(ValueError):
    """Raised when the handoff inputs cannot support a deliver pack."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise DeliverPackError(message)


def nonempty(value: Any, name: str) -> str:
    require(isinstance(value, str) and value.strip() != "", f"{name} 必須是非空字串")
    return value.strip()


def list_of(value: Any, name: str) -> list[Any]:
    require(isinstance(value, list), f"{name} 必須是陣列")
    return value


def safe_path(value: Any, name: str) -> str:
    raw = nonempty(value, name).replace("\\", "/")
    require(not raw.startswith("/"), f"{name} 不可是絕對路徑：{raw}")
    parts = [part for part in raw.split("/") if part not in ("", ".")]
    require(bool(parts) and ".." not in parts, f"{name} 不可包含路徑穿越：{raw}")
    return PurePosixPath(*parts).as_posix()


def load_json(path: str) -> dict[str, Any]:
    try:
        with open(path, encoding="utf-8") as handle:
            value = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise DeliverPackError(f"無法讀取 JSON：{path}：{exc}") from exc
    require(isinstance(value, dict), f"{path} 必須是 JSON 物件")
    return value


def check_identity(plan: dict[str, Any], verification: dict[str, Any]) -> str:
    context_id = nonempty(plan.get("context_id"), "plan.context_id")
    for key in ("context_version", "source_commit"):
        require(key in plan, f"plan 缺少欄位：{key}")
        require(key in verification, f"verification 缺少欄位：{key}")
    for key in ("context_id", "context_version", "source_commit"):
        require(plan.get(key) == verification.get(key), f"{key} 與 verification 不一致")
    require(verification.get("final_status") == "verified", "verification.final_status 必須是 verified")
    return context_id


def expected_tasks(plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for raw in list_of(plan.get("tasks"), "plan.tasks"):
        require(isinstance(raw, dict), "plan.tasks[] 必須是物件")
        task_id = nonempty(raw.get("id"), "plan task.id")
        require(task_id not in result, f"plan task id 重複：{task_id}")
        refs = [nonempty(ref, f"plan task {task_id}.acceptance_refs[]") for ref in list_of(raw.get("acceptance_refs"), f"plan task {task_id}.acceptance_refs")]
        paths = [safe_path(path, f"plan task {task_id}.paths[]") for path in list_of(raw.get("paths"), f"plan task {task_id}.paths")]
        require(bool(refs) and bool(paths), f"plan task {task_id} 的 paths 與 acceptance_refs 不可為空")
        result[task_id] = {
            "id": task_id,
            "acceptance_refs": refs,
            "paths": paths,
            "requires_human_review": raw.get("requires_human_review") is True,
        }
    require(bool(result), "plan.tasks 不可為空")
    return result


def check_evidence(value: Any, name: str) -> int:
    items = list_of(value, name)
    require(bool(items), f"{name} 不可為空")
    count = 0
    for index, item in enumerate(items):
        if isinstance(item, str):
            nonempty(item, f"{name}[{index}]")
        elif isinstance(item, dict):
            nonempty(item.get("evidence"), f"{name}[{index}].evidence")
        else:
            raise DeliverPackError(f"{name}[{index}] 必須是字串或物件")
        count += 1
    return count


def check_task(raw: Any, expected: dict[str, Any]) -> tuple[dict[str, Any], int, int]:
    require(isinstance(raw, dict), "verification.tasks[] 必須是物件")
    task_id = nonempty(raw.get("id"), "verification task.id")
    require(task_id == expected["id"], f"verification task 順序或 id 不一致：{task_id}")
    layers = raw.get("layers")
    require(isinstance(layers, dict), f"task {task_id}.layers 必須是物件")
    for name in REQUIRED_LAYERS:
        require(name in layers, f"task {task_id} 缺少 {name} layer")
        require(isinstance(layers[name], dict) and layers[name].get("status") == "pass", f"task {task_id}.{name}.status 必須是 pass")

    contract_count = check_evidence(layers["contract"].get("evidence"), f"task {task_id}.contract.evidence")
    process = layers["process"]
    commands = list_of(process.get("commands"), f"task {task_id}.process.commands")
    require(bool(commands), f"task {task_id}.process.commands 不可為空")
    process_count = 0
    for index, command in enumerate(commands):
        require(isinstance(command, dict), f"task {task_id}.process.commands[{index}] 必須是物件")
        argv = command.get("argv")
        require(isinstance(argv, list) and bool(argv) and all(isinstance(part, str) and part for part in argv), f"task {task_id}.process.commands[{index}].argv 不完整")
        require(command.get("exit_code") == 0, f"task {task_id} 驗證命令未通過")
        process_count += check_evidence([command.get("evidence")], f"task {task_id}.process.commands[{index}].evidence")

    behavior = layers["behavior"]
    acceptance = list_of(behavior.get("acceptance"), f"task {task_id}.behavior.acceptance")
    actual_refs: list[str] = []
    behavior_count = 0
    for index, item in enumerate(acceptance):
        require(isinstance(item, dict), f"task {task_id}.behavior.acceptance[{index}] 必須是物件")
        ref = nonempty(item.get("ref"), f"task {task_id}.behavior.acceptance[{index}].ref")
        require(ref not in actual_refs, f"task {task_id} acceptance ref 重複：{ref}")
        actual_refs.append(ref)
        require(item.get("status") == "pass", f"task {task_id} {ref} 未通過")
        behavior_count += check_evidence([item.get("evidence")], f"task {task_id}.{ref}.evidence")
    require(set(actual_refs) == set(expected["acceptance_refs"]), f"task {task_id} 的 acceptance refs 與 Plan 不一致")

    review = layers["review"]
    reviewer = nonempty(review.get("reviewer"), f"task {task_id}.review.reviewer")
    diff_paths = [safe_path(path, f"task {task_id}.review.diff_paths[]") for path in list_of(review.get("diff_paths"), f"task {task_id}.review.diff_paths")]
    require(bool(diff_paths), f"task {task_id}.review.diff_paths 不可為空")
    if expected["requires_human_review"]:
        require(reviewer != "agent", f"task {task_id} 需要人類 Review")
    review_count = check_evidence([review.get("evidence")], f"task {task_id}.review.evidence")
    evidence_count = contract_count + process_count + behavior_count + review_count
    summary = {
        "id": task_id,
        "acceptance": len(actual_refs),
        "evidence": evidence_count,
        "reviewer": reviewer,
        "diff_paths": diff_paths,
    }
    return summary, len(actual_refs), evidence_count


def validate_inputs(plan: dict[str, Any], verification: dict[str, Any], change: dict[str, Any]) -> dict[str, Any]:
    context_id = check_identity(plan, verification)
    expected = expected_tasks(plan)
    raw_tasks = list_of(verification.get("tasks"), "verification.tasks")
    actual_ids = [task.get("id") for task in raw_tasks if isinstance(task, dict)]
    require(set(actual_ids) == set(expected), "verification.tasks 必須與 plan.tasks 完整對應")

    summaries: list[dict[str, Any]] = []
    total_acceptance = 0
    total_evidence = 0
    for index, raw_task in enumerate(raw_tasks):
        require(isinstance(raw_task, dict), f"verification.tasks[{index}] 必須是物件")
        task_id = nonempty(raw_task.get("id"), f"verification.tasks[{index}].id")
        require(task_id in expected, f"verification 出現未知 task：{task_id}")
        summary, acceptance_count, evidence_count = check_task(raw_task, expected[task_id])
        summaries.append(summary)
        total_acceptance += acceptance_count
        total_evidence += evidence_count

    summary_text = nonempty(change.get("summary"), "change.summary")
    next_step = change.get("next_step")
    if not isinstance(next_step, dict):
        raise DeliverPackError("change.next_step 必須是物件")
    next_owner = nonempty(next_step.get("owner"), "change.next_step.owner")
    next_action = nonempty(next_step.get("action"), "change.next_step.action")
    open_items = list_of(change.get("open_items", []), "change.open_items")
    normalized_open: list[dict[str, str]] = []
    for index, item in enumerate(open_items):
        require(isinstance(item, dict), f"change.open_items[{index}] 必須是物件")
        normalized_open.append({
            "id": nonempty(item.get("id"), f"change.open_items[{index}].id"),
            "owner": nonempty(item.get("owner"), f"change.open_items[{index}].owner"),
            "action": nonempty(item.get("action"), f"change.open_items[{index}].action"),
            "status": nonempty(item.get("status"), f"change.open_items[{index}].status"),
        })

    return {
        "context_id": context_id,
        "context_version": plan["context_version"],
        "source_commit": plan["source_commit"],
        "tasks": summaries,
        "acceptance": total_acceptance,
        "evidence": total_evidence,
        "summary": summary_text,
        "next_owner": next_owner,
        "next_action": next_action,
        "open_items": normalized_open,
    }


def render_pack(summary: dict[str, Any], change: dict[str, Any]) -> str:
    lines = [
        f"# Deliver Pack｜{summary['context_id']}",
        "",
        "狀態：READY_FOR_HANDOFF",
        f"Context：`{summary['context_id']}` / v{summary['context_version']}",
        f"Source commit：`{summary['source_commit']}`",
        "",
        "## 1. 變更摘要",
        "",
        summary["summary"],
        "",
        "## 2. 驗證結果",
        "",
        "| Task | Acceptance | Evidence | Reviewer | Diff |",
        "| --- | ---: | ---: | --- | --- |",
    ]
    for task in summary["tasks"]:
        lines.append(f"| `{task['id']}` | {task['acceptance']} | {task['evidence']} | `{task['reviewer']}` | {', '.join(f'`{path}`' for path in task['diff_paths'])} |")
    lines.extend([
        "",
        f"總計：{summary['acceptance']} 條 acceptance、{summary['evidence']} 份 evidence。",
        "",
        "## 3. OPEN items",
        "",
    ])
    if summary["open_items"]:
        for item in summary["open_items"]:
            lines.append(f"- `{item['id']}`（{item['status']}）owner=`{item['owner']}`：{item['action']}")
    else:
        lines.append("- 無已知 OPEN item；仍需依正式發布流程完成授權與回讀。")
    lines.extend([
        "",
        "## 4. 下一步",
        "",
        f"- owner：`{summary['next_owner']}`",
        f"- action：{summary['next_action']}",
        "",
        "## 5. 狀態邊界",
        "",
        "本包只表示 Verified 證據已整理完成、結果可交接；不表示已合併、部署或公開發布。",
        "",
    ])
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Build a fail-closed Deliver Pack")
    parser.add_argument("--plan", required=True)
    parser.add_argument("--verification", required=True)
    parser.add_argument("--change", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv[1:])
    try:
        plan = load_json(args.plan)
        verification = load_json(args.verification)
        change = load_json(args.change)
        summary = validate_inputs(plan, verification, change)
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(render_pack(summary, change))
            handle.write("\n")
    except (DeliverPackError, OSError) as exc:
        print(f"DELIVER_PACK_BLOCKED reason={exc}", file=sys.stderr)
        return 1

    print(
        f"DELIVER_PACK_READY context={summary['context_id']} version={summary['context_version']} "
        f"tasks={len(summary['tasks'])} acceptance={summary['acceptance']} evidence={summary['evidence']} "
        f"open_items={len(summary['open_items'])}"
    )
    print(f"NEXT_OWNER {summary['next_owner']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
