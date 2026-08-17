import copy
import json
import unittest
from pathlib import Path

from post_deployment_stability_gate import evaluate_stability


ROOT = Path(__file__).parent


def intent(**overrides):
    value = json.loads((ROOT / "fixtures/intent.json").read_text(encoding="utf-8"))
    value.update(overrides)
    return value


def observation(**overrides):
    value = json.loads((ROOT / "fixtures/observation.json").read_text(encoding="utf-8"))
    value.update(overrides)
    return value


class PostDeploymentStabilityGateTests(unittest.TestCase):
    def test_complete_window_is_stable(self):
        report = evaluate_stability(intent(), observation())
        self.assertTrue(report["allowed"])
        self.assertEqual("post_deployment_stable", report["state"])
        self.assertEqual([], report["reasons"])
        self.assertTrue(report["checks"]["metrics"])

    def test_incomplete_window_is_blocked(self):
        changed = observation()
        changed["observation_window"]["state"] = "collecting"
        report = evaluate_stability(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("observation_window_incomplete", report["reasons"])

    def test_window_too_short_is_blocked(self):
        changed = observation()
        changed["observation_window"]["duration_seconds"] = 120
        report = evaluate_stability(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("observation_window_too_short", report["reasons"])

    def test_sample_shortfall_is_blocked(self):
        changed = observation()
        changed["observation_window"]["samples"] = 2
        report = evaluate_stability(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("sample_count_shortfall", report["reasons"])

    def test_error_rate_threshold_is_blocked(self):
        changed = observation()
        changed["metrics"]["error_rate"] = 0.08
        report = evaluate_stability(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("metric_error_rate_exceeded", report["reasons"])

    def test_latency_threshold_is_blocked(self):
        changed = observation()
        changed["metrics"]["p95_latency_ms"] = 480
        report = evaluate_stability(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("metric_p95_latency_exceeded", report["reasons"])

    def test_saturation_threshold_is_blocked(self):
        changed = observation()
        changed["metrics"]["saturation_percent"] = 91
        report = evaluate_stability(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("metric_saturation_exceeded", report["reasons"])

    def test_skipped_check_is_blocked(self):
        changed = observation()
        changed["checks"]["latency"] = "skipped"
        report = evaluate_stability(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("check_not_passed:latency", report["reasons"])

    def test_missing_check_is_blocked(self):
        changed = observation()
        del changed["checks"]["traffic"]
        report = evaluate_stability(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("check_missing:traffic", report["reasons"])

    def test_serving_candidate_mismatch_is_blocked(self):
        changed = observation()
        changed["traffic"]["serving_candidate_id"] = "rc-orders-20260818.1"
        report = evaluate_stability(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("serving_candidate_mismatch", report["reasons"])

    def test_identity_drift_is_blocked(self):
        changed = observation(source_commit="def5678")
        report = evaluate_stability(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("source_commit_mismatch", report["reasons"])

    def test_non_serving_route_is_blocked(self):
        changed = observation()
        changed["traffic"]["route_state"] = "draining"
        report = evaluate_stability(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("traffic_not_serving", report["reasons"])

    def test_retry_is_deterministic_and_read_only(self):
        original_intent = intent()
        original_observation = observation()
        intent_before = copy.deepcopy(original_intent)
        observation_before = copy.deepcopy(original_observation)
        first = evaluate_stability(original_intent, original_observation)
        second = evaluate_stability(original_intent, original_observation)
        self.assertEqual(first, second)
        self.assertEqual(intent_before, original_intent)
        self.assertEqual(observation_before, original_observation)
        self.assertEqual("rc-orders-20260819.1", first["checks"]["candidate_id"])


if __name__ == "__main__":
    unittest.main()
