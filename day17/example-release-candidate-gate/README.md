# Release Candidate Gate 範例

這個範例示範 Artifact Promotion 通過後，如何再檢查一個 Release Candidate 是否具備進入發布決策的條件。

## 一次執行

```bash
cd day17/example-release-candidate-gate
python3 -m unittest -v
python3 -m py_compile release_candidate_gate.py test_release_candidate_gate.py
python3 release_candidate_gate.py fixtures/intent.json fixtures/observation.json
```

成功 fixture 會輸出：

```json
{
  "allowed": true,
  "state": "releasable",
  "reasons": []
}
```

## 驗收對照

| 行為 | 測試 |
| --- | --- |
| candidate、artifact、checks、window、rollback、approval 都通過 | `test_complete_candidate_is_releasable` |
| 舊 run 的 artifact 被擋下 | `test_artifact_from_other_run_is_blocked` |
| pending artifact 被擋下 | `test_pending_artifact_is_blocked` |
| 缺少或未知 artifact 被擋下 | `test_missing_and_unknown_artifacts_are_blocked` |
| digest 漂移被擋下 | `test_digest_mismatch_is_blocked` |
| skipped required check 不得冒充通過 | `test_skipped_required_check_is_blocked` |
| release window 過期被擋下 | `test_release_window_is_fail_closed` |
| rollback 尚未 ready 被擋下 | `test_rollback_must_be_ready_and_matching` |
| approval target／owner 不符被擋下 | `test_approval_target_and_owner_are_checked` |
| identity 漂移與 deterministic retry | `test_identity_mismatch_is_blocked`、`test_retry_is_deterministic_and_read_only` |

Gate 是唯讀檢查器；`releasable` 只代表可以交給 release owner 做發布決策，不代表已部署、已切流或已公開發布。
