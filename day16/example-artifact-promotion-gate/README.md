# Artifact Promotion Gate 範例

這個範例示範如何在 Reproducibility Gate 通過後，再檢查一組 artifact 是否真的可以晉級到下一個交付階段。

## 一次執行

```bash
cd day16/example-artifact-promotion-gate
python3 -m unittest -v
python3 -m py_compile artifact_promotion_gate.py test_artifact_promotion.py
python3 artifact_promotion_gate.py fixtures/intent.json fixtures/observation.json
```

成功 fixture 會輸出：

```json
{
  "allowed": true,
  "state": "promotable",
  "reasons": []
}
```

## 驗收對照

| 行為 | 測試 |
| --- | --- |
| 完整 artifact bundle 放行 | `test_complete_bundle_is_promotable` |
| 舊 run 的 artifact 被擋下 | `test_artifact_from_other_run_is_blocked` |
| pending artifact 被擋下 | `test_pending_artifact_is_blocked` |
| skipped QA 不得冒充通過 | `test_skipped_required_check_is_blocked` |
| 缺少或未知 artifact | `test_missing_and_unknown_artifacts_are_blocked` |
| digest 漂移 | `test_digest_mismatch_is_blocked` |
| artifact identity 漂移 | `test_source_mismatch_is_blocked` |
| promotion target／owner 不符 | `test_promotion_request_mismatch_is_blocked` |
| 相同輸入 deterministic、read-only | `test_retry_is_deterministic_and_read_only` |

Gate 是唯讀檢查器；`promotable` 只代表可以交給 release owner，並不代表已經 promotion、發布或上線。
