import copy
import json
import unittest
from pathlib import Path

from human_approval_gate import evaluate_approval


ROOT = Path(__file__).parent


def intent(**overrides):
    value = json.loads((ROOT / "fixtures/intent.json").read_text(encoding="utf-8"))
    value.update(overrides)
    return value


def observation(**overrides):
    value = json.loads((ROOT / "fixtures/observation.json").read_text(encoding="utf-8"))
    value.update(overrides)
    return value


class HumanApprovalGateTests(unittest.TestCase):
    def test_bound_approvals_are_eligible(self):
        report = evaluate_approval(intent(), observation())
        self.assertTrue(report["allowed"])
        self.assertEqual("approval_eligible", report["state"])
        self.assertEqual([], report["reasons"])
        self.assertTrue(report["checks"]["approval_policy"])

    def test_missing_required_evidence_is_blocked(self):
        changed = observation()
        changed["evidence"].pop("slo_impact")
        report = evaluate_approval(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("evidence_missing:slo_impact", report["reasons"])

    def test_evidence_state_must_match(self):
        changed = observation()
        changed["evidence"]["slo_impact"]["state"] = "blocked"
        report = evaluate_approval(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("evidence_state_mismatch:slo_impact", report["reasons"])

    def test_evidence_digest_must_match_intent(self):
        changed = observation()
        changed["evidence"]["slo_impact"]["digest"] = "sha256:old-slo-evidence"
        report = evaluate_approval(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("evidence_digest_mismatch:slo_impact", report["reasons"])

    def test_expired_approval_is_blocked(self):
        changed = observation()
        changed["approvals"][0]["approved_at_epoch"] = 100
        report = evaluate_approval(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("approval_expired:approver-alice", report["reasons"])

    def test_rejected_approval_is_not_evidence(self):
        changed = observation()
        changed["approvals"][1]["decision"] = "rejected"
        report = evaluate_approval(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("approval_not_approved:approver-bob", report["reasons"])
        self.assertIn("approval_count_shortfall", report["reasons"])

    def test_minimum_approval_count_is_enforced(self):
        changed = observation()
        changed["approvals"] = changed["approvals"][:1]
        report = evaluate_approval(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("approval_count_shortfall", report["reasons"])

    def test_duplicate_approver_ids_are_blocked(self):
        changed = observation()
        changed["approvals"][1]["approver_id"] = changed["approvals"][0]["approver_id"]
        report = evaluate_approval(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("approver_not_distinct", report["reasons"])

    def test_approver_role_is_required(self):
        changed = observation()
        changed["approvals"][0]["role"] = "developer"
        report = evaluate_approval(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("approver_role_mismatch:approver-alice", report["reasons"])

    def test_proposer_cannot_approve_own_change(self):
        changed = observation()
        changed["approvals"][0]["approver_id"] = changed["proposer_id"]
        report = evaluate_approval(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("self_approval:change-author", report["reasons"])

    def test_approval_scope_must_match_candidate_and_target(self):
        changed = observation()
        changed["approvals"][0]["scope"] = "production/other-candidate"
        report = evaluate_approval(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("approval_scope_mismatch:approver-alice", report["reasons"])

    def test_identity_drift_is_blocked(self):
        changed = observation(source_commit="commit-previous")
        report = evaluate_approval(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("source_commit_mismatch", report["reasons"])

    def test_duplicate_required_evidence_is_invalid(self):
        with self.assertRaises(ValueError):
            evaluate_approval(
                intent(
                    required_evidence=[
                        {"name": "slo_impact", "state": "slo_impact_clear"},
                        {"name": "slo_impact", "state": "slo_impact_clear"},
                    ]
                ),
                observation(),
            )

    def test_retry_is_deterministic_and_read_only(self):
        original_intent = intent()
        original_observation = observation()
        intent_before = copy.deepcopy(original_intent)
        observation_before = copy.deepcopy(original_observation)
        first = evaluate_approval(original_intent, original_observation)
        second = evaluate_approval(original_intent, original_observation)
        self.assertEqual(first, second)
        self.assertEqual(intent_before, original_intent)
        self.assertEqual(observation_before, original_observation)
        self.assertEqual("candidate-orders-current", first["checks"]["candidate_id"])


if __name__ == "__main__":
    unittest.main()
