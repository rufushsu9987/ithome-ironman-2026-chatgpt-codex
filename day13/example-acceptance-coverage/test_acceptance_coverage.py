import copy
import unittest

from acceptance_coverage import evaluate_coverage


NOW = "2026-08-13T09:30:00Z"


def intent(**overrides):
    value = {
        "intent_id": "intent-export-20260813-001",
        "context_id": "orders-export",
        "source_commit": "abc1234",
        "acceptance_ids": ["AC-01", "AC-02", "AC-03"],
    }
    value.update(overrides)
    return value


def evidence(**overrides):
    value = {
        "evidence_id": "coverage-20260813-001",
        "intent_id": "intent-export-20260813-001",
        "context_id": "orders-export",
        "source_commit": "abc1234",
        "observation_id": "obs-20260813-001",
        "captured_at": NOW,
        "acceptance_results": [
            {"acceptance_id": "AC-01", "status": "passed", "evidence_ids": ["test-001"]},
            {"acceptance_id": "AC-02", "status": "passed", "evidence_ids": ["test-002"]},
            {"acceptance_id": "AC-03", "status": "passed", "evidence_ids": ["review-001"]},
        ],
        "artifacts": [
            {"artifact_id": "test-001", "kind": "test-log", "acceptance_ids": ["AC-01"], "source_commit": "abc1234"},
            {"artifact_id": "test-002", "kind": "test-log", "acceptance_ids": ["AC-02"], "source_commit": "abc1234"},
            {"artifact_id": "review-001", "kind": "review", "acceptance_ids": ["AC-03"], "source_commit": "abc1234"},
        ],
    }
    value.update(overrides)
    return value


class AcceptanceCoverageTests(unittest.TestCase):
    def test_every_acceptance_has_passing_evidence(self):
        report = evaluate_coverage(intent(), evidence())
        self.assertTrue(report["allowed"])
        self.assertEqual("covered", report["state"])
        self.assertEqual([], report["reasons"])

    def test_missing_acceptance_is_blocked(self):
        changed = copy.deepcopy(evidence())
        changed["acceptance_results"] = changed["acceptance_results"][:-1]
        report = evaluate_coverage(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("acceptance_missing:AC-03", report["reasons"])

    def test_failed_acceptance_is_blocked(self):
        changed = copy.deepcopy(evidence())
        changed["acceptance_results"][1]["status"] = "failed"
        report = evaluate_coverage(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("acceptance_not_passed:AC-02", report["reasons"])

    def test_missing_evidence_is_blocked(self):
        changed = copy.deepcopy(evidence())
        changed["acceptance_results"][0]["evidence_ids"] = []
        report = evaluate_coverage(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("evidence_missing:AC-01", report["reasons"])

    def test_evidence_must_link_back_to_acceptance(self):
        changed = copy.deepcopy(evidence())
        changed["acceptance_results"][0]["evidence_ids"] = ["test-002"]
        report = evaluate_coverage(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("evidence_not_linked:AC-01:test-002", report["reasons"])

    def test_unknown_acceptance_is_blocked(self):
        changed = copy.deepcopy(evidence())
        changed["acceptance_results"].append(
            {"acceptance_id": "AC-99", "status": "passed", "evidence_ids": ["test-001"]}
        )
        report = evaluate_coverage(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("acceptance_unknown:AC-99", report["reasons"])

    def test_identity_mismatch_is_blocked(self):
        changed = copy.deepcopy(evidence())
        changed["source_commit"] = "def5678"
        report = evaluate_coverage(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("source_commit_mismatch", report["reasons"])

    def test_duplicate_evidence_id_is_blocked(self):
        changed = copy.deepcopy(evidence())
        changed["artifacts"][1]["artifact_id"] = "test-001"
        report = evaluate_coverage(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("duplicate_evidence_id", report["reasons"])

    def test_same_input_is_deterministic_and_read_only(self):
        original_intent = intent()
        original_evidence = evidence()
        first = evaluate_coverage(original_intent, original_evidence)
        second = evaluate_coverage(original_intent, original_evidence)
        self.assertEqual(first, second)
        self.assertEqual(original_intent, intent())
        self.assertEqual(original_evidence, evidence())
        self.assertEqual("coverage-20260813-001", first["checks"]["evidence_id"])


if __name__ == "__main__":
    unittest.main()
