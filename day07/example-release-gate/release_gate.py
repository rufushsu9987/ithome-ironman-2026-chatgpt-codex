#!/usr/bin/env python3
"""Validate a fail-closed release gate from verified handoff packs."""
from __future__ import annotations

import argparse
import json
from pathlib import PurePosixPath
from typing import Any


class ReleaseGateError(ValueError):
    """Raised when a release cannot be proven safe to start."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReleaseGateError(message)


def nonempty(value: Any, name: str) -> str:
    require(isinstance(value, str) and value.strip(), f"{name} 必須是非空字串")
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


def validate_release(
    plan: dict[str, Any],
    packs: dict[str, dict[str, Any]],
    approvals: list[dict[str, Any]],
    rollback: dict[str, Any],
) -> dict[str, Any]:
    """Return a release decision only when every gate is explicitly satisfied."""
    require(isinstance(plan, dict), "plan 必須是物件")
    release_id = nonempty(plan.get("release_id"), "plan.release_id")
    version = nonempty(plan.get("version"), "plan.version")
    source_commit = nonempty(plan.get("source_commit"), "plan.source_commit")
    owner = nonempty(plan.get("owner"), "plan.owner")
    dependencies = [nonempty(item, "plan.dependencies[]") for item in list_of(plan.get("dependencies"), "plan.dependencies")]
    require(bool(dependencies), "plan.dependencies 不可為空")
    require(len(set(dependencies)) == len(dependencies), "plan.dependencies 不可重複")
    require(isinstance(packs, dict), "packs 必須是物件")

    normalized_paths: dict[str, list[str]] = {}
    for dependency in dependencies:
        require(dependency in packs, f"缺少 dependency pack：{dependency}")
        pack = packs[dependency]
        require(isinstance(pack, dict), f"dependency pack {dependency} 必須是物件")
        require(pack.get("status") == "READY_FOR_HANDOFF", f"dependency {dependency} 尚未 READY_FOR_HANDOFF")
        require(pack.get("version") == version, f"dependency {dependency} version 與 release 不一致")
        require(pack.get("source_commit") == source_commit, f"dependency {dependency} source_commit 與 release 不一致")
        paths = [safe_path(path, f"dependency {dependency}.artifact_paths[]") for path in list_of(pack.get("artifact_paths"), f"dependency {dependency}.artifact_paths")]
        require(bool(paths), f"dependency {dependency}.artifact_paths 不可為空")
        open_items = list_of(pack.get("open_items", []), f"dependency {dependency}.open_items")
        for index, item in enumerate(open_items):
            require(isinstance(item, dict), f"dependency {dependency}.open_items[{index}] 必須是物件")
            status = nonempty(item.get("status"), f"dependency {dependency}.open_items[{index}].status")
            require(status in {"resolved", "closed", "done"}, f"dependency {dependency} 有未處理 OPEN item")
        normalized_paths[dependency] = paths

    matching_approval = None
    for approval in list_of(approvals, "approvals"):
        if not isinstance(approval, dict):
            continue
        if (
            approval.get("release_id") == release_id
            and approval.get("role") == owner
            and approval.get("decision") == "approved"
        ):
            reviewer = nonempty(approval.get("reviewer"), "approval.reviewer")
            require(reviewer.lower() != "agent", "release approval 必須由 human reviewer 提供")
            matching_approval = approval
            break
    require(matching_approval is not None, "缺少 release owner 的 human approval")

    require(isinstance(rollback, dict), "rollback 必須是物件")
    rollback_owner = nonempty(rollback.get("owner"), "rollback.owner")
    triggers = [nonempty(item, "rollback.triggers[]") for item in list_of(rollback.get("triggers"), "rollback.triggers")]
    steps = [nonempty(item, "rollback.steps[]") for item in list_of(rollback.get("steps"), "rollback.steps")]
    require(triggers and steps, "rollback 必須包含 trigger 與 steps")

    return {
        "decision": "READY_FOR_RELEASE",
        "release_id": release_id,
        "version": version,
        "source_commit": source_commit,
        "owner": owner,
        "dependencies": len(dependencies),
        "artifact_paths": normalized_paths,
        "approval_reviewer": matching_approval["reviewer"],
        "rollback_owner": rollback_owner,
        "rollback_triggers": triggers,
        "rollback_steps": steps,
    }


def load_json(path: str) -> Any:
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ReleaseGateError(f"無法讀取 JSON：{path}：{exc}") from exc


def render_release_gate(result: dict[str, Any]) -> str:
    lines = [
        f"# Release Gate｜{result['release_id']}",
        "",
        "狀態：READY_FOR_RELEASE",
        f"版本：`{result['version']}`",
        f"Source commit：`{result['source_commit']}`",
        f"Dependencies：{result['dependencies']}",
        f"Release owner：`{result['owner']}`",
        f"Human approval：`{result['approval_reviewer']}`",
        f"Rollback owner：`{result['rollback_owner']}`",
        "",
        "## Release decision",
        "",
        "所有交接包都已對齊版本與 source commit，沒有未處理 OPEN item，且已具備人類核准與可執行的回滾條件。",
        "",
        "> 這份 Gate 只證明可以進入發布窗口，不代表已經發布成功。",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--packs", required=True)
    parser.add_argument("--approvals", required=True)
    parser.add_argument("--rollback", required=True)
    parser.add_argument("--out")
    args = parser.parse_args()
    try:
        result = validate_release(
            load_json(args.plan),
            load_json(args.packs),
            load_json(args.approvals),
            load_json(args.rollback),
        )
        if args.out:
            with open(args.out, "w", encoding="utf-8") as handle:
                handle.write(render_release_gate(result))
        print(f"RELEASE_GATE_READY id={result['release_id']} version={result['version']} dependencies={result['dependencies']} rollback_owner={result['rollback_owner']}")
        return 0
    except ReleaseGateError as exc:
        print(f"RELEASE_GATE_BLOCKED {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
