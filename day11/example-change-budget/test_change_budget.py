import copy
import unittest

from change_budget import BudgetError, evaluate_budget


NOW = "2026-08-12T09:00:00Z"


def intent(**overrides):
    value = {
        "intent_id": "change-export-20260812-001",
        "context_id": "orders-export",
        "source_commit": "abc1234",
        "allowed_paths": ["services/export/**"],
        "forbidden_paths": ["services/billing/**", ".github/**"],
        "allowed_commands": ["python3 -m unittest -v", "python3 -m py_compile *"],
        "max_files_changed": 3,
        "max_diff_lines": 40,
        "max_commands": 4,
        "acceptance_ids": ["AC-01", "AC-02"],
    }
    value.update(overrides)
    return value


def observed(**overrides):
    value = {
        "context_id": "orders-export",
        "source_commit": "abc1234",
        "paths_changed": [
            "services/export/api.py",
            "services/export/test_api.py",
        ],
        "diff_added": 18,
        "diff_removed": 7,
        "commands": ["python3 -m unittest -v"],
        "checked_at": NOW,
    }
    value.update(overrides)
    return value


class ChangeBudgetTests(unittest.TestCase):
    def test_matching_change_is_allowed(self):
        report = evaluate_budget(intent(), observed())
        self.assertTrue(report["allowed"])
        self.assertEqual("allowed", report["state"])
        self.assertEqual([], report["reasons"])

    def test_path_outside_allowlist_is_blocked(self):
        report = evaluate_budget(
            intent(), observed(paths_changed=["services/export/api.py", "services/orders/model.py"])
        )
        self.assertFalse(report["allowed"])
        self.assertIn("path_out_of_scope:services/orders/model.py", report["reasons"])

    def test_forbidden_path_is_blocked_even_if_otherwise_in_scope(self):
        report = evaluate_budget(
            intent(), observed(paths_changed=["services/export/api.py", ".github/workflows/ci.yml"])
        )
        self.assertFalse(report["allowed"])
        self.assertIn("path_forbidden:.github/workflows/ci.yml", report["reasons"])

    def test_file_count_budget_is_blocked(self):
        report = evaluate_budget(
            intent(max_files_changed=2),
            observed(paths_changed=[
                "services/export/api.py",
                "services/export/test_api.py",
                "services/export/worker.py",
            ]),
        )
        self.assertFalse(report["allowed"])
        self.assertIn("max_files_changed_exceeded", report["reasons"])

    def test_diff_line_budget_is_blocked(self):
        report = evaluate_budget(intent(max_diff_lines=20), observed(diff_added=15, diff_removed=6))
        self.assertFalse(report["allowed"])
        self.assertIn("max_diff_lines_exceeded", report["reasons"])

    def test_command_allowlist_and_count_are_enforced(self):
        report = evaluate_budget(
            intent(max_commands=1),
            observed(commands=["python3 -m unittest -v", "rm -rf services/export"]),
        )
        self.assertFalse(report["allowed"])
        self.assertIn("max_commands_exceeded", report["reasons"])
        self.assertIn("command_not_allowed:rm -rf services/export", report["reasons"])

    def test_context_and_commit_mismatch_are_blocked(self):
        report = evaluate_budget(
            intent(), observed(context_id="billing", source_commit="def5678")
        )
        self.assertFalse(report["allowed"])
        self.assertIn("context_id_mismatch", report["reasons"])
        self.assertIn("source_commit_mismatch", report["reasons"])

    def test_same_input_is_deterministic_and_read_only(self):
        original_intent = intent()
        original_observed = observed()
        first = evaluate_budget(original_intent, original_observed)
        second = evaluate_budget(original_intent, original_observed)
        self.assertEqual(first, second)
        self.assertEqual(original_intent, intent())
        self.assertEqual(original_observed, observed())
        self.assertEqual(NOW, first["input"]["checked_at"])
        self.assertEqual("change-export-20260812-001", first["intent"]["intent_id"])


if __name__ == "__main__":
    unittest.main()
