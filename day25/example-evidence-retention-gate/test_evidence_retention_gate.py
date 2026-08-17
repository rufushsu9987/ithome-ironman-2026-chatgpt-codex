#!/usr/bin/env python3
"""Tests for Day 25 Evidence Retention Gate."""
from __future__ import annotations

import copy
import unittest

from evidence_retention_gate import evaluate_retention

BASE_INTENT = {
    "incident_id": "inc-25-001",
    "closeout_id": "closeout-25-001",
    "run_id": "run-25-1",
    "evidence_digest": "sha256:incident-25-current",
    "environment_id": "env-prod",
    "target": "production",
    "min_retention_seconds": 604800,
    "required_evidence": ["recovery", "impact", "followup", "learning", "approval"],
    "required_access_scope": "incident:inc-25-001",
    "legal_hold_required": True,
}

BASE_OBSERVATION = {
    "incident_id": "inc-25-001",
    "closeout_id": "closeout-25-001",
    "run_id": "run-25-1",
    "evidence_digest": "sha256:incident-25-current",
    "environment_id": "env-prod",
    "target": "production",
    "observed_at_epoch": 2_000_000,
    "retention": {"state": "inventory_verified", "archive_complete": True},
    "legal_hold": {"state": "active", "reason": "audit-window"},
    "access_scope": "incident:inc-25-001",
    "evidence": {
        "recovery": {"readable": True, "storage_state": "archived", "digest": "sha256:incident-25-current", "created_at_epoch": 1_000_000, "retain_until_epoch": 2_000_000 + 604800},
        "impact": {"readable": True, "storage_state": "archived", "digest": "sha256:incident-25-current", "created_at_epoch": 1_000_000, "retain_until_epoch": 2_000_000 + 604800},
        "followup": {"readable": True, "storage_state": "online", "digest": "sha256:incident-25-current", "created_at_epoch": 1_000_000, "retain_until_epoch": 2_000_000 + 604800},
        "learning": {"readable": True, "storage_state": "archived", "digest": "sha256:incident-25-current", "created_at_epoch": 1_000_000, "retain_until_epoch": 2_000_000 + 604800},
        "approval": {"readable": True, "storage_state": "archived", "digest": "sha256:incident-25-current", "created_at_epoch": 1_000_000, "retain_until_epoch": 2_000_000 + 604800},
    },
}


class EvidenceRetentionGateTests(unittest.TestCase):
    def test_retention_is_ready_when_inventory_is_readable_and_bound(self):
        result = evaluate_retention(BASE_INTENT, BASE_OBSERVATION)
        self.assertEqual(result, {"allowed": True, "state": "retention_ready", "reasons": []})

    def test_identity_drift_is_blocked_before_retention_checks(self):
        observed = copy.deepcopy(BASE_OBSERVATION)
        observed["closeout_id"] = "closeout-other"
        result = evaluate_retention(BASE_INTENT, observed)
        self.assertEqual(result["state"], "blocked_identity")
        self.assertEqual(result["reasons"], ["identity_mismatch:closeout_id"])

    def test_inventory_must_be_verified_and_archive_complete(self):
        observed = copy.deepcopy(BASE_OBSERVATION)
        observed["retention"]["state"] = "indexing"
        observed["retention"]["archive_complete"] = False
        result = evaluate_retention(BASE_INTENT, observed)
        self.assertIn("retention_inventory_not_verified", result["reasons"])
        self.assertIn("retention_archive_incomplete", result["reasons"])

    def test_missing_required_evidence_is_fail_closed(self):
        observed = copy.deepcopy(BASE_OBSERVATION)
        observed["evidence"].pop("learning")
        result = evaluate_retention(BASE_INTENT, observed)
        self.assertIn("evidence_missing:learning", result["reasons"])

    def test_unreadable_or_unknown_storage_is_blocked(self):
        observed = copy.deepcopy(BASE_OBSERVATION)
        observed["evidence"]["impact"]["readable"] = False
        observed["evidence"]["recovery"]["storage_state"] = "missing"
        result = evaluate_retention(BASE_INTENT, observed)
        self.assertIn("evidence_not_readable:impact", result["reasons"])
        self.assertIn("evidence_storage_invalid:recovery", result["reasons"])

    def test_digest_drift_is_blocked_per_evidence_item(self):
        observed = copy.deepcopy(BASE_OBSERVATION)
        observed["evidence"]["followup"]["digest"] = "sha256:old"
        result = evaluate_retention(BASE_INTENT, observed)
        self.assertIn("evidence_digest_mismatch:followup", result["reasons"])

    def test_retention_window_must_cover_now_and_policy(self):
        observed = copy.deepcopy(BASE_OBSERVATION)
        observed["evidence"]["approval"]["retain_until_epoch"] = 1_999_900
        observed["evidence"]["recovery"]["retain_until_epoch"] = 2_000_000 + 100
        result = evaluate_retention(BASE_INTENT, observed)
        self.assertIn("evidence_retention_expired:approval", result["reasons"])
        self.assertIn("evidence_retention_too_short:recovery", result["reasons"])

    def test_created_and_expiry_timestamps_are_required(self):
        observed = copy.deepcopy(BASE_OBSERVATION)
        observed["evidence"]["impact"].pop("created_at_epoch")
        observed["evidence"]["learning"].pop("retain_until_epoch")
        result = evaluate_retention(BASE_INTENT, observed)
        self.assertIn("evidence_created_at_missing:impact", result["reasons"])
        self.assertIn("evidence_retain_until_missing:learning", result["reasons"])

    def test_legal_hold_and_access_scope_are_required(self):
        observed = copy.deepcopy(BASE_OBSERVATION)
        observed["legal_hold"]["state"] = "released"
        observed["access_scope"] = "incident:other"
        result = evaluate_retention(BASE_INTENT, observed)
        self.assertIn("legal_hold_missing", result["reasons"])
        self.assertIn("access_scope_mismatch", result["reasons"])

    def test_retry_is_deterministic_and_does_not_mutate_inputs(self):
        intent = copy.deepcopy(BASE_INTENT)
        observed = copy.deepcopy(BASE_OBSERVATION)
        intent_before = copy.deepcopy(intent)
        observed_before = copy.deepcopy(observed)
        first = evaluate_retention(intent, observed)
        second = evaluate_retention(intent, observed)
        self.assertEqual(first, second)
        self.assertEqual(intent, intent_before)
        self.assertEqual(observed, observed_before)


if __name__ == "__main__":
    unittest.main()
