import copy
import json
import unittest
from pathlib import Path

from slo_impact_gate import evaluate_impact


ROOT = Path(__file__).parent


def intent(**overrides):
    value = json.loads((ROOT / "fixtures/intent.json").read_text(encoding="utf-8"))
    value.update(overrides)
    return value


def observation(**overrides):
    value = json.loads((ROOT / "fixtures/observation.json").read_text(encoding="utf-8"))
    value.update(overrides)
    return value


class SloImpactGateTests(unittest.TestCase):
    def test_clear_window_has_no_user_impact_blocker(self):
        report = evaluate_impact(intent(), observation())
        self.assertTrue(report["allowed"])
        self.assertEqual("slo_impact_clear", report["state"])
        self.assertEqual([], report["reasons"])
        self.assertTrue(report["checks"]["error_budget"])

    def test_incomplete_window_is_blocked(self):
        changed = observation()
        changed["observation_window"]["state"] = "collecting"
        report = evaluate_impact(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("observation_window_incomplete", report["reasons"])

    def test_short_window_is_blocked(self):
        changed = observation()
        changed["observation_window"]["duration_seconds"] = 120
        report = evaluate_impact(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("observation_window_too_short", report["reasons"])

    def test_sample_shortfall_is_blocked(self):
        changed = observation()
        changed["observation_window"]["samples"] = 4
        report = evaluate_impact(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("sample_count_shortfall", report["reasons"])

    def test_availability_below_slo_is_blocked(self):
        changed = observation()
        changed["metrics"]["availability"] = 0.97
        report = evaluate_impact(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("metric_availability_below_target", report["reasons"])

    def test_latency_above_slo_is_blocked(self):
        changed = observation()
        changed["metrics"]["p95_latency_ms"] = 480
        report = evaluate_impact(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("metric_p95_latency_exceeded", report["reasons"])

    def test_error_budget_burn_is_blocked(self):
        changed = observation()
        changed["metrics"]["error_budget_burn_rate"] = 1.8
        report = evaluate_impact(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("metric_error_budget_burn_exceeded", report["reasons"])

    def test_skipped_check_is_not_evidence(self):
        changed = observation()
        changed["checks"]["latency"] = "skipped"
        report = evaluate_impact(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("check_not_passed:latency", report["reasons"])

    def test_missing_check_is_blocked(self):
        changed = observation()
        del changed["checks"]["traffic"]
        report = evaluate_impact(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("check_missing:traffic", report["reasons"])

    def test_serving_candidate_drift_is_blocked(self):
        changed = observation()
        changed["traffic"]["serving_candidate_id"] = "candidate-orders-previous"
        report = evaluate_impact(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("serving_candidate_mismatch", report["reasons"])

    def test_non_serving_route_is_blocked(self):
        changed = observation()
        changed["traffic"]["route_state"] = "draining"
        report = evaluate_impact(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("traffic_not_serving", report["reasons"])

    def test_identity_drift_is_blocked(self):
        changed = observation(source_commit="commit-previous")
        report = evaluate_impact(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("source_commit_mismatch", report["reasons"])

    def test_duplicate_required_checks_are_invalid(self):
        with self.assertRaises(ValueError):
            evaluate_impact(intent(required_checks=["window_complete", "window_complete"]), observation())

    def test_retry_is_deterministic_and_read_only(self):
        original_intent = intent()
        original_observation = observation()
        intent_before = copy.deepcopy(original_intent)
        observation_before = copy.deepcopy(original_observation)
        first = evaluate_impact(original_intent, original_observation)
        second = evaluate_impact(original_intent, original_observation)
        self.assertEqual(first, second)
        self.assertEqual(intent_before, original_intent)
        self.assertEqual(observation_before, original_observation)
        self.assertEqual("candidate-orders-current", first["checks"]["candidate_id"])


if __name__ == "__main__":
    unittest.main()
