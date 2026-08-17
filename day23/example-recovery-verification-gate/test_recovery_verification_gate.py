#!/usr/bin/env python3
"""Tests for Day 23 Recovery Verification Gate."""
from __future__ import annotations

import copy
import unittest

from recovery_verification_gate import evaluate_recovery


BASE_INTENT = {
    "rollback_id": "rollback-23-001",
    "run_id": "run-23-1",
    "source_candidate_id": "candidate-a",
    "target_candidate_id": "candidate-b",
    "source_commit": "commit-a",
    "input_digest": "digest-a",
    "environment_id": "env-prod",
    "target": "production",
    "min_recovery_window_seconds": 900,
    "min_samples": 100,
    "recovery_thresholds": {
        "availability_min": 0.999,
        "p95_latency_max_ms": 450,
        "error_rate_max": 0.01,
        "queue_depth_max": 20,
    },
    "required_checks": ["rollback_execution", "health", "traffic", "data_integrity"],
    "recovery_evidence": {
        "name": "recovery-observation",
        "digest": "sha256:recovery-current",
    },
}

BASE_OBSERVATION = {
    "rollback_id": "rollback-23-001",
    "run_id": "run-23-1",
    "source_candidate_id": "candidate-a",
    "target_candidate_id": "candidate-b",
    "source_commit": "commit-a",
    "input_digest": "digest-a",
    "environment_id": "env-prod",
    "target": "production",
    "rollback": {
        "status": "completed",
        "applied_target_candidate_id": "candidate-b",
        "execution_evidence": "sha256:rollback-execution",
    },
    "recovery_window": {
        "complete": True,
        "duration_seconds": 900,
        "sample_count": 120,
    },
    "metrics": {
        "availability": 0.9995,
        "p95_latency_ms": 320,
        "error_rate": 0.002,
        "queue_depth": 8,
    },
    "checks": {
        "rollback_execution": "passed",
        "health": "passed",
        "traffic": "passed",
        "data_integrity": "passed",
    },
    "traffic": {
        "state": "serving",
        "serving_candidate_id": "candidate-b",
    },
    "recovery_evidence": {
        "name": "recovery-observation",
        "digest": "sha256:recovery-current",
    },
}


class RecoveryVerificationGateTests(unittest.TestCase):
    def test_recovery_is_verified_when_all_evidence_is_bound(self):
        result = evaluate_recovery(BASE_INTENT, BASE_OBSERVATION)
        self.assertEqual(result, {"allowed": True, "state": "recovery_verified", "reasons": []})

    def test_identity_drift_is_blocked_before_other_checks(self):
        observed = copy.deepcopy(BASE_OBSERVATION)
        observed["run_id"] = "run-23-other"
        result = evaluate_recovery(BASE_INTENT, observed)
        self.assertFalse(result["allowed"])
        self.assertEqual(result["state"], "blocked_identity")
        self.assertEqual(result["reasons"], ["identity_mismatch:run_id"])

    def test_incomplete_rollback_is_blocked(self):
        observed = copy.deepcopy(BASE_OBSERVATION)
        observed["rollback"]["status"] = "failed"
        result = evaluate_recovery(BASE_INTENT, observed)
        self.assertIn("rollback_not_completed", result["reasons"])

    def test_applied_target_mismatch_is_blocked(self):
        observed = copy.deepcopy(BASE_OBSERVATION)
        observed["rollback"]["applied_target_candidate_id"] = "candidate-c"
        result = evaluate_recovery(BASE_INTENT, observed)
        self.assertIn("rollback_target_mismatch", result["reasons"])

    def test_window_and_sample_shortfall_are_blocked(self):
        observed = copy.deepcopy(BASE_OBSERVATION)
        observed["recovery_window"]["complete"] = False
        observed["recovery_window"]["duration_seconds"] = 120
        observed["recovery_window"]["sample_count"] = 4
        result = evaluate_recovery(BASE_INTENT, observed)
        self.assertIn("recovery_window_incomplete", result["reasons"])
        self.assertIn("recovery_window_too_short", result["reasons"])
        self.assertIn("recovery_sample_count_shortfall", result["reasons"])

    def test_metric_threshold_breach_is_blocked(self):
        observed = copy.deepcopy(BASE_OBSERVATION)
        observed["metrics"]["availability"] = 0.98
        observed["metrics"]["p95_latency_ms"] = 900
        observed["metrics"]["error_rate"] = 0.05
        observed["metrics"]["queue_depth"] = 80
        result = evaluate_recovery(BASE_INTENT, observed)
        self.assertIn("recovery_metric_availability_below_target", result["reasons"])
        self.assertIn("recovery_metric_p95_latency_exceeded", result["reasons"])
        self.assertIn("recovery_metric_error_rate_exceeded", result["reasons"])
        self.assertIn("recovery_metric_queue_depth_exceeded", result["reasons"])

    def test_missing_and_failed_checks_are_blocked(self):
        observed = copy.deepcopy(BASE_OBSERVATION)
        del observed["checks"]["data_integrity"]
        observed["checks"]["health"] = "pending"
        result = evaluate_recovery(BASE_INTENT, observed)
        self.assertIn("recovery_check_missing:data_integrity", result["reasons"])
        self.assertIn("recovery_check_not_passed:health", result["reasons"])

    def test_traffic_and_evidence_drift_are_blocked(self):
        observed = copy.deepcopy(BASE_OBSERVATION)
        observed["traffic"]["state"] = "draining"
        observed["traffic"]["serving_candidate_id"] = "candidate-a"
        observed["recovery_evidence"]["digest"] = "sha256:old"
        result = evaluate_recovery(BASE_INTENT, observed)
        self.assertIn("recovery_traffic_not_serving", result["reasons"])
        self.assertIn("recovery_serving_candidate_mismatch", result["reasons"])
        self.assertIn("recovery_evidence_digest_mismatch", result["reasons"])

    def test_retry_is_deterministic_and_does_not_mutate_inputs(self):
        intent = copy.deepcopy(BASE_INTENT)
        observed = copy.deepcopy(BASE_OBSERVATION)
        intent_before = copy.deepcopy(intent)
        observed_before = copy.deepcopy(observed)
        first = evaluate_recovery(intent, observed)
        second = evaluate_recovery(intent, observed)
        self.assertEqual(first, second)
        self.assertEqual(intent, intent_before)
        self.assertEqual(observed, observed_before)


if __name__ == "__main__":
    unittest.main()
