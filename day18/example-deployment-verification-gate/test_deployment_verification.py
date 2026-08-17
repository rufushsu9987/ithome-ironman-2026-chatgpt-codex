import copy
import json
import unittest
from pathlib import Path

from deployment_verification_gate import evaluate_deployment


ROOT = Path(__file__).parent


def intent(**overrides):
    value = json.loads((ROOT / "fixtures/intent.json").read_text(encoding="utf-8"))
    value.update(overrides)
    return value


def observation(**overrides):
    value = json.loads((ROOT / "fixtures/observation.json").read_text(encoding="utf-8"))
    value.update(overrides)
    return value


class DeploymentVerificationGateTests(unittest.TestCase):
    def test_complete_deployment_is_verified(self):
        report = evaluate_deployment(intent(), observation())
        self.assertTrue(report["allowed"])
        self.assertEqual("deployment_verified", report["state"])
        self.assertEqual([], report["reasons"])
        self.assertTrue(report["checks"]["serving_identity"])

    def test_deployed_candidate_must_match_intent(self):
        changed = observation()
        changed["deployment"]["candidate_id"] = "rc-orders-20260818.0"
        report = evaluate_deployment(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("deployment_candidate_mismatch", report["reasons"])

    def test_deployed_artifact_digest_must_match(self):
        changed = observation()
        changed["deployment"]["artifact_digest"] = "sha256:artifact-old"
        report = evaluate_deployment(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("deployment_artifact_digest_mismatch", report["reasons"])

    def test_rollout_must_be_complete(self):
        changed = observation()
        changed["deployment"]["rollout_state"] = "in_progress"
        report = evaluate_deployment(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("rollout_not_complete", report["reasons"])

    def test_all_declared_replicas_must_be_ready(self):
        changed = observation()
        changed["deployment"]["replicas_ready"] = 2
        report = evaluate_deployment(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("replica_shortfall", report["reasons"])

    def test_skipped_required_check_is_blocked(self):
        changed = observation()
        changed["checks"]["smoke"] = "skipped"
        report = evaluate_deployment(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("check_not_passed:smoke", report["reasons"])

    def test_missing_required_check_is_blocked(self):
        changed = observation()
        del changed["checks"]["traffic"]
        report = evaluate_deployment(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("check_missing:traffic", report["reasons"])

    def test_traffic_must_serve_the_candidate(self):
        changed = observation()
        changed["traffic"]["serving_candidate_id"] = "rc-orders-20260817.1"
        report = evaluate_deployment(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("serving_candidate_mismatch", report["reasons"])

    def test_identity_drift_is_blocked(self):
        changed = observation(source_commit="def5678")
        report = evaluate_deployment(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("source_commit_mismatch", report["reasons"])

    def test_config_digest_drift_is_blocked(self):
        changed = observation()
        changed["deployment"]["config_digest"] = "sha256:config-old"
        report = evaluate_deployment(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("deployment_config_digest_mismatch", report["reasons"])

    def test_retry_is_deterministic_and_read_only(self):
        original_intent = intent()
        original_observation = observation()
        intent_before = copy.deepcopy(original_intent)
        observation_before = copy.deepcopy(original_observation)
        first = evaluate_deployment(original_intent, original_observation)
        second = evaluate_deployment(original_intent, original_observation)
        self.assertEqual(first, second)
        self.assertEqual(intent_before, original_intent)
        self.assertEqual(observation_before, original_observation)
        self.assertEqual("rc-orders-20260818.1", first["checks"]["candidate_id"])


if __name__ == "__main__":
    unittest.main()
