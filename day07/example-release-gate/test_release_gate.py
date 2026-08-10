import copy
import unittest

from release_gate import ReleaseGateError, validate_release


PLAN = {
    "release_id": "release-v7",
    "version": "2026.08.10",
    "source_commit": "approved-commit",
    "owner": "release-manager",
    "dependencies": ["api", "worker"],
}

PACKS = {
    "api": {
        "status": "READY_FOR_HANDOFF",
        "version": "2026.08.10",
        "source_commit": "approved-commit",
        "artifact_paths": ["artifacts/api.tar.gz", "evidence/api-tests.log"],
        "open_items": [],
    },
    "worker": {
        "status": "READY_FOR_HANDOFF",
        "version": "2026.08.10",
        "source_commit": "approved-commit",
        "artifact_paths": ["artifacts/worker.tar.gz", "evidence/worker-tests.log"],
        "open_items": [],
    },
}

APPROVALS = [
    {
        "release_id": "release-v7",
        "reviewer": "engineering-review",
        "role": "release-manager",
        "decision": "approved",
    }
]

ROLLBACK = {
    "owner": "oncall",
    "triggers": ["healthcheck_failure", "error_rate_threshold"],
    "steps": ["stop rollout", "restore previous version", "verify healthcheck"],
}


class ReleaseGateTests(unittest.TestCase):
    def test_complete_release_is_ready(self):
        result = validate_release(PLAN, PACKS, APPROVALS, ROLLBACK)
        self.assertEqual("READY_FOR_RELEASE", result["decision"])
        self.assertEqual("release-v7", result["release_id"])
        self.assertEqual(2, result["dependencies"])
        self.assertEqual("oncall", result["rollback_owner"])

    def test_missing_dependency_blocks(self):
        packs = copy.deepcopy(PACKS)
        del packs["worker"]
        with self.assertRaisesRegex(ReleaseGateError, "worker"):
            validate_release(PLAN, packs, APPROVALS, ROLLBACK)

    def test_dependency_version_drift_blocks(self):
        packs = copy.deepcopy(PACKS)
        packs["api"]["version"] = "2026.08.09"
        with self.assertRaisesRegex(ReleaseGateError, "version"):
            validate_release(PLAN, packs, APPROVALS, ROLLBACK)

    def test_open_item_blocks_release(self):
        packs = copy.deepcopy(PACKS)
        packs["api"]["open_items"] = [{"id": "OPEN-01", "status": "open"}]
        with self.assertRaisesRegex(ReleaseGateError, "OPEN"):
            validate_release(PLAN, packs, APPROVALS, ROLLBACK)

    def test_agent_approval_blocks_release(self):
        approvals = copy.deepcopy(APPROVALS)
        approvals[0]["reviewer"] = "agent"
        with self.assertRaisesRegex(ReleaseGateError, "human"):
            validate_release(PLAN, PACKS, approvals, ROLLBACK)

    def test_missing_rollback_trigger_blocks(self):
        rollback = copy.deepcopy(ROLLBACK)
        rollback["triggers"] = []
        with self.assertRaisesRegex(ReleaseGateError, "rollback"):
            validate_release(PLAN, PACKS, APPROVALS, rollback)

    def test_absolute_artifact_path_blocks(self):
        packs = copy.deepcopy(PACKS)
        packs["api"]["artifact_paths"] = ["/tmp/api.tar.gz"]
        with self.assertRaisesRegex(ReleaseGateError, "絕對路徑"):
            validate_release(PLAN, packs, APPROVALS, ROLLBACK)


if __name__ == "__main__":
    unittest.main(verbosity=2)
