#!/usr/bin/env python3
"""Read-only, deterministic gate for human approval before an irreversible change."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any


class HumanApprovalGateError(ValueError):
    """Raised when an intent or observation is malformed."""


def _string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise HumanApprovalGateError(f"{field} must be a non-empty string")
    return value


def _object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise HumanApprovalGateError(f"{field} must be an object")
    return value


def _number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise HumanApprovalGateError(f"{field} must be a number")
    if value < 0:
        raise HumanApprovalGateError(f"{field} must not be negative")
    return float(value)


def _identity(value: Any, prefix: str) -> dict[str, str]:
    raw = _object(value, prefix)
    return {
        field: _string(raw.get(field), f"{prefix}.{field}")
        for field in (
            "intent_id",
            "run_id",
            "candidate_id",
            "source_commit",
            "input_digest",
            "environment_id",
            "target",
        )
    }


def _unique_reasons(reasons: list[str]) -> list[str]:
    return list(dict.fromkeys(reasons))


def _required_evidence(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list) or not value:
        raise HumanApprovalGateError("intent.required_evidence must be a non-empty list")
    parsed: list[dict[str, str]] = []
    names: set[str] = set()
    for index, item in enumerate(value):
        raw = _object(item, f"intent.required_evidence[{index}]")
        name = _string(raw.get("name"), f"intent.required_evidence[{index}].name")
        state = _string(raw.get("state"), f"intent.required_evidence[{index}].state")
        digest = _string(raw.get("digest"), f"intent.required_evidence[{index}].digest")
        if name in names:
            raise HumanApprovalGateError("intent.required_evidence must not contain duplicates")
        names.add(name)
        parsed.append({"name": name, "state": state, "digest": digest})
    return parsed


def _approval_policy(value: Any) -> dict[str, Any]:
    raw = _object(value, "intent.approval_policy")
    minimum = _number(raw.get("minimum_approvals"), "intent.approval_policy.minimum_approvals")
    if not minimum.is_integer() or minimum < 1:
        raise HumanApprovalGateError("intent.approval_policy.minimum_approvals must be a positive integer")
    max_age = _number(raw.get("max_age_seconds"), "intent.approval_policy.max_age_seconds")
    required_role = _string(raw.get("required_role"), "intent.approval_policy.required_role")
    distinct = raw.get("require_distinct_approvers")
    self_approval = raw.get("forbid_self_approval")
    if not isinstance(distinct, bool) or not isinstance(self_approval, bool):
        raise HumanApprovalGateError("intent.approval_policy boolean flags must be booleans")
    return {
        "minimum_approvals": int(minimum),
        "required_role": required_role,
        "max_age_seconds": max_age,
        "require_distinct_approvers": distinct,
        "forbid_self_approval": self_approval,
    }


def evaluate_approval(intent: dict[str, Any], observed: dict[str, Any]) -> dict[str, Any]:
    """Evaluate approval evidence without mutating either input object."""
    intent_identity = _identity(intent, "intent")
    observed_identity = _identity(observed, "observed")
    reasons: list[str] = []

    for field, expected in intent_identity.items():
        if observed_identity[field] != expected:
            reasons.append(f"{field}_mismatch")

    required_evidence = _required_evidence(intent.get("required_evidence"))
    evidence = _object(observed.get("evidence"), "observed.evidence")
    evidence_reasons: list[str] = []
    for requirement in required_evidence:
        name = requirement["name"]
        item = evidence.get(name)
        if item is None:
            evidence_reasons.append(f"evidence_missing:{name}")
            continue
        observed_evidence = _object(item, f"observed.evidence.{name}")
        if _string(observed_evidence.get("state"), f"observed.evidence.{name}.state") != requirement["state"]:
            evidence_reasons.append(f"evidence_state_mismatch:{name}")
        if _string(observed_evidence.get("digest"), f"observed.evidence.{name}.digest") != requirement["digest"]:
            evidence_reasons.append(f"evidence_digest_mismatch:{name}")
    reasons.extend(evidence_reasons)

    policy = _approval_policy(intent.get("approval_policy"))
    observed_at = _number(observed.get("observed_at_epoch"), "observed.observed_at_epoch")
    proposer_id = _string(intent.get("proposer_id"), "intent.proposer_id")
    approvals_raw = observed.get("approvals")
    if not isinstance(approvals_raw, list):
        raise HumanApprovalGateError("observed.approvals must be a list")

    approvals: list[dict[str, Any]] = []
    approver_ids: list[str] = []
    expected_scope = f"{intent_identity['target']}/{intent_identity['candidate_id']}"
    valid_approved_count = 0
    per_approval_reasons: list[str] = []
    for index, item in enumerate(approvals_raw):
        raw = _object(item, f"observed.approvals[{index}]")
        approver_id = _string(raw.get("approver_id"), f"observed.approvals[{index}].approver_id")
        role = _string(raw.get("role"), f"observed.approvals[{index}].role")
        decision = _string(raw.get("decision"), f"observed.approvals[{index}].decision")
        approved_at = _number(raw.get("approved_at_epoch"), f"observed.approvals[{index}].approved_at_epoch")
        scope = _string(raw.get("scope"), f"observed.approvals[{index}].scope")
        approver_ids.append(approver_id)
        item_reasons: list[str] = []
        if decision != "approved":
            item_reasons.append(f"approval_not_approved:{approver_id}")
        if role != policy["required_role"]:
            item_reasons.append(f"approver_role_mismatch:{approver_id}")
        if approved_at > observed_at or observed_at - approved_at > policy["max_age_seconds"]:
            item_reasons.append(f"approval_expired:{approver_id}")
        if scope != expected_scope:
            item_reasons.append(f"approval_scope_mismatch:{approver_id}")
        if policy["forbid_self_approval"] and approver_id == proposer_id:
            item_reasons.append(f"self_approval:{approver_id}")
        per_approval_reasons.extend(item_reasons)
        if decision == "approved" and not item_reasons:
            valid_approved_count += 1
        approvals.append(
            {
                "approver_id": approver_id,
                "role": role,
                "decision": decision,
                "approved_at_epoch": approved_at,
                "scope": scope,
            }
        )

    reasons.extend(per_approval_reasons)
    if policy["require_distinct_approvers"] and len(set(approver_ids)) != len(approver_ids):
        reasons.append("approver_not_distinct")
    if valid_approved_count < policy["minimum_approvals"]:
        reasons.append("approval_count_shortfall")

    reasons = _unique_reasons(reasons)
    identity_reasons = {
        "intent_id_mismatch",
        "run_id_mismatch",
        "candidate_id_mismatch",
        "source_commit_mismatch",
        "input_digest_mismatch",
        "environment_id_mismatch",
        "target_mismatch",
    }
    return {
        "allowed": not reasons,
        "state": "approval_eligible" if not reasons else "blocked",
        "reasons": reasons,
        "intent": copy.deepcopy(intent),
        "input": copy.deepcopy(observed),
        "checks": {
            "identity": not any(reason in identity_reasons for reason in reasons),
            "evidence": not any(reason.startswith("evidence_") for reason in reasons),
            "approval_policy": not any(reason.startswith(("approval_", "approver_", "self_approval:")) for reason in reasons),
            "approval_count": valid_approved_count >= policy["minimum_approvals"],
            "distinct_approvers": len(set(approver_ids)) == len(approver_ids),
            "candidate_id": intent_identity["candidate_id"],
            "run_id": intent_identity["run_id"],
        },
    }


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise HumanApprovalGateError(f"file does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise HumanApprovalGateError(f"invalid JSON: {path}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description="Check human approvals without executing a change")
    parser.add_argument("intent_json", type=Path)
    parser.add_argument("observation_json", type=Path)
    args = parser.parse_args()
    try:
        report = evaluate_approval(load_json(args.intent_json), load_json(args.observation_json))
    except HumanApprovalGateError as exc:
        parser.error(str(exc))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["allowed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
