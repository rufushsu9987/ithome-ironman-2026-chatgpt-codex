import copy
import unittest

from verify_matrix import VerifyError, validate_report


POLICY = {
    "context_id": "orders-export",
    "context_version": 3,
    "source_commit": "approved-commit",
    "allowed_paths": ["src/export/**", "tests/export/**", "docs/exports.md"],
    "read_only_paths": ["src/auth/**", "config/**"],
    "required_layers": ["contract", "process", "behavior", "review"],
}

PLAN = {
    "context_id": "orders-export",
    "context_version": 3,
    "source_commit": "approved-commit",
    "tasks": [
        {
            "id": "export-api",
            "paths": ["src/export/api.py", "tests/export/test_api.py"],
            "acceptance_refs": ["AC-01", "AC-02"],
            "requires_human_review": True,
        },
        {
            "id": "export-worker",
            "paths": ["src/export/worker.py", "tests/export/test_worker.py"],
            "acceptance_refs": ["AC-03", "AC-04"],
            "requires_human_review": True,
        },
    ],
}


def layer(evidence: str) -> dict:
    return {"status": "pass", "evidence": [evidence]}


def process_layer(evidence: str) -> dict:
    return {
        "status": "pass",
        "commands": [
            {
                "argv": ["python3", "-m", "unittest", "-v"],
                "exit_code": 0,
                "evidence": evidence,
            }
        ],
    }


def task(task_id: str, refs: list[str], paths: list[str], prefix: str) -> dict:
    return {
        "id": task_id,
        "layers": {
            "contract": layer(f"{prefix}-context.json"),
            "process": process_layer(f"{prefix}-tests.log"),
            "behavior": {
                "status": "pass",
                "acceptance": [
                    {"ref": ref, "status": "pass", "evidence": f"{prefix}-{ref}.json"}
                    for ref in refs
                ],
            },
            "review": {
                "status": "pass",
                "reviewer": "engineering-review",
                "diff_paths": paths,
                "risks": [],
                "evidence": f"{prefix}-review.md",
            },
        },
    }


REPORT = {
    "context_id": "orders-export",
    "context_version": 3,
    "source_commit": "approved-commit",
    "final_status": "verified",
    "tasks": [
        task(
            "export-api",
            ["AC-01", "AC-02"],
            ["src/export/api.py", "tests/export/test_api.py"],
            "api",
        ),
        task(
            "export-worker",
            ["AC-03", "AC-04"],
            ["src/export/worker.py", "tests/export/test_worker.py"],
            "worker",
        ),
    ],
}


class VerifyMatrixTests(unittest.TestCase):
    def test_complete_matrix_passes(self):
        summary = validate_report(POLICY, PLAN, REPORT)
        self.assertEqual(2, len(summary["tasks"]))
        self.assertEqual(4, summary["acceptance"])
        self.assertEqual(["contract", "process", "behavior", "review"], summary["layers"])

    def test_context_drift_blocks_report(self):
        report = copy.deepcopy(REPORT)
        report["context_version"] = 2
        with self.assertRaisesRegex(VerifyError, "context_version"):
            validate_report(POLICY, PLAN, report)

    def test_unverified_final_status_blocks_report(self):
        report = copy.deepcopy(REPORT)
        report["final_status"] = "candidate"
        with self.assertRaisesRegex(VerifyError, "final_status"):
            validate_report(POLICY, PLAN, report)

    def test_missing_layer_blocks_report(self):
        report = copy.deepcopy(REPORT)
        del report["tasks"][0]["layers"]["review"]
        with self.assertRaisesRegex(VerifyError, "review layer"):
            validate_report(POLICY, PLAN, report)

    def test_process_failure_blocks_report(self):
        report = copy.deepcopy(REPORT)
        report["tasks"][0]["layers"]["process"]["commands"][0]["exit_code"] = 1
        with self.assertRaisesRegex(VerifyError, "未通過"):
            validate_report(POLICY, PLAN, report)

    def test_behavior_without_evidence_blocks_report(self):
        report = copy.deepcopy(REPORT)
        report["tasks"][0]["layers"]["behavior"]["acceptance"][0]["evidence"] = ""
        with self.assertRaisesRegex(VerifyError, "evidence"):
            validate_report(POLICY, PLAN, report)

    def test_acceptance_refs_must_match_plan(self):
        report = copy.deepcopy(REPORT)
        report["tasks"][0]["layers"]["behavior"]["acceptance"][1]["ref"] = "AC-99"
        with self.assertRaisesRegex(VerifyError, "acceptance refs"):
            validate_report(POLICY, PLAN, report)

    def test_diff_outside_allowlist_blocks_report(self):
        report = copy.deepcopy(REPORT)
        report["tasks"][0]["layers"]["review"]["diff_paths"].append("src/billing/charge.py")
        with self.assertRaisesRegex(VerifyError, "allowed_paths"):
            validate_report(POLICY, PLAN, report)

    def test_diff_read_only_path_blocks_report(self):
        policy = copy.deepcopy(POLICY)
        policy["allowed_paths"].append("src/auth/**")
        report = copy.deepcopy(REPORT)
        report["tasks"][0]["layers"]["review"]["diff_paths"] = ["src/auth/policy.py"]
        with self.assertRaisesRegex(VerifyError, "read_only_paths"):
            validate_report(policy, PLAN, report)

    def test_agent_cannot_self_approve_required_review(self):
        report = copy.deepcopy(REPORT)
        report["tasks"][0]["layers"]["review"]["reviewer"] = "agent"
        with self.assertRaisesRegex(VerifyError, "人類 Review"):
            validate_report(POLICY, PLAN, report)

    def test_missing_task_blocks_report(self):
        report = copy.deepcopy(REPORT)
        report["tasks"].pop()
        with self.assertRaisesRegex(VerifyError, "完整對應"):
            validate_report(POLICY, PLAN, report)

    def test_unknown_task_blocks_report(self):
        report = copy.deepcopy(REPORT)
        report["tasks"][1]["id"] = "unrelated-task"
        with self.assertRaisesRegex(VerifyError, "完整對應"):
            validate_report(POLICY, PLAN, report)


if __name__ == "__main__":
    unittest.main(verbosity=2)
