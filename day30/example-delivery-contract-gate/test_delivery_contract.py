from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path
from unittest import TestCase

from delivery_contract_gate import check_delivery, evaluate_delivery


class DeliveryContractGateTests(TestCase):
    def valid_intent(self) -> dict:
        return json.loads((Path(__file__).parent / "fixtures/intent.json").read_text(encoding="utf-8"))

    def valid_observation(self) -> dict:
        return json.loads((Path(__file__).parent / "fixtures/observation.json").read_text(encoding="utf-8"))

    def run_result(self, intent: dict | None = None, observation: dict | None = None) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "intent.json").write_text(json.dumps(intent or self.valid_intent()), encoding="utf-8")
            (root / "observation.json").write_text(json.dumps(observation or self.valid_observation()), encoding="utf-8")
            return check_delivery(root / "intent.json", root / "observation.json")

    def test_delivery_ready(self):
        self.assertEqual(self.run_result(), {"allowed": True, "state": "delivery_ready", "reasons": []})

    def test_identity_mismatch_blocks_before_other_checks(self):
        observation = self.valid_observation()
        observation["identity"]["run_id"] = "run-old"
        result = self.run_result(observation=observation)
        self.assertEqual(result["state"], "blocked_identity")
        self.assertIn("identity_mismatch:run_id", result["reasons"])

    def test_missing_and_unknown_stages_are_blocked(self):
        observation = self.valid_observation()
        del observation["stages"]["review"]
        observation["stages"]["unexpected"] = {}
        result = self.run_result(observation=observation)
        self.assertIn("stage_missing:review", result["reasons"])
        self.assertIn("stage_unknown:unexpected", result["reasons"])

    def test_stage_order_and_state_are_checked(self):
        observation = self.valid_observation()
        observation["stage_order"] = ["context", "plan", "execute", "review", "verify", "deliver"]
        observation["stages"]["verify"]["state"] = "candidate"
        result = self.run_result(observation=observation)
        self.assertIn("stage_order_invalid", result["reasons"])
        self.assertIn("stage_state_invalid:verify", result["reasons"])

    def test_stage_digest_and_audit_are_required(self):
        observation = self.valid_observation()
        observation["stages"]["execute"]["evidence_digest"] = "sha256:old"
        observation["stages"]["review"].pop("audit_event_id")
        result = self.run_result(observation=observation)
        self.assertIn("stage_digest_mismatch:execute", result["reasons"])
        self.assertIn("audit_event_missing:review", result["reasons"])

    def test_missing_deliverable_is_blocked(self):
        observation = self.valid_observation()
        del observation["deliverables"]["video"]
        result = self.run_result(observation=observation)
        self.assertIn("deliverable_missing:video", result["reasons"])

    def test_unverified_or_empty_deliverable_is_blocked(self):
        observation = self.valid_observation()
        observation["deliverables"]["video"]["status"] = "generated"
        observation["deliverables"]["subtitles"]["bytes"] = 0
        result = self.run_result(observation=observation)
        self.assertIn("deliverable_not_verified:video", result["reasons"])
        self.assertIn("deliverable_empty:subtitles", result["reasons"])

    def test_absolute_path_is_rejected(self):
        observation = self.valid_observation()
        observation["deliverables"]["article"]["path"] = "/Users/example/article.md"
        result = self.run_result(observation=observation)
        self.assertIn("deliverable_path_absolute:article", result["reasons"])

    def test_media_qa_must_be_pass(self):
        observation = self.valid_observation()
        observation["deliverables"]["media_qa"]["qa_status"] = "PENDING_VISUAL_REVIEW"
        result = self.run_result(observation=observation)
        self.assertIn("media_qa_not_pass", result["reasons"])

    def test_external_boundary_and_publication_status_are_protected(self):
        observation = self.valid_observation()
        observation["external_boundary"] = "published"
        observation["publication_status"] = "public"
        result = self.run_result(observation=observation)
        self.assertIn("external_boundary_mismatch", result["reasons"])
        self.assertIn("publication_evidence_missing", result["reasons"])

    def test_handoff_and_idempotency_are_required(self):
        observation = self.valid_observation()
        observation["handoff"]["next_owner"] = ""
        observation["handoff"]["idempotency_key"] = "other-contract"
        result = self.run_result(observation=observation)
        self.assertIn("handoff_incomplete", result["reasons"])

        observation = self.valid_observation()
        observation["handoff"]["idempotency_key"] = "other-contract"
        result = self.run_result(observation=observation)
        self.assertIn("handoff_idempotency_mismatch", result["reasons"])

    def test_duplicate_delivery_is_blocked(self):
        observation = self.valid_observation()
        observation["executed_contracts"] = ["delivery-30-001"]
        result = self.run_result(observation=observation)
        self.assertIn("duplicate_delivery", result["reasons"])

    def test_deterministic_and_non_mutating(self):
        intent = self.valid_intent()
        observation = self.valid_observation()
        before_intent = copy.deepcopy(intent)
        before_observation = copy.deepcopy(observation)
        first = evaluate_delivery(intent, observation)
        second = evaluate_delivery(intent, observation)
        self.assertEqual(first, second)
        self.assertEqual(intent, before_intent)
        self.assertEqual(observation, before_observation)


if __name__ == "__main__":
    import unittest

    unittest.main()
