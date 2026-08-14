import copy
import unittest

from learning_pack import LearningPackError, apply_learning, build_learning_pack


CONTEXT_ID = "orders-export"


def record(**overrides):
    value = {
        "learning_id": "learn-export-async-001",
        "context_id": CONTEXT_ID,
        "incident_id": "inc-20260811-01",
        "change_id": "orders-export-20260811",
        "source_commit": "abc1234",
        "observed_at": "2026-08-11T09:40:00Z",
        "incident_status": "resolved",
        "lesson": "大檔案匯出必須交給背景 worker。",
        "evidence_refs": ["incident/e6-rollback-completed.json"],
        "scope": ["services/export/**"],
        "status": "approved",
        "owner": "platform-owner",
        "approved_by": "engineering-review",
        "approved_at": "2026-08-12T01:10:00Z",
    }
    value.update(overrides)
    return value


class LearningPackTests(unittest.TestCase):
    def test_build_approved_pack_from_resolved_incident(self):
        pack = build_learning_pack([record()], CONTEXT_ID)
        self.assertEqual("approved", pack["status"])
        self.assertEqual(["learn-export-async-001"], pack["learning_ids"])
        self.assertEqual("engineering-review", pack["lessons"][0]["approved_by"])

    def test_open_incident_is_blocked(self):
        with self.assertRaisesRegex(LearningPackError, "resolved"):
            build_learning_pack([record(incident_status="open")], CONTEXT_ID)

    def test_missing_evidence_or_scope_is_blocked(self):
        with self.assertRaisesRegex(LearningPackError, "evidence_refs"):
            build_learning_pack([record(evidence_refs=[])], CONTEXT_ID)
        with self.assertRaisesRegex(LearningPackError, "scope"):
            build_learning_pack([record(scope=[])], CONTEXT_ID)

    def test_approved_without_human_approval_cannot_apply(self):
        value = record(approved_by="", approved_at="")
        with self.assertRaisesRegex(LearningPackError, "approved_by"):
            build_learning_pack([value], CONTEXT_ID)

    def test_cross_context_apply_is_rejected(self):
        pack = build_learning_pack([record()], CONTEXT_ID)
        with self.assertRaisesRegex(LearningPackError, "different context_id"):
            apply_learning(pack, {"context_id": "billing", "context_version": 2})

    def test_apply_is_idempotent(self):
        pack = build_learning_pack([record()], CONTEXT_ID)
        context = {"context_id": CONTEXT_ID, "context_version": 3, "learning_refs": []}
        first = apply_learning(pack, copy.deepcopy(context))
        second = apply_learning(pack, first)
        self.assertEqual(["learn-export-async-001"], second["learning_refs"])
        self.assertEqual(4, second["context_version"])
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
