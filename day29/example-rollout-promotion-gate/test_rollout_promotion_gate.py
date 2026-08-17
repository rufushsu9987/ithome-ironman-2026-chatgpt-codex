from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path
from unittest import TestCase

from rollout_promotion_gate import check_promotion


class RolloutPromotionGateTests(TestCase):
    def valid_intent(self) -> dict:
        return {
            "identity": {
                "release_id": "release-29",
                "environment": "staging",
                "current_cohort": "canary-10",
                "target_cohort": "canary-25",
                "run_id": "run-29",
                "promotion_id": "promotion-29-001",
                "evidence_digest": "sha256:promotion-29-current",
                "policy_version": "rollout-policy-v3",
            },
            "minimum_window_seconds": 600,
            "minimum_samples": 1000,
            "evaluation_time": "2026-08-13T12:00:00+00:00",
            "thresholds": {"max_error_rate": 0.02, "max_p95_ms": 450, "max_saturation": 0.75},
            "max_step_percent": 25,
            "allowed_target_cohorts": ["canary-25", "canary-50"],
            "approval_expires_at": "2026-08-14T12:00:00+00:00",
        }

    def valid_observation(self) -> dict:
        digest = "sha256:promotion-29-current"
        return {
            "identity": {
                "release_id": "release-29",
                "environment": "staging",
                "current_cohort": "canary-10",
                "target_cohort": "canary-25",
                "run_id": "run-29",
                "promotion_id": "promotion-29-001",
                "evidence_digest": digest,
                "policy_version": "rollout-policy-v3",
            },
            "stage_order": ["observe", "metrics", "policy", "approval", "handoff"],
            "stages": {
                "observe": {
                    "state": "window_complete",
                    "evidence_digest": digest,
                    "run_id": "run-29",
                    "window_seconds": 900,
                    "sample_count": 2400,
                    "audit_event_id": "audit-29-observe",
                },
                "metrics": {
                    "state": "metrics_passed",
                    "evidence_digest": digest,
                    "run_id": "run-29",
                    "error_rate": 0.004,
                    "p95_ms": 240,
                    "saturation": 0.48,
                    "audit_event_id": "audit-29-metrics",
                },
                "policy": {
                    "state": "step_allowed",
                    "evidence_digest": digest,
                    "current_cohort": "canary-10",
                    "target_cohort": "canary-25",
                    "step_percent": 15,
                    "audit_event_id": "audit-29-policy",
                },
                "approval": {
                    "state": "approval_bound",
                    "evidence_digest": digest,
                    "owner": "release-owner",
                    "scope": "canary-10->canary-25",
                    "expires_at": "2026-08-14T12:00:00+00:00",
                    "audit_event_id": "audit-29-approval",
                },
                "handoff": {
                    "state": "handoff_ready",
                    "evidence_digest": digest,
                    "next_owner": "platform-executor",
                    "decision": "promote_to_next_cohort",
                    "idempotency_key": "promotion-29-001",
                    "audit_event_id": "audit-29-handoff",
                },
            },
            "executed_promotions": [],
        }

    def run_result(self, intent: dict | None = None, observation: dict | None = None) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "intent.json").write_text(json.dumps(intent or self.valid_intent()), encoding="utf-8")
            (root / "observation.json").write_text(json.dumps(observation or self.valid_observation()), encoding="utf-8")
            return check_promotion(root / "intent.json", root / "observation.json")

    def test_promotion_ready(self):
        self.assertEqual(self.run_result(), {"allowed": True, "state": "promotion_ready", "reasons": []})

    def test_identity_mismatch_blocks_before_stage_checks(self):
        observation = self.valid_observation()
        observation["identity"]["run_id"] = "run-old"
        result = self.run_result(observation=observation)
        self.assertEqual(result["state"], "blocked_identity")
        self.assertIn("identity_mismatch:run_id", result["reasons"])

    def test_observation_window_and_samples_are_required(self):
        observation = self.valid_observation()
        observation["stages"]["observe"]["window_seconds"] = 100
        observation["stages"]["observe"]["sample_count"] = 10
        result = self.run_result(observation=observation)
        self.assertIn("observation_window_incomplete", result["reasons"])
        self.assertIn("observation_samples_insufficient", result["reasons"])

    def test_metrics_thresholds_block(self):
        observation = self.valid_observation()
        observation["stages"]["metrics"]["error_rate"] = 0.2
        observation["stages"]["metrics"]["p95_ms"] = 900
        observation["stages"]["metrics"]["saturation"] = 0.9
        result = self.run_result(observation=observation)
        self.assertIn("metric_error_rate_exceeded", result["reasons"])
        self.assertIn("metric_p95_exceeded", result["reasons"])
        self.assertIn("metric_saturation_exceeded", result["reasons"])

    def test_target_cohort_must_be_allowed(self):
        observation = self.valid_observation()
        observation["stages"]["policy"]["target_cohort"] = "all-users"
        result = self.run_result(observation=observation)
        self.assertIn("target_cohort_not_allowed", result["reasons"])

    def test_step_size_must_not_exceed_policy(self):
        observation = self.valid_observation()
        observation["stages"]["policy"]["step_percent"] = 40
        result = self.run_result(observation=observation)
        self.assertIn("promotion_step_exceeded", result["reasons"])

    def test_approval_scope_and_expiry_are_checked(self):
        observation = self.valid_observation()
        observation["stages"]["approval"]["scope"] = "canary-10->all-users"
        observation["stages"]["approval"]["expires_at"] = "2020-01-01T00:00:00+00:00"
        result = self.run_result(observation=observation)
        self.assertIn("approval_scope_mismatch", result["reasons"])
        self.assertIn("approval_expired", result["reasons"])

    def test_handoff_is_required(self):
        observation = self.valid_observation()
        observation["stages"]["handoff"]["next_owner"] = ""
        observation["stages"]["handoff"]["idempotency_key"] = ""
        result = self.run_result(observation=observation)
        self.assertIn("handoff_incomplete", result["reasons"])

    def test_duplicate_promotion_is_blocked(self):
        observation = self.valid_observation()
        observation["executed_promotions"] = ["promotion-29-001"]
        result = self.run_result(observation=observation)
        self.assertIn("duplicate_promotion", result["reasons"])

    def test_missing_stage_and_unknown_stage_are_reported(self):
        observation = self.valid_observation()
        del observation["stages"]["approval"]
        observation["stages"]["unexpected"] = {}
        result = self.run_result(observation=observation)
        self.assertIn("stage_missing:approval", result["reasons"])
        self.assertIn("stage_unknown:unexpected", result["reasons"])

    def test_deterministic_and_non_mutating(self):
        intent = self.valid_intent()
        observation = self.valid_observation()
        before_intent = copy.deepcopy(intent)
        before_observation = copy.deepcopy(observation)
        first = self.run_result(intent=intent, observation=observation)
        second = self.run_result(intent=intent, observation=observation)
        self.assertEqual(first, second)
        self.assertEqual(intent, before_intent)
        self.assertEqual(observation, before_observation)


if __name__ == "__main__":
    import unittest

    unittest.main()
