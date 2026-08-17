import copy
import unittest

from traceability_gate import evaluate_traceability


NOW = "2026-08-14T09:30:00Z"


def intent(**overrides):
    value = {
        "intent_id": "intent-export-20260814-001",
        "context_id": "orders-export",
        "source_commit": "abc1234",
        "acceptance_ids": ["AC-01", "AC-02", "AC-03"],
        "change_ids": ["CH-01"],
        "release_owner": "release-owner",
    }
    value.update(overrides)
    return value


def trace(**overrides):
    value = {
        "trace_id": "trace-20260814-001",
        "intent_id": "intent-export-20260814-001",
        "context_id": "orders-export",
        "source_commit": "abc1234",
        "observation_id": "obs-20260814-001",
        "captured_at": NOW,
        "acceptance_results": [
            {"acceptance_id": "AC-01", "status": "passed", "evidence_ids": ["artifact-01"]},
            {"acceptance_id": "AC-02", "status": "passed", "evidence_ids": ["artifact-02"]},
            {"acceptance_id": "AC-03", "status": "passed", "evidence_ids": ["artifact-03"]},
        ],
        "changes": [
            {"change_id": "CH-01", "artifact_ids": ["artifact-01", "artifact-02", "artifact-03"]}
        ],
        "artifacts": [
            {
                "artifact_id": "artifact-01",
                "kind": "test-log",
                "source_commit": "abc1234",
                "acceptance_ids": ["AC-01"],
                "change_ids": ["CH-01"],
            },
            {
                "artifact_id": "artifact-02",
                "kind": "test-log",
                "source_commit": "abc1234",
                "acceptance_ids": ["AC-02"],
                "change_ids": ["CH-01"],
            },
            {
                "artifact_id": "artifact-03",
                "kind": "review",
                "source_commit": "abc1234",
                "acceptance_ids": ["AC-03"],
                "change_ids": ["CH-01"],
            },
        ],
        "release": {
            "status": "approved",
            "approved_by": "release-owner",
            "approval_id": "approval-20260814-001",
            "source_commit": "abc1234",
        },
    }
    value.update(overrides)
    return value


class TraceabilityGateTests(unittest.TestCase):
    def test_complete_trace_is_allowed(self):
        report = evaluate_traceability(intent(), trace())
        self.assertTrue(report["allowed"])
        self.assertEqual("traceable", report["state"])
        self.assertEqual([], report["reasons"])
        self.assertTrue(report["checks"]["all_acceptances_traceable"])
        self.assertTrue(report["checks"]["all_changes_traceable"])
        self.assertTrue(report["checks"]["release_approved"])

    def test_missing_acceptance_result_is_blocked(self):
        changed = copy.deepcopy(trace())
        changed["acceptance_results"] = changed["acceptance_results"][:-1]
        report = evaluate_traceability(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("acceptance_missing:AC-03", report["reasons"])

    def test_failed_acceptance_is_blocked(self):
        changed = copy.deepcopy(trace())
        changed["acceptance_results"][0]["status"] = "failed"
        report = evaluate_traceability(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("acceptance_not_passed:AC-01", report["reasons"])

    def test_acceptance_artifact_must_link_back(self):
        changed = copy.deepcopy(trace())
        changed["acceptance_results"][0]["evidence_ids"] = ["artifact-02"]
        report = evaluate_traceability(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("artifact_not_linked:AC-01:artifact-02", report["reasons"])

    def test_missing_change_is_blocked(self):
        changed = copy.deepcopy(trace())
        changed["changes"] = []
        report = evaluate_traceability(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("change_missing:CH-01", report["reasons"])

    def test_change_artifact_must_link_back(self):
        changed = copy.deepcopy(trace())
        changed["changes"][0]["artifact_ids"] = ["artifact-01"]
        changed["artifacts"][0]["change_ids"] = []
        report = evaluate_traceability(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("change_artifact_not_linked:CH-01:artifact-01", report["reasons"])

    def test_identity_mismatch_is_blocked(self):
        changed = copy.deepcopy(trace())
        changed["source_commit"] = "def5678"
        report = evaluate_traceability(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("source_commit_mismatch", report["reasons"])

    def test_stale_artifact_commit_is_blocked(self):
        changed = copy.deepcopy(trace())
        changed["artifacts"][1]["source_commit"] = "def5678"
        report = evaluate_traceability(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("artifact_source_commit_mismatch:artifact-02", report["reasons"])

    def test_release_requires_explicit_approval(self):
        changed = copy.deepcopy(trace())
        changed["release"]["status"] = "pending"
        report = evaluate_traceability(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("release_not_approved", report["reasons"])

    def test_unknown_artifact_reference_is_blocked(self):
        changed = copy.deepcopy(trace())
        changed["acceptance_results"][1]["evidence_ids"] = ["artifact-404"]
        report = evaluate_traceability(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("artifact_missing:AC-02:artifact-404", report["reasons"])

    def test_same_input_is_deterministic_and_read_only(self):
        original_intent = intent()
        original_trace = trace()
        first = evaluate_traceability(original_intent, original_trace)
        second = evaluate_traceability(original_intent, original_trace)
        self.assertEqual(first, second)
        self.assertEqual(original_intent, intent())
        self.assertEqual(original_trace, trace())
        self.assertEqual("trace-20260814-001", first["checks"]["trace_id"])


if __name__ == "__main__":
    unittest.main()
