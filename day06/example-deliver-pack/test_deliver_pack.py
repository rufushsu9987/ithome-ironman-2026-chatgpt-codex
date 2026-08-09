import copy
import unittest

from deliver_pack import DeliverPackError, validate_inputs


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


def task(task_id: str, refs: list[str], paths: list[str], prefix: str) -> dict:
    return {
        "id": task_id,
        "layers": {
            "contract": {"status": "pass", "evidence": [f"{prefix}-context.json"]},
            "process": {
                "status": "pass",
                "commands": [{"argv": ["python3", "-m", "unittest", "-v"], "exit_code": 0, "evidence": f"{prefix}-tests.log"}],
            },
            "behavior": {
                "status": "pass",
                "acceptance": [{"ref": ref, "status": "pass", "evidence": f"{prefix}-{ref}.json"} for ref in refs],
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


VERIFICATION = {
    "context_id": "orders-export",
    "context_version": 3,
    "source_commit": "approved-commit",
    "final_status": "verified",
    "tasks": [
        task("export-api", ["AC-01", "AC-02"], ["src/export/api.py", "tests/export/test_api.py"], "api"),
        task("export-worker", ["AC-03", "AC-04"], ["src/export/worker.py", "tests/export/test_worker.py"], "worker"),
    ],
}

CHANGE = {
    "summary": "將訂單 CSV 匯出拆成 API 建立任務與 Worker 取用資料兩個步驟。",
    "open_items": [{"id": "OPEN-01", "owner": "product-owner", "action": "確認部署窗口與回滾檢查", "status": "open"}],
    "next_step": {"owner": "release-manager", "action": "安排人工 Review 與部署窗口"},
}


class DeliverPackTests(unittest.TestCase):
    def test_complete_inputs_pass(self):
        summary = validate_inputs(PLAN, VERIFICATION, CHANGE)
        self.assertEqual("orders-export", summary["context_id"])
        self.assertEqual(4, summary["acceptance"])
        self.assertEqual(10, summary["evidence"])
        self.assertEqual("release-manager", summary["next_owner"])

    def test_identity_drift_blocks(self):
        verification = copy.deepcopy(VERIFICATION)
        verification["context_version"] = 2
        with self.assertRaisesRegex(DeliverPackError, "context_version"):
            validate_inputs(PLAN, verification, CHANGE)

    def test_unverified_status_blocks(self):
        verification = copy.deepcopy(VERIFICATION)
        verification["final_status"] = "candidate"
        with self.assertRaisesRegex(DeliverPackError, "final_status"):
            validate_inputs(PLAN, verification, CHANGE)

    def test_missing_layer_blocks(self):
        verification = copy.deepcopy(VERIFICATION)
        del verification["tasks"][0]["layers"]["review"]
        with self.assertRaisesRegex(DeliverPackError, "review layer"):
            validate_inputs(PLAN, verification, CHANGE)

    def test_process_failure_blocks(self):
        verification = copy.deepcopy(VERIFICATION)
        verification["tasks"][0]["layers"]["process"]["commands"][0]["exit_code"] = 1
        with self.assertRaisesRegex(DeliverPackError, "未通過"):
            validate_inputs(PLAN, verification, CHANGE)

    def test_acceptance_gap_blocks(self):
        verification = copy.deepcopy(VERIFICATION)
        verification["tasks"][0]["layers"]["behavior"]["acceptance"].pop()
        with self.assertRaisesRegex(DeliverPackError, "acceptance refs"):
            validate_inputs(PLAN, verification, CHANGE)

    def test_unsafe_diff_path_blocks(self):
        verification = copy.deepcopy(VERIFICATION)
        verification["tasks"][0]["layers"]["review"]["diff_paths"] = ["../secrets.txt"]
        with self.assertRaisesRegex(DeliverPackError, "路徑穿越"):
            validate_inputs(PLAN, verification, CHANGE)

    def test_agent_cannot_self_approve(self):
        verification = copy.deepcopy(VERIFICATION)
        verification["tasks"][0]["layers"]["review"]["reviewer"] = "agent"
        with self.assertRaisesRegex(DeliverPackError, "人類 Review"):
            validate_inputs(PLAN, verification, CHANGE)

    def test_missing_next_owner_blocks(self):
        change = copy.deepcopy(CHANGE)
        change["next_step"]["owner"] = ""
        with self.assertRaisesRegex(DeliverPackError, "next_step.owner"):
            validate_inputs(PLAN, VERIFICATION, change)


if __name__ == "__main__":
    unittest.main(verbosity=2)
