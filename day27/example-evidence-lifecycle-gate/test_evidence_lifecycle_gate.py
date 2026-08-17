#!/usr/bin/env python3
"""Tests for the Day 27 Incident Evidence Lifecycle Gate."""
from __future__ import annotations

import copy
import unittest

from evidence_lifecycle_gate import evaluate_lifecycle


BASE_INTENT = {
    "incident_id": "inc-27-001",
    "closeout_id": "closeout-27-001",
    "run_id": "run-27-1",
    "evidence_digest": "sha256:incident-27-current",
    "environment_id": "env-prod",
    "target": "production",
    "required_stages": ["closeout", "retention", "access"],
}

BASE_OBSERVATION = {
    "incident_id": "inc-27-001",
    "closeout_id": "closeout-27-001",
    "run_id": "run-27-1",
    "evidence_digest": "sha256:incident-27-current",
    "environment_id": "env-prod",
    "target": "production",
    "stages": {
        "closeout": {
            "state": "closed",
            "evidence_digest": "sha256:incident-27-current",
            "audit_event_id": "closeout-event-27-001",
        },
        "retention": {
            "state": "retention_ready",
            "evidence_digest": "sha256:incident-27-current",
            "readback_passed": True,
            "audit_event_id": "retention-event-27-001",
        },
        "access": {
            "state": "access_eligible",
            "evidence_digest": "sha256:incident-27-current",
            "approval_bound": True,
            "audit_event_id": "access-event-27-001",
        },
    },
}


class EvidenceLifecycleGateTests(unittest.TestCase):
    def test_pipeline_is_ready_when_all_stages_are_bound_and_ordered(self):
        result = evaluate_lifecycle(BASE_INTENT, BASE_OBSERVATION)
        self.assertEqual(
            result,
            {"allowed": True, "state": "pipeline_ready", "reasons": []},
        )

    def test_identity_drift_blocks_before_stage_evaluation(self):
        observed = copy.deepcopy(BASE_OBSERVATION)
        observed["run_id"] = "run-other"
        result = evaluate_lifecycle(BASE_INTENT, observed)
        self.assertEqual(result["state"], "blocked_identity")
        self.assertEqual(result["reasons"], ["identity_mismatch:run_id"])

    def test_missing_stage_is_fail_closed(self):
        observed = copy.deepcopy(BASE_OBSERVATION)
        del observed["stages"]["access"]
        result = evaluate_lifecycle(BASE_INTENT, observed)
        self.assertIn("stage_missing:access", result["reasons"])
        self.assertEqual(result["state"], "blocked_pipeline")

    def test_stage_order_is_required(self):
        observed = copy.deepcopy(BASE_OBSERVATION)
        observed["stages"] = {
            "closeout": BASE_OBSERVATION["stages"]["closeout"],
            "access": BASE_OBSERVATION["stages"]["access"],
            "retention": BASE_OBSERVATION["stages"]["retention"],
        }
        result = evaluate_lifecycle(BASE_INTENT, observed)
        self.assertIn("stage_order_invalid:retention_before_access", result["reasons"])

    def test_stage_digest_drift_blocks_the_pipeline(self):
        observed = copy.deepcopy(BASE_OBSERVATION)
        observed["stages"]["retention"]["evidence_digest"] = "sha256:old"
        result = evaluate_lifecycle(BASE_INTENT, observed)
        self.assertIn("stage_digest_mismatch:retention", result["reasons"])

    def test_stage_state_must_match_the_lifecycle_contract(self):
        observed = copy.deepcopy(BASE_OBSERVATION)
        observed["stages"]["retention"]["state"] = "blocked_retention"
        result = evaluate_lifecycle(BASE_INTENT, observed)
        self.assertIn("stage_state_invalid:retention", result["reasons"])

    def test_retention_requires_readback_and_access_requires_bound_approval(self):
        observed = copy.deepcopy(BASE_OBSERVATION)
        observed["stages"]["retention"]["readback_passed"] = False
        observed["stages"]["access"]["approval_bound"] = False
        result = evaluate_lifecycle(BASE_INTENT, observed)
        self.assertIn("retention_readback_missing", result["reasons"])
        self.assertIn("access_approval_unbound", result["reasons"])

    def test_every_stage_needs_an_audit_event(self):
        observed = copy.deepcopy(BASE_OBSERVATION)
        observed["stages"]["closeout"].pop("audit_event_id")
        result = evaluate_lifecycle(BASE_INTENT, observed)
        self.assertIn("audit_event_missing:closeout", result["reasons"])

    def test_unknown_stage_is_rejected(self):
        observed = copy.deepcopy(BASE_OBSERVATION)
        observed["stages"]["cleanup"] = {"state": "done"}
        result = evaluate_lifecycle(BASE_INTENT, observed)
        self.assertIn("stage_unknown:cleanup", result["reasons"])

    def test_retry_is_deterministic_and_does_not_mutate_inputs(self):
        intent = copy.deepcopy(BASE_INTENT)
        observed = copy.deepcopy(BASE_OBSERVATION)
        intent_before = copy.deepcopy(intent)
        observed_before = copy.deepcopy(observed)
        first = evaluate_lifecycle(intent, observed)
        second = evaluate_lifecycle(intent, observed)
        self.assertEqual(first, second)
        self.assertEqual(intent, intent_before)
        self.assertEqual(observed, observed_before)


if __name__ == "__main__":
    unittest.main()
