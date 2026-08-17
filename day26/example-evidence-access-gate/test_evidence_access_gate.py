#!/usr/bin/env python3
"""Tests for Day 26 Evidence Access Gate."""
from __future__ import annotations

import copy
import unittest

from evidence_access_gate import evaluate_access

BASE_INTENT = {
    "incident_id": "inc-26-001",
    "closeout_id": "closeout-26-001",
    "run_id": "run-26-1",
    "evidence_digest": "sha256:incident-26-current",
    "environment_id": "env-prod",
    "target": "production",
    "allowed_requester_roles": ["incident_responder", "incident_commander"],
    "allowed_purposes": ["incident_investigation", "audit_review"],
    "max_access_seconds": 1800,
    "approval_max_age_seconds": 900,
    "permitted_fields": {
        "recovery": ["candidate_id", "state", "evidence_digest"],
        "impact": ["window_seconds", "sample_count", "aggregate_metrics"],
    },
}

BASE_OBSERVATION = {
    "incident_id": "inc-26-001",
    "closeout_id": "closeout-26-001",
    "run_id": "run-26-1",
    "evidence_digest": "sha256:incident-26-current",
    "environment_id": "env-prod",
    "target": "production",
    "observed_at_epoch": 10_000,
    "access_request": {
        "requester_id": "alice",
        "requester_role": "incident_responder",
        "purpose": "incident_investigation",
        "evidence_names": ["recovery", "impact"],
        "field_scope": {
            "recovery": ["candidate_id", "state"],
            "impact": ["window_seconds", "sample_count", "aggregate_metrics"],
        },
        "requested_at_epoch": 9_900,
        "expires_at_epoch": 10_900,
    },
    "evidence_inventory": {
        "recovery": {
            "readable": True,
            "storage_state": "archived",
            "digest": "sha256:incident-26-current",
            "fields": ["candidate_id", "state", "evidence_digest"],
        },
        "impact": {
            "readable": True,
            "storage_state": "online",
            "digest": "sha256:incident-26-current",
            "fields": ["window_seconds", "sample_count", "aggregate_metrics"],
        },
    },
    "access_approval": {
        "incident_id": "inc-26-001",
        "closeout_id": "closeout-26-001",
        "run_id": "run-26-1",
        "evidence_digest": "sha256:incident-26-current",
        "environment_id": "env-prod",
        "target": "production",
        "requester_id": "alice",
        "purpose": "incident_investigation",
        "decision": "approved",
        "scope": "inc-26-001/production/alice/incident_investigation",
        "approved_at_epoch": 9_700,
    },
    "audit_anchor": {
        "event_id": "access-event-26-001",
        "request_digest": "sha256:request-26-current",
        "evidence_digest": "sha256:incident-26-current",
        "recorded_at_epoch": 9_950,
    },
}


class EvidenceAccessGateTests(unittest.TestCase):
    def test_access_is_eligible_when_request_is_minimal_and_bound(self):
        result = evaluate_access(BASE_INTENT, BASE_OBSERVATION)
        self.assertEqual(result, {"allowed": True, "state": "access_eligible", "reasons": []})

    def test_identity_drift_is_blocked_before_scope_checks(self):
        observed = copy.deepcopy(BASE_OBSERVATION)
        observed["run_id"] = "run-other"
        result = evaluate_access(BASE_INTENT, observed)
        self.assertEqual(result["state"], "blocked_identity")
        self.assertEqual(result["reasons"], ["identity_mismatch:run_id"])

    def test_role_and_purpose_are_separate_allowlists(self):
        observed = copy.deepcopy(BASE_OBSERVATION)
        observed["access_request"]["requester_role"] = "developer"
        observed["access_request"]["purpose"] = "curiosity"
        result = evaluate_access(BASE_INTENT, observed)
        self.assertIn("requester_role_not_allowed", result["reasons"])
        self.assertIn("purpose_not_allowed", result["reasons"])

    def test_evidence_and_field_scope_are_minimal(self):
        observed = copy.deepcopy(BASE_OBSERVATION)
        observed["access_request"]["evidence_names"].append("approval")
        observed["access_request"]["field_scope"]["recovery"].append("raw_customer_payload")
        result = evaluate_access(BASE_INTENT, observed)
        self.assertIn("evidence_not_allowed:approval", result["reasons"])
        self.assertIn("field_scope_exceeded:recovery:raw_customer_payload", result["reasons"])

    def test_unreadable_or_digest_drifted_inventory_is_blocked(self):
        observed = copy.deepcopy(BASE_OBSERVATION)
        observed["evidence_inventory"]["impact"]["readable"] = False
        observed["evidence_inventory"]["recovery"]["digest"] = "sha256:old"
        result = evaluate_access(BASE_INTENT, observed)
        self.assertIn("access_evidence_not_readable:impact", result["reasons"])
        self.assertIn("access_evidence_digest_mismatch:recovery", result["reasons"])

    def test_access_window_must_be_current_and_short(self):
        observed = copy.deepcopy(BASE_OBSERVATION)
        observed["access_request"]["requested_at_epoch"] = 10_100
        observed["access_request"]["expires_at_epoch"] = 12_500
        result = evaluate_access(BASE_INTENT, observed)
        self.assertIn("access_requested_at_future", result["reasons"])
        self.assertIn("access_window_too_long", result["reasons"])

    def test_approval_scope_requester_and_age_are_checked(self):
        observed = copy.deepcopy(BASE_OBSERVATION)
        observed["access_approval"]["scope"] = "inc-other/production/alice/incident_investigation"
        observed["access_approval"]["requester_id"] = "bob"
        observed["access_approval"]["approved_at_epoch"] = 8_000
        result = evaluate_access(BASE_INTENT, observed)
        self.assertIn("approval_scope_mismatch", result["reasons"])
        self.assertIn("approval_requester_mismatch", result["reasons"])
        self.assertIn("approval_expired", result["reasons"])

    def test_audit_anchor_must_bind_the_request_and_evidence(self):
        observed = copy.deepcopy(BASE_OBSERVATION)
        observed["audit_anchor"].pop("event_id")
        observed["audit_anchor"]["evidence_digest"] = "sha256:old"
        result = evaluate_access(BASE_INTENT, observed)
        self.assertIn("audit_anchor_missing", result["reasons"])
        self.assertIn("audit_digest_mismatch", result["reasons"])

    def test_missing_or_empty_field_scope_is_fail_closed(self):
        observed = copy.deepcopy(BASE_OBSERVATION)
        observed["access_request"]["field_scope"]["impact"] = []
        observed["evidence_inventory"]["recovery"]["fields"].remove("state")
        observed["access_request"]["field_scope"]["recovery"] = ["state"]
        result = evaluate_access(BASE_INTENT, observed)
        self.assertIn("field_scope_empty:impact", result["reasons"])
        self.assertIn("field_not_available:recovery:state", result["reasons"])

    def test_retry_is_deterministic_and_does_not_mutate_inputs(self):
        intent = copy.deepcopy(BASE_INTENT)
        observed = copy.deepcopy(BASE_OBSERVATION)
        intent_before = copy.deepcopy(intent)
        observed_before = copy.deepcopy(observed)
        first = evaluate_access(intent, observed)
        second = evaluate_access(intent, observed)
        self.assertEqual(first, second)
        self.assertEqual(intent, intent_before)
        self.assertEqual(observed, observed_before)


if __name__ == "__main__":
    unittest.main()
