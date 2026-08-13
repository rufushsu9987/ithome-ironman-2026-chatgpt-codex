import copy
import unittest

from freshness_gate import evaluate_freshness


NOW = "2026-08-12T06:00:00Z"


def learning(**overrides):
    value = {
        "learning_id": "learn-export-async-001",
        "status": "approved",
        "scope": ["services/export/**"],
        "evidence_refs": ["incident/e6-rollback-completed.json"],
        "expires_at": "2026-08-20T00:00:00Z",
    }
    value.update(overrides)
    return value


def context(**overrides):
    value = {
        "context_id": "orders-export",
        "source_commit": "abc1234",
        "created_at": "2026-08-12T00:00:00Z",
        "max_age_hours": 24,
        "learning_refs": [learning()],
    }
    value.update(overrides)
    return value


def request(**overrides):
    value = {
        "context_id": "orders-export",
        "source_commit": "abc1234",
        "paths": ["services/export/api.py"],
        "checked_at": NOW,
    }
    value.update(overrides)
    return value


class FreshnessGateTests(unittest.TestCase):
    def test_fresh_context_is_allowed(self):
        report = evaluate_freshness(context(), request())
        self.assertTrue(report["allowed"])
        self.assertEqual([], report["reasons"])
        self.assertEqual("fresh", report["state"])

    def test_source_commit_drift_is_blocked(self):
        report = evaluate_freshness(context(), request(source_commit="def5678"))
        self.assertFalse(report["allowed"])
        self.assertIn("source_commit_mismatch", report["reasons"])

    def test_context_age_is_blocked(self):
        old_context = context(created_at="2026-08-10T00:00:00Z")
        report = evaluate_freshness(old_context, request())
        self.assertFalse(report["allowed"])
        self.assertIn("context_expired", report["reasons"])

    def test_retired_expired_and_missing_evidence_learning_is_blocked(self):
        report = evaluate_freshness(
            context(learning_refs=[
                learning(status="retired"),
                learning(learning_id="learn-expired", expires_at="2026-08-11T00:00:00Z"),
                learning(learning_id="learn-no-evidence", evidence_refs=[]),
            ]),
            request(),
        )
        self.assertFalse(report["allowed"])
        self.assertIn("learning:learn-export-async-001:status_retired", report["reasons"])
        self.assertIn("learning:learn-expired:expired", report["reasons"])
        self.assertIn("learning:learn-no-evidence:missing_evidence", report["reasons"])

    def test_cross_context_and_out_of_scope_paths_are_blocked(self):
        report = evaluate_freshness(
            context(),
            request(context_id="billing", paths=["services/billing/api.py"]),
        )
        self.assertFalse(report["allowed"])
        self.assertIn("context_id_mismatch", report["reasons"])
        self.assertIn("path_out_of_scope:services/billing/api.py", report["reasons"])

    def test_same_input_is_deterministic_and_read_only(self):
        original_context = context()
        original_request = request()
        first = evaluate_freshness(original_context, original_request)
        second = evaluate_freshness(original_context, original_request)
        self.assertEqual(first, second)
        self.assertEqual(original_context, context())
        self.assertEqual(original_request, request())
        self.assertEqual(first["input"]["checked_at"], NOW)


if __name__ == "__main__":
    unittest.main()
