import copy
import json
import unittest
from pathlib import Path

from release_candidate_gate import evaluate_release_candidate


ROOT = Path(__file__).parent


def intent(**overrides):
    value = json.loads((ROOT / "fixtures/intent.json").read_text(encoding="utf-8"))
    value.update(overrides)
    return value


def observation(**overrides):
    value = json.loads((ROOT / "fixtures/observation.json").read_text(encoding="utf-8"))
    value.update(overrides)
    return value


class ReleaseCandidateGateTests(unittest.TestCase):
    def test_complete_candidate_is_releasable(self):
        report = evaluate_release_candidate(intent(), observation())
        self.assertTrue(report["allowed"])
        self.assertEqual("releasable", report["state"])
        self.assertEqual([], report["reasons"])

    def test_artifact_from_other_run_is_blocked(self):
        changed = observation()
        changed["artifacts"][0]["produced_by_run"] = "run-release-old"
        report = evaluate_release_candidate(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("artifact_run_mismatch:release-bundle.tgz", report["reasons"])

    def test_pending_artifact_is_blocked(self):
        changed = observation()
        changed["artifacts"][1]["status"] = "pending"
        report = evaluate_release_candidate(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("artifact_not_ready:release-manifest.json", report["reasons"])

    def test_missing_and_unknown_artifacts_are_blocked(self):
        changed = observation()
        changed["artifacts"] = changed["artifacts"][:2]
        changed["artifacts"].append(
            {
                "artifact_id": "debug.log",
                "status": "ready",
                "artifact_digest": "sha256:debug-v1",
                "produced_by_run": "run-release-20260817-001",
                "source_commit": "abc1234",
                "input_digest": "sha256:orders-input-v2",
                "environment_id": "env-python311",
                "target": "staging",
            }
        )
        report = evaluate_release_candidate(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("artifact_missing:rollback-bundle.tgz", report["reasons"])
        self.assertIn("artifact_unknown:debug.log", report["reasons"])

    def test_digest_mismatch_is_blocked(self):
        changed = observation()
        changed["artifacts"][0]["artifact_digest"] = "sha256:release-old"
        report = evaluate_release_candidate(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("artifact_digest_mismatch:release-bundle.tgz", report["reasons"])

    def test_skipped_required_check_is_blocked(self):
        changed = observation()
        changed["checks"]["smoke"] = "skipped"
        report = evaluate_release_candidate(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("check_not_passed:smoke", report["reasons"])

    def test_release_window_is_fail_closed(self):
        changed = observation(now="2026-08-17T12:00:00Z")
        report = evaluate_release_candidate(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("release_window_expired", report["reasons"])

    def test_rollback_must_be_ready_and_matching(self):
        changed = observation()
        changed["rollback"]["ready"] = False
        report = evaluate_release_candidate(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("rollback_not_ready", report["reasons"])

    def test_approval_target_and_owner_are_checked(self):
        changed = observation()
        changed["approval"] = {
            "requested": True,
            "granted": True,
            "target": "production",
            "owner": "other@example.invalid",
        }
        report = evaluate_release_candidate(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("approval_target_mismatch", report["reasons"])
        self.assertIn("approval_owner_mismatch", report["reasons"])

    def test_identity_mismatch_is_blocked(self):
        changed = observation(source_commit="def5678")
        report = evaluate_release_candidate(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("source_commit_mismatch", report["reasons"])

    def test_retry_is_deterministic_and_read_only(self):
        original_intent = intent()
        original_observation = observation()
        first = evaluate_release_candidate(original_intent, original_observation)
        second = evaluate_release_candidate(original_intent, original_observation)
        self.assertEqual(first, second)
        self.assertEqual(original_intent, intent())
        self.assertEqual(original_observation, observation())
        self.assertEqual("run-release-20260817-001", first["checks"]["run_id"])


if __name__ == "__main__":
    unittest.main()
