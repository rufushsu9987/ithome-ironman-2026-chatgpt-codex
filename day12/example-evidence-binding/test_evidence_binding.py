import copy
import unittest

from evidence_binding import BindingError, evaluate_binding


NOW = "2026-08-12T09:30:00Z"


def intent(**overrides):
    value = {
        "intent_id": "intent-export-20260812-001",
        "context_id": "orders-export",
        "source_commit": "abc1234",
        "allowed_paths": ["services/export/**"],
        "forbidden_paths": ["services/billing/**", ".github/**"],
        "required_evidence": ["diff", "test-log", "review"],
        "acceptance_ids": ["AC-01", "AC-02"],
    }
    value.update(overrides)
    return value


def evidence(**overrides):
    value = {
        "evidence_id": "ev-export-20260812-001",
        "intent_id": "intent-export-20260812-001",
        "context_id": "orders-export",
        "source_commit": "abc1234",
        "observation_id": "obs-20260812-001",
        "captured_at": NOW,
        "diff": {
            "paths": ["services/export/api.py"],
            "added": 12,
            "removed": 3,
        },
        "tests": {
            "run_id": "test-20260812-001",
            "command": "python3 -m unittest -v",
            "status": "passed",
            "result_digest": "sha256:example-result",
        },
        "review": {
            "review_id": "review-20260812-001",
            "status": "approved",
        },
        "artifacts": [
            {"kind": "diff", "artifact_id": "diff-001", "source_commit": "abc1234"},
            {"kind": "test-log", "artifact_id": "test-log-001", "source_commit": "abc1234"},
            {"kind": "review", "artifact_id": "review-001", "source_commit": "abc1234"},
        ],
    }
    value.update(overrides)
    return value


class EvidenceBindingTests(unittest.TestCase):
    def test_matching_bundle_is_bound(self):
        report = evaluate_binding(intent(), evidence())
        self.assertTrue(report["allowed"])
        self.assertEqual("bound", report["state"])
        self.assertEqual([], report["reasons"])

    def test_identity_mismatch_is_blocked(self):
        report = evaluate_binding(
            intent(), evidence(intent_id="other-intent", source_commit="def5678", context_id="billing")
        )
        self.assertFalse(report["allowed"])
        self.assertIn("intent_id_mismatch", report["reasons"])
        self.assertIn("source_commit_mismatch", report["reasons"])
        self.assertIn("context_id_mismatch", report["reasons"])

    def test_diff_path_outside_scope_is_blocked(self):
        changed = copy.deepcopy(evidence())
        changed["diff"]["paths"].append("services/orders/model.py")
        report = evaluate_binding(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("path_out_of_scope:services/orders/model.py", report["reasons"])

    def test_test_status_and_digest_are_required(self):
        changed = copy.deepcopy(evidence())
        changed["tests"]["status"] = "failed"
        changed["tests"]["result_digest"] = "log-only"
        report = evaluate_binding(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("test_not_passed", report["reasons"])
        self.assertIn("test_result_digest_missing", report["reasons"])

    def test_review_must_be_approved(self):
        changed = copy.deepcopy(evidence())
        changed["review"]["status"] = "pending"
        report = evaluate_binding(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("review_not_approved", report["reasons"])

    def test_required_evidence_kind_is_required(self):
        changed = copy.deepcopy(evidence())
        changed["artifacts"] = [item for item in changed["artifacts"] if item["kind"] != "review"]
        report = evaluate_binding(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("required_evidence_missing:review", report["reasons"])

    def test_artifact_identity_is_unique_and_bound(self):
        changed = copy.deepcopy(evidence())
        changed["artifacts"][1]["artifact_id"] = changed["artifacts"][0]["artifact_id"]
        changed["artifacts"][2]["source_commit"] = "def5678"
        report = evaluate_binding(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("duplicate_artifact_id", report["reasons"])
        self.assertIn("artifact_source_commit_mismatch:review-001", report["reasons"])

    def test_same_input_is_deterministic_and_read_only(self):
        original_intent = intent()
        original_evidence = evidence()
        first = evaluate_binding(original_intent, original_evidence)
        second = evaluate_binding(original_intent, original_evidence)
        self.assertEqual(first, second)
        self.assertEqual(original_intent, intent())
        self.assertEqual(original_evidence, evidence())
        self.assertEqual(NOW, first["input"]["captured_at"])
        self.assertEqual("ev-export-20260812-001", first["checks"]["evidence_id"])


if __name__ == "__main__":
    unittest.main()
