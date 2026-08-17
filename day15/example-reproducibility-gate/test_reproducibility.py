import copy
import unittest

from reproducibility_gate import evaluate_reproducibility


CAPTURED_AT = "2026-08-15T09:30:00Z"


def intent(**overrides):
    value = {
        "intent_id": "intent-export-20260815-001",
        "context_id": "orders-export",
        "source_commit": "abc1234",
        "input_digest": "sha256:orders-input-v1",
        "environment_id": "env-python311",
        "toolchain": {"python": "3.11", "runner": "codex-runner-1"},
        "dependencies_lock_digest": "sha256:lock-v3",
        "expected_outputs": ["trace.json", "report.json"],
    }
    value.update(overrides)
    return value


def run(**overrides):
    value = {
        "run_id": "run-export-20260815-001",
        "intent_id": "intent-export-20260815-001",
        "context_id": "orders-export",
        "source_commit": "abc1234",
        "input_digest": "sha256:orders-input-v1",
        "environment_id": "env-python311",
        "toolchain": {"python": "3.11", "runner": "codex-runner-1"},
        "dependencies_lock_digest": "sha256:lock-v3",
        "captured_at": CAPTURED_AT,
        "outputs": [
            {
                "output_id": "trace.json",
                "status": "ready",
                "source_commit": "abc1234",
                "input_digest": "sha256:orders-input-v1",
                "environment_id": "env-python311",
                "artifact_digest": "sha256:trace-v1",
            },
            {
                "output_id": "report.json",
                "status": "ready",
                "source_commit": "abc1234",
                "input_digest": "sha256:orders-input-v1",
                "environment_id": "env-python311",
                "artifact_digest": "sha256:report-v1",
            },
        ],
    }
    value.update(overrides)
    return value


class ReproducibilityGateTests(unittest.TestCase):
    def test_complete_run_is_allowed(self):
        report = evaluate_reproducibility(intent(), run())
        self.assertTrue(report["allowed"])
        self.assertEqual("reproducible", report["state"])
        self.assertEqual([], report["reasons"])
        self.assertTrue(report["checks"]["toolchain"])
        self.assertTrue(report["checks"]["outputs_ready"])

    def test_source_commit_mismatch_is_blocked(self):
        changed = run(source_commit="def5678")
        report = evaluate_reproducibility(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("source_commit_mismatch", report["reasons"])

    def test_input_digest_mismatch_is_blocked(self):
        changed = run(input_digest="sha256:orders-input-v2")
        report = evaluate_reproducibility(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("input_digest_mismatch", report["reasons"])

    def test_toolchain_mismatch_is_blocked(self):
        changed = run(toolchain={"python": "3.12", "runner": "codex-runner-1"})
        report = evaluate_reproducibility(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("toolchain_mismatch:python", report["reasons"])

    def test_dependency_lock_mismatch_is_blocked(self):
        changed = run(dependencies_lock_digest="sha256:lock-v4")
        report = evaluate_reproducibility(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("dependency_lock_mismatch", report["reasons"])

    def test_missing_output_is_blocked(self):
        changed = copy.deepcopy(run())
        changed["outputs"] = changed["outputs"][:1]
        report = evaluate_reproducibility(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("output_missing:report.json", report["reasons"])

    def test_output_not_ready_is_blocked(self):
        changed = copy.deepcopy(run())
        changed["outputs"][1]["status"] = "pending"
        report = evaluate_reproducibility(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("output_not_ready:report.json", report["reasons"])

    def test_output_identity_mismatch_is_blocked(self):
        changed = copy.deepcopy(run())
        changed["outputs"][0]["environment_id"] = "env-python312"
        report = evaluate_reproducibility(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("output_environment_mismatch:trace.json", report["reasons"])

    def test_unknown_output_is_blocked(self):
        changed = copy.deepcopy(run())
        changed["outputs"].append(
            {
                "output_id": "debug.log",
                "status": "ready",
                "source_commit": "abc1234",
                "input_digest": "sha256:orders-input-v1",
                "environment_id": "env-python311",
                "artifact_digest": "sha256:debug-v1",
            }
        )
        report = evaluate_reproducibility(intent(), changed)
        self.assertFalse(report["allowed"])
        self.assertIn("output_unknown:debug.log", report["reasons"])

    def test_same_input_is_deterministic_and_read_only(self):
        original_intent = intent()
        original_run = run()
        first = evaluate_reproducibility(original_intent, original_run)
        second = evaluate_reproducibility(original_intent, original_run)
        self.assertEqual(first, second)
        self.assertEqual(original_intent, intent())
        self.assertEqual(original_run, run())
        self.assertEqual("run-export-20260815-001", first["checks"]["run_id"])


if __name__ == "__main__":
    unittest.main()
