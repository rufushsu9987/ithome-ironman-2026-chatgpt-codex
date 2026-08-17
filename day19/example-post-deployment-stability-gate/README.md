# Post-Deployment Stability Gate 範例

這個範例示範 Deployment Verification 通過後，如何再用一段時間的真實 observation，確認服務不是只有某一刻看起來正常。

## 一次執行

```bash
cd day19/example-post-deployment-stability-gate
python3 -m unittest -v
python3 -m py_compile post_deployment_stability_gate.py test_post_deployment_stability.py
python3 post_deployment_stability_gate.py fixtures/intent.json fixtures/observation.json
```

成功 fixture 會輸出：

```json
{
  "allowed": true,
  "state": "post_deployment_stable",
  "reasons": []
}
```

## 驗收對照

| 行為 | 測試 |
| --- | --- |
| 完整 observation window 與 metrics 放行 | `test_complete_window_is_stable` |
| window 尚未完成或時間不足 | `test_incomplete_window_is_blocked`、`test_window_too_short_is_blocked` |
| 樣本數不足 | `test_sample_shortfall_is_blocked` |
| error rate、latency、saturation 超標 | `test_error_rate_threshold_is_blocked`、`test_latency_threshold_is_blocked`、`test_saturation_threshold_is_blocked` |
| skipped 或缺少 required check | `test_skipped_check_is_blocked`、`test_missing_check_is_blocked` |
| traffic serving candidate 漂移 | `test_serving_candidate_mismatch_is_blocked` |
| source identity 漂移或 route 非 serving | `test_identity_drift_is_blocked`、`test_non_serving_route_is_blocked` |
| deterministic、read-only retry | `test_retry_is_deterministic_and_read_only` |

Gate 是唯讀檢查器；`post_deployment_stable` 只代表這段 observation 與 intent 一致，不代表已替人類調整容量、切流量、rollback 或公開發布。
