#!/usr/bin/env python3
"""Tests for Day 24 Incident Closeout Gate."""
from __future__ import annotations

import copy
import unittest

from incident_closeout_gate import evaluate_closeout

BASE_INTENT = {
    "incident_id": "inc-24-001",
    "recovery_id": "recovery-24-001",
    "run_id": "run-24-1",
    "candidate_id": "candidate-safe",
    "source_commit": "commit-a",
    "input_digest": "digest-a",
    "environment_id": "env-prod",
    "target": "production",
    "evidence_digest": "sha256:recovery-current",
    "min_impact_window_seconds": 1800,
    "min_impact_samples": 200,
    "critical_followups": ["monitoring", "data_audit", "runbook"],
    "allowed_approval_roles": ["incident_commander", "service_owner"],
    "approval_max_age_seconds": 900,
}

BASE_OBSERVATION = {
    "incident_id": "inc-24-001",
    "recovery_id": "recovery-24-001",
    "run_id": "run-24-1",
    "candidate_id": "candidate-safe",
    "source_commit": "commit-a",
    "input_digest": "digest-a",
    "environment_id": "env-prod",
    "target": "production",
    "observed_at_epoch": 5000,
    "recovery": {"state": "recovery_verified", "evidence_digest": "sha256:recovery-current"},
    "customer_impact_window": {"complete": True, "duration_seconds": 1800, "sample_count": 240},
    "followups": {
        "monitoring": {"owner_id": "alice", "due_at_epoch": 5200, "status": "completed", "evidence_digest": "sha256:recovery-current"},
        "data_audit": {"owner_id": "bob", "due_at_epoch": 5200, "status": "accepted", "evidence_digest": "sha256:recovery-current"},
        "runbook": {"owner_id": "carol", "due_at_epoch": 5200, "status": "completed", "evidence_digest": "sha256:recovery-current"},
    },
    "postmortem": {"status": "published", "incident_id": "inc-24-001", "evidence_digest": "sha256:recovery-current"},
    "learning_pack": {"status": "ready", "incident_id": "inc-24-001", "evidence_digest": "sha256:recovery-current"},
    "closeout_approval": {
        "incident_id": "inc-24-001",
        "recovery_id": "recovery-24-001",
        "run_id": "run-24-1",
        "candidate_id": "candidate-safe",
        "source_commit": "commit-a",
        "input_digest": "digest-a",
        "environment_id": "env-prod",
        "target": "production",
        "approver_id": "commander-alice",
        "role": "incident_commander",
        "decision": "approved",
        "approved_at_epoch": 4500,
        "scope": "inc-24-001/production",
    },
}


class IncidentCloseoutGateTests(unittest.TestCase):
    def test_closeout_is_eligible_when_all_evidence_is_bound(self):
        result = evaluate_closeout(BASE_INTENT, BASE_OBSERVATION)
        self.assertEqual(result, {"allowed": True, "state": "closeout_eligible", "reasons": []})

    def test_identity_drift_is_blocked_before_other_checks(self):
        observed = copy.deepcopy(BASE_OBSERVATION)
        observed["run_id"] = "run-other"
        result = evaluate_closeout(BASE_INTENT, observed)
        self.assertEqual(result["state"], "blocked_identity")
        self.assertEqual(result["reasons"], ["identity_mismatch:run_id"])

    def test_recovery_and_impact_window_are_required(self):
        observed = copy.deepcopy(BASE_OBSERVATION)
        observed["recovery"]["state"] = "rollback_executed"
        observed["customer_impact_window"]["complete"] = False
        observed["customer_impact_window"]["sample_count"] = 4
        result = evaluate_closeout(BASE_INTENT, observed)
        self.assertIn("recovery_not_verified", result["reasons"])
        self.assertIn("impact_window_incomplete", result["reasons"])
        self.assertIn("impact_sample_count_shortfall", result["reasons"])

    def test_followup_owner_due_and_status_are_required(self):
        observed = copy.deepcopy(BASE_OBSERVATION)
        observed["followups"]["monitoring"].pop("owner_id")
        observed["followups"]["data_audit"]["due_at_epoch"] = 4000
        observed["followups"]["runbook"]["status"] = "pending"
        result = evaluate_closeout(BASE_INTENT, observed)
        self.assertIn("followup_owner_missing:monitoring", result["reasons"])
        self.assertIn("followup_overdue:data_audit", result["reasons"])
        self.assertIn("followup_not_complete:runbook", result["reasons"])

    def test_learning_and_postmortem_digest_drift_are_blocked(self):
        observed = copy.deepcopy(BASE_OBSERVATION)
        observed["postmortem"]["evidence_digest"] = "sha256:old"
        observed["learning_pack"]["status"] = "draft"
        result = evaluate_closeout(BASE_INTENT, observed)
        self.assertIn("postmortem_digest_mismatch", result["reasons"])
        self.assertIn("learning_pack_not_ready", result["reasons"])

    def test_approval_scope_role_and_age_are_checked(self):
        observed = copy.deepcopy(BASE_OBSERVATION)
        observed["closeout_approval"]["role"] = "developer"
        observed["closeout_approval"]["scope"] = "inc-other/production"
        observed["closeout_approval"]["approved_at_epoch"] = 1000
        result = evaluate_closeout(BASE_INTENT, observed)
        self.assertIn("closeout_approval_role_mismatch", result["reasons"])
        self.assertIn("closeout_approval_scope_mismatch", result["reasons"])
        self.assertIn("closeout_approval_expired", result["reasons"])

    def test_retry_is_deterministic_and_does_not_mutate_inputs(self):
        intent = copy.deepcopy(BASE_INTENT)
        observed = copy.deepcopy(BASE_OBSERVATION)
        intent_before = copy.deepcopy(intent)
        observed_before = copy.deepcopy(observed)
        first = evaluate_closeout(intent, observed)
        second = evaluate_closeout(intent, observed)
        self.assertEqual(first, second)
        self.assertEqual(intent, intent_before)
        self.assertEqual(observed, observed_before)


if __name__ == "__main__":
    unittest.main()
