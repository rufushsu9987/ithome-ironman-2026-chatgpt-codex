import copy
import json
import unittest
from pathlib import Path

from artifact_promotion_gate import evaluate_promotion


ROOT = Path(__file__).parent


def intent(**overrides):
    value = json.loads((ROOT / "fixtures/intent.json").read_text(encoding="utf-8"))
    value.update(overrides)
    return value


def observation(**overrides):
    value = json.loads((ROOT / "fixtures/observation.json").read_text(encoding="utf-8"))
    value.update(overrides)
    return value


class ArtifactPromotionGateTests(unittest.TestCase):
    def test_complete_bundle_is_promotable(self):
        report = evaluate_promotion(intent(), observation())
        self.assertTrue(report["allowed"])
        self.assertEqual("promotable", report["state"])
        self.assertEqual([], report["reasons"])
        self.assertTrue(report["checks"]["exact_artifact_set"])

    def test_artifact_from_other_run_is_blocked(self):
        changed = observation()
        changed["artifacts"][0]["produced_by_run"] = "run-export-old"
        report = evaluate_promotion(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("artifact_run_mismatch:export-bundle.tgz", report["reasons"])

    def test_pending_artifact_is_blocked(self):
        changed = observation()
        changed["artifacts"][1]["status"] = "pending"
        report = evaluate_promotion(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("artifact_not_ready:verification-report.json", report["reasons"])

    def test_skipped_required_check_is_blocked(self):
        changed = observation()
        changed["artifacts"][0]["checks"]["compatibility"] = "skipped"
        report = evaluate_promotion(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("artifact_check_not_passed:export-bundle.tgz:compatibility", report["reasons"])

    def test_missing_and_unknown_artifacts_are_blocked(self):
        changed = observation()
        changed["artifacts"] = changed["artifacts"][:1]
        changed["artifacts"].append(
            {
                "artifact_id": "debug.log",
                "status": "ready",
                "artifact_digest": "sha256:debug-v1",
                "produced_by_run": "run-export-20260816-001",
                "source_commit": "abc1234",
                "input_digest": "sha256:orders-input-v1",
                "environment_id": "env-python311",
                "checks": {"integrity": "passed"},
            }
        )
        report = evaluate_promotion(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("artifact_missing:verification-report.json", report["reasons"])
        self.assertIn("artifact_unknown:debug.log", report["reasons"])

    def test_digest_mismatch_is_blocked(self):
        changed = observation()
        changed["artifacts"][0]["artifact_digest"] = "sha256:bundle-old"
        report = evaluate_promotion(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("artifact_digest_mismatch:export-bundle.tgz", report["reasons"])

    def test_source_mismatch_is_blocked(self):
        changed = observation()
        changed["artifacts"][1]["source_commit"] = "def5678"
        report = evaluate_promotion(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("artifact_source_mismatch:verification-report.json", report["reasons"])

    def test_promotion_request_mismatch_is_blocked(self):
        changed = observation()
        changed["promotion"] = {"requested": False, "target": "production", "owner": "other@example.invalid"}
        report = evaluate_promotion(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("promotion_not_requested", report["reasons"])
        self.assertIn("promotion_target_mismatch", report["reasons"])
        self.assertIn("promotion_owner_mismatch", report["reasons"])

    def test_identity_mismatch_is_blocked(self):
        changed = observation(source_commit="def5678")
        report = evaluate_promotion(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("source_commit_mismatch", report["reasons"])

    def test_retry_is_deterministic_and_read_only(self):
        original_intent = intent()
        original_observation = observation()
        first = evaluate_promotion(original_intent, original_observation)
        second = evaluate_promotion(original_intent, original_observation)
        self.assertEqual(first, second)
        self.assertEqual(original_intent, intent())
        self.assertEqual(original_observation, observation())
        self.assertEqual("run-export-20260816-001", first["checks"]["run_id"])


if __name__ == "__main__":
    unittest.main()
