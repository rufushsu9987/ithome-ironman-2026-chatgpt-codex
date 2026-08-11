import json
import tempfile
import unittest
from pathlib import Path

from incident_pack import IncidentPackError, append_event, build_incident_pack


CHANGE_ID = "orders-export-20260811"
SOURCE_COMMIT = "abc1234"


def event(event_id: str, timestamp: str, action: str, outcome: str = "pass") -> dict:
    return {
        "event_id": event_id,
        "change_id": CHANGE_ID,
        "timestamp": timestamp,
        "actor": "release-bot",
        "action": action,
        "outcome": outcome,
        "source_commit": SOURCE_COMMIT,
        "evidence": f"evidence/{event_id}.json",
    }


class IncidentPackTests(unittest.TestCase):
    def test_rollback_incident_is_resolved_with_traceable_timeline(self) -> None:
        events = [
            event("e1", "2026-08-11T09:00:00Z", "release_approved"),
            event("e2", "2026-08-11T09:05:00Z", "deployed"),
            event("e3", "2026-08-11T09:06:00Z", "health_check_failed", "fail"),
            event("e4", "2026-08-11T09:07:00Z", "incident_opened", "fail"),
            event("e5", "2026-08-11T09:10:00Z", "rollback_started"),
            event("e6", "2026-08-11T09:12:00Z", "rollback_completed"),
        ]

        pack = build_incident_pack(events, CHANGE_ID)

        self.assertEqual("resolved", pack["status"])
        self.assertEqual("rollback", pack["resolution"])
        self.assertEqual(["e1", "e2", "e3", "e4", "e5", "e6"], pack["timeline"])
        self.assertEqual("e6", pack["last_event_id"])

    def test_open_incident_cannot_be_reported_as_success(self) -> None:
        events = [
            event("e1", "2026-08-11T09:00:00Z", "release_approved"),
            event("e2", "2026-08-11T09:05:00Z", "deployed"),
            event("e3", "2026-08-11T09:06:00Z", "health_check_failed", "fail"),
            event("e4", "2026-08-11T09:07:00Z", "incident_opened", "fail"),
        ]

        pack = build_incident_pack(events, CHANGE_ID)

        self.assertEqual("open", pack["status"])
        self.assertEqual("rollback_or_fix", pack["next_action"])

    def test_missing_deployed_event_blocks_pack(self) -> None:
        events = [event("e1", "2026-08-11T09:00:00Z", "release_approved")]

        with self.assertRaisesRegex(IncidentPackError, "deployed"):
            build_incident_pack(events, CHANGE_ID)

    def test_mixed_change_ids_are_rejected(self) -> None:
        events = [event("e1", "2026-08-11T09:00:00Z", "release_approved")]
        other = event("e2", "2026-08-11T09:05:00Z", "deployed")
        other["change_id"] = "other-change"
        events.append(other)

        with self.assertRaisesRegex(IncidentPackError, "change_id"):
            build_incident_pack(events, CHANGE_ID)

    def test_duplicate_event_id_is_rejected_when_appending(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "audit.jsonl"
            first = event("e1", "2026-08-11T09:00:00Z", "release_approved")
            append_event(path, first)

            with self.assertRaisesRegex(IncidentPackError, "duplicate"):
                append_event(path, first)

            self.assertEqual(1, len(path.read_text(encoding="utf-8").splitlines()))
            self.assertEqual("e1", json.loads(path.read_text(encoding="utf-8"))["event_id"])


if __name__ == "__main__":
    unittest.main()
