# Day 29 Runnable Example：Rollout Promotion Gate

這個範例把「能不能從目前 cohort 放量到下一個 cohort」拆成五個唯讀關卡：

- `observe`：觀察窗與樣本數完整，且綁定同一個 run。
- `metrics`：error rate、p95 latency、saturation 都在門檻內。
- `policy`：current／target cohort、allowlist 與 step size 符合政策。
- `approval`：核准綁定本次 promotion、scope、digest 且未過期。
- `handoff`：下一個 owner、decision、idempotency key 與 audit event 完整。

Gate 只讀兩份 JSON，不會修改 feature flag、traffic、deployment 或輸入資料。它輸出 `allowed`、`state` 與固定 reason code，讓 deploy、QA、稽核與重試都能使用同一個判斷介面。

## 快速執行

```bash
python3 rollout_promotion_gate.py fixtures/intent.json fixtures/observation.json
```

預期結果：

```json
{
  "allowed": true,
  "state": "promotion_ready",
  "reasons": []
}
```

## 測試與語法檢查

```bash
python3 -m unittest -v
python3 -m py_compile rollout_promotion_gate.py test_rollout_promotion_gate.py
```

## Requirement → behavior

| Requirement | Executable behavior |
| --- | --- |
| 只用同一輪 evidence | identity 不一致回傳 `identity_mismatch:*` |
| 觀察窗完整 | 回傳 `observation_window_incomplete` 或 `observation_samples_insufficient` |
| metrics 都達標 | 回傳 `metric_error_rate_exceeded`、`metric_p95_exceeded` 或 `metric_saturation_exceeded` |
| 不能任意跳 cohort | 回傳 `target_cohort_not_allowed` 或 `promotion_step_exceeded` |
| 核准屬於這次 promotion | 回傳 `approval_missing`、`approval_expired`、`approval_scope_mismatch` 或 `approval_digest_mismatch` |
| 交接可被執行 | 回傳 `handoff_incomplete` |
| retry 不可重複放量 | 已存在的 `promotion_id` 回傳 `duplicate_promotion` |
| 同一輸入重跑一致 | 測試確認結果一致且 input 未被 mutate |
