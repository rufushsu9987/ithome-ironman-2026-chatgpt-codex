from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path
from unittest import TestCase

from evidence_rollout_gate import check_pipeline


class ProgressiveRolloutGateTests(TestCase):
    def valid_intent(self) -> dict:
        return {
            "identity": {
                "release_id": "r28",
                "environment": "staging",
                "cohort": "canary-10",
                "flag_key": "search-beta",
                "run_id": "run-28",
            },
            "evidence_digest": "sha256:rollout-28-current",
            "thresholds": {"max_p95_ms": 450, "max_error_rate": 0.02},
            "required_stages": ["identity", "canary", "flag", "rollback", "health"],
        }

    def valid_observation(self) -> dict:
        digest = "sha256:rollout-28-current"
        return {
            "identity": {
                "release_id": "r28",
                "environment": "staging",
                "cohort": "canary-10",
                "flag_key": "search-beta",
                "run_id": "run-28",
            },
            "stage_order": ["identity", "canary", "flag", "rollback", "health"],
            "stages": {
                "identity": {
                    "state": "identity_bound",
                    "evidence_digest": digest,
                    "audit_event_id": "audit-28-identity",
                },
                "canary": {
                    "state": "canary_passed",
                    "p95_ms": 220,
                    "error_rate": 0.005,
                    "cohort_match": True,
                    "evidence_digest": digest,
                    "audit_event_id": "audit-28-canary",
                },
                "flag": {
                    "state": "flag_bound",
                    "flag_key": "search-beta",
                    "mapping_match": True,
                    "kill_switch_ready": True,
                    "evidence_digest": digest,
                    "audit_event_id": "audit-28-flag",
                },
                "rollback": {
                    "state": "rollback_ready",
                    "target": "release-27",
                    "trigger": "error_rate_or_p95",
                    "timeout_seconds": 300,
                    "evidence_digest": digest,
                    "audit_event_id": "audit-28-rollback",
                },
                "health": {
                    "state": "health_passed",
                    "readback_match": True,
                    "run_id": "run-28",
                    "evidence_digest": digest,
                    "audit_event_id": "audit-28-health",
                },
            },
        }

    def run_result(self, intent: dict | None = None, observation: dict | None = None) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "intent.json").write_text(
                json.dumps(intent or self.valid_intent(), ensure_ascii=False), encoding="utf-8"
            )
            (root / "observation.json").write_text(
                json.dumps(observation or self.valid_observation(), ensure_ascii=False), encoding="utf-8"
            )
            return check_pipeline(root / "intent.json", root / "observation.json")

    def test_pipeline_ready(self):
        result = self.run_result()
        self.assertEqual(result, {"allowed": True, "state": "pipeline_ready", "reasons": []})

    def test_identity_mismatch_blocks_before_stage_checks(self):
        observation = self.valid_observation()
        observation["identity"]["release_id"] = "r27"
        result = self.run_result(observation=observation)
        self.assertFalse(result["allowed"])
        self.assertEqual(result["state"], "blocked_identity")
        self.assertIn("identity_mismatch:release_id", result["reasons"])

    def test_missing_stage_is_reported(self):
        observation = self.valid_observation()
        del observation["stages"]["rollback"]
        observation["stage_order"].remove("rollback")
        result = self.run_result(observation=observation)
        self.assertIn("stage_missing:rollback", result["reasons"])

    def test_unknown_stage_is_reported(self):
        observation = self.valid_observation()
        observation["stages"]["deploy"] = observation["stages"]["health"]
        observation["stage_order"].append("deploy")
        result = self.run_result(observation=observation)
        self.assertIn("stage_unknown:deploy", result["reasons"])

    def test_stage_order_is_a_contract(self):
        observation = self.valid_observation()
        observation["stage_order"] = ["identity", "canary", "rollback", "flag", "health"]
        result = self.run_result(observation=observation)
        self.assertIn("stage_order_invalid:flag_before_rollback", result["reasons"])

    def test_stage_state_must_match(self):
        observation = self.valid_observation()
        observation["stages"]["flag"]["state"] = "flag_pending"
        result = self.run_result(observation=observation)
        self.assertIn("stage_state_invalid:flag", result["reasons"])

    def test_stage_digest_must_match(self):
        observation = self.valid_observation()
        observation["stages"]["canary"]["evidence_digest"] = "sha256:old"
        result = self.run_result(observation=observation)
        self.assertIn("stage_digest_mismatch:canary", result["reasons"])

    def test_audit_event_is_required(self):
        observation = self.valid_observation()
        observation["stages"]["health"]["audit_event_id"] = ""
        result = self.run_result(observation=observation)
        self.assertIn("audit_event_missing:health", result["reasons"])

    def test_canary_threshold_blocks(self):
        observation = self.valid_observation()
        observation["stages"]["canary"]["p95_ms"] = 900
        result = self.run_result(observation=observation)
        self.assertIn("canary_p95_exceeded", result["reasons"])

    def test_flag_mapping_blocks(self):
        observation = self.valid_observation()
        observation["stages"]["flag"]["mapping_match"] = False
        result = self.run_result(observation=observation)
        self.assertIn("flag_mapping_mismatch", result["reasons"])

    def test_rollback_contract_blocks(self):
        observation = self.valid_observation()
        observation["stages"]["rollback"]["target"] = ""
        result = self.run_result(observation=observation)
        self.assertIn("rollback_target_missing", result["reasons"])

    def test_health_readback_blocks(self):
        observation = self.valid_observation()
        observation["stages"]["health"]["readback_match"] = False
        result = self.run_result(observation=observation)
        self.assertIn("health_readback_mismatch", result["reasons"])

    def test_input_is_not_mutated_and_result_is_deterministic(self):
        intent = self.valid_intent()
        observation = self.valid_observation()
        before = copy.deepcopy(observation)
        first = self.run_result(intent=intent, observation=observation)
        second = self.run_result(intent=intent, observation=observation)
        self.assertEqual(first, second)
        self.assertEqual(observation, before)


if __name__ == "__main__":
    import unittest

    unittest.main()
