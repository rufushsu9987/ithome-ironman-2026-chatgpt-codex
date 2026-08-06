from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from context_gate import GateError, load_json, validate_context, validate_plan


ROOT = Path(__file__).parent


class ContextGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.context = load_json(ROOT / "context_pack.json")
        self.plan = load_json(ROOT / "plan.json")

    def test_approved_context_and_plan_pass(self) -> None:
        context = validate_context(self.context)
        result = validate_plan(self.plan, context)
        self.assertEqual(result["task_count"], 2)

    def test_stale_context_version_is_rejected(self) -> None:
        context = validate_context(self.context)
        plan = copy.deepcopy(self.plan)
        plan["context_version"] = 2
        with self.assertRaisesRegex(GateError, "context_version"):
            validate_plan(plan, context)

    def test_path_outside_allowlist_is_rejected(self) -> None:
        context = validate_context(self.context)
        plan = copy.deepcopy(self.plan)
        plan["tasks"][0]["paths"].append("src/payments/refund.py")
        with self.assertRaisesRegex(GateError, "outside allowlist"):
            validate_plan(plan, context)

    def test_duplicate_task_id_is_rejected(self) -> None:
        context = validate_context(self.context)
        plan = copy.deepcopy(self.plan)
        plan["tasks"][1]["id"] = plan["tasks"][0]["id"]
        with self.assertRaisesRegex(GateError, "duplicate task id"):
            validate_plan(plan, context)

    def test_dependency_cycle_is_rejected(self) -> None:
        context = validate_context(self.context)
        plan = copy.deepcopy(self.plan)
        plan["tasks"][0]["depends_on"] = ["export-worker"]
        with self.assertRaisesRegex(GateError, "cycle"):
            validate_plan(plan, context)

    def test_open_question_blocks_execution(self) -> None:
        context = copy.deepcopy(self.context)
        context["open_questions"] = ["是否允許客服角色觸發匯出？"]
        with self.assertRaisesRegex(GateError, "open_questions"):
            validate_context(context)


if __name__ == "__main__":
    unittest.main(verbosity=2)
