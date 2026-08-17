# Deployment Verification Gate 範例

這個範例示範 Release Candidate Gate 通過、部署動作完成後，如何再用唯讀 Gate 核對實際 deployment、rollout、replica、required checks 與 traffic serving 狀態。

## 一次執行

```bash
cd day18/example-deployment-verification-gate
python3 -m unittest -v
python3 -m py_compile deployment_verification_gate.py test_deployment_verification.py
python3 deployment_verification_gate.py fixtures/intent.json fixtures/observation.json
```

成功 fixture 會輸出：

```json
{
  "allowed": true,
  "state": "deployment_verified",
  "reasons": []
}
```

## 驗收對照

| 行為 | 測試 |
| --- | --- |
| 完整 deployment 與 traffic identity 放行 | `test_complete_deployment_is_verified` |
| deployment candidate 不符 | `test_deployed_candidate_must_match_intent` |
| artifact digest 漂移 | `test_deployed_artifact_digest_must_match` |
| rollout 未完成 | `test_rollout_must_be_complete` |
| ready replica 不足 | `test_all_declared_replicas_must_be_ready` |
| skipped required check 不得冒充通過 | `test_skipped_required_check_is_blocked` |
| 缺少 required check | `test_missing_required_check_is_blocked` |
| traffic 仍服務舊 candidate | `test_traffic_must_serve_the_candidate` |
| source/config identity 漂移 | `test_identity_drift_is_blocked`、`test_config_digest_drift_is_blocked` |
| deterministic、read-only retry | `test_retry_is_deterministic_and_read_only` |

Gate 是唯讀檢查器；`deployment_verified` 只代表這次觀察與 intent 一致，不代表已替人類部署、切流量或公開發布。
