import unittest
from datetime import date

from export_service import (
    ExportService,
    ExportWorker,
    InMemoryState,
    Order,
    User,
)


class ExportServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.state = InMemoryState(
            orders=[
                Order("A-001", "tenant-a", date(2026, 8, 1), 1200),
                Order("B-001", "tenant-b", date(2026, 8, 1), 9999),
            ]
        )
        self.service = ExportService(self.state, job_id_factory=lambda: "job-001")
        self.admin = User("u-admin", "tenant-a", "tenant_admin")

    def create(self, **overrides):
        payload = {
            "user": self.admin,
            "tenant_id": "tenant-a",
            "request_id": "req-001",
            "start_date": date(2026, 8, 1),
            "end_date": date(2026, 8, 31),
        }
        payload.update(overrides)
        return self.service.create_export(**payload)

    def test_non_admin_is_rejected_without_creating_job(self):
        response = self.create(user=User("u-viewer", "tenant-a", "viewer"))
        self.assertEqual(403, response.status_code)
        self.assertEqual({}, self.state.jobs)
        self.assertEqual("export.rejected", self.state.audit_log[-1]["event"])

    def test_cross_tenant_admin_is_rejected(self):
        response = self.create(user=User("u-other", "tenant-b", "tenant_admin"))
        self.assertEqual(403, response.status_code)
        self.assertEqual([], self.state.queue)

    def test_date_range_over_31_days_is_rejected(self):
        response = self.create(end_date=date(2026, 9, 1))
        self.assertEqual(422, response.status_code)
        self.assertEqual("date_range", response.body["field"])

    def test_accepted_request_returns_202_and_enqueues_job(self):
        response = self.create()
        self.assertEqual(202, response.status_code)
        self.assertEqual({"job_id": "job-001", "reused": False}, response.body)
        self.assertEqual(["job-001"], self.state.queue)

    def test_same_request_id_is_idempotent(self):
        first = self.create()
        second = self.create()
        self.assertEqual(first.body["job_id"], second.body["job_id"])
        self.assertTrue(second.body["reused"])
        self.assertEqual(1, len(self.state.jobs))
        self.assertEqual(1, len(self.state.queue))

    def test_worker_exports_only_current_tenant_and_creates_short_lived_url(self):
        self.create()
        worker = ExportWorker(self.state)
        job = worker.process_next()
        assert job is not None
        assert job.object_key is not None
        self.assertEqual("completed", job.status)
        csv_text = self.state.objects[job.object_key].decode("utf-8")
        self.assertIn("A-001", csv_text)
        self.assertNotIn("B-001", csv_text)
        self.assertEqual(
            "https://download.example/exports/tenant-a/job-001.csv?ttl=600",
            worker.create_download_url("job-001"),
        )


if __name__ == "__main__":
    unittest.main()
