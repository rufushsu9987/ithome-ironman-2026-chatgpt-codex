import copy
import unittest

from execution_guard import GuardError, validate_plan


POLICY = {
    "context_id": "orders-export",
    "context_version": 3,
    "source_commit": "approved-commit",
    "allowed_paths": ["src/export/**", "tests/export/**", "docs/exports.md"],
    "read_only_paths": ["src/auth/**", "config/**"],
    "sensitive_patterns": [".env", "*.pem", "**/*secret*", "**/*token*"],
    "max_runtime_seconds": 900,
    "network": "disabled",
    "approval": "required_on_boundary",
    "stop_conditions": [
        "context_drift",
        "path_violation",
        "verification_failure",
        "timeout",
    ],
}

PLAN = {
    "context_id": "orders-export",
    "context_version": 3,
    "source_commit": "approved-commit",
    "status": "approved",
    "tasks": [
        {
            "id": "export-api",
            "branch": "agent/export-api",
            "worktree": ".worktrees/export-api",
            "paths": ["src/export/api.py", "tests/export/test_api.py"],
            "commands": [["python3", "-m", "unittest", "-v", "tests/export/test_api.py"]],
            "acceptance_refs": ["AC-01", "AC-02"],
            "timeout_seconds": 600,
            "network": "disabled",
            "stop_on_drift": True,
            "requires_human_review": True,
        }
    ],
}


class ExecutionGuardTests(unittest.TestCase):
    def test_approved_plan_passes(self):
        summaries = validate_plan(POLICY, PLAN)
        self.assertEqual(["export-api"], [item["id"] for item in summaries])
        self.assertEqual(".worktrees/export-api", summaries[0]["worktree"])

    def test_context_drift_blocks_plan(self):
        plan = copy.deepcopy(PLAN)
        plan["context_version"] = 2
        with self.assertRaisesRegex(GuardError, "context_version"):
            validate_plan(POLICY, plan)

    def test_path_outside_allowlist_blocks_plan(self):
        plan = copy.deepcopy(PLAN)
        plan["tasks"][0]["paths"].append("src/billing/charge.py")
        with self.assertRaisesRegex(GuardError, "allowed_paths"):
            validate_plan(POLICY, plan)

    def test_read_only_path_blocks_plan(self):
        policy = copy.deepcopy(POLICY)
        policy["allowed_paths"].append("src/auth/**")
        plan = copy.deepcopy(PLAN)
        plan["tasks"][0]["paths"] = ["src/auth/policy.py"]
        with self.assertRaisesRegex(GuardError, "read_only_paths"):
            validate_plan(policy, plan)

    def test_sensitive_path_blocks_plan(self):
        policy = copy.deepcopy(POLICY)
        policy["allowed_paths"].append("config/**")
        policy["read_only_paths"] = []
        plan = copy.deepcopy(PLAN)
        plan["tasks"][0]["paths"] = ["config/client_secret.json"]
        with self.assertRaisesRegex(GuardError, "sensitive_patterns"):
            validate_plan(policy, plan)

    def test_root_worktree_blocks_plan(self):
        plan = copy.deepcopy(PLAN)
        plan["tasks"][0]["worktree"] = "."
        with self.assertRaisesRegex(GuardError, "worktree"):
            validate_plan(POLICY, plan)

    def test_network_command_blocks_plan(self):
        plan = copy.deepcopy(PLAN)
        plan["tasks"][0]["commands"] = [["curl", "https://example.com"]]
        with self.assertRaisesRegex(GuardError, "禁止"):
            validate_plan(POLICY, plan)

    def test_missing_stop_on_drift_blocks_plan(self):
        plan = copy.deepcopy(PLAN)
        plan["tasks"][0]["stop_on_drift"] = False
        with self.assertRaisesRegex(GuardError, "stop_on_drift"):
            validate_plan(POLICY, plan)

    def test_duplicate_path_owner_blocks_plan(self):
        plan = copy.deepcopy(PLAN)
        second = copy.deepcopy(plan["tasks"][0])
        second["id"] = "export-tests"
        second["branch"] = "agent/export-tests"
        second["worktree"] = ".worktrees/export-tests"
        plan["tasks"].append(second)
        with self.assertRaisesRegex(GuardError, "同時被"):
            validate_plan(POLICY, plan)


if __name__ == "__main__":
    unittest.main(verbosity=2)
