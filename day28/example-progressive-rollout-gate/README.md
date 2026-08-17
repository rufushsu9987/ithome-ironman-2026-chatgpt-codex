# Day 28 Runnable Example：Progressive Rollout Gate

這個範例把一次漸進式上線拆成五個可觀察關卡：

- `identity`：確認 release、environment、cohort、flag key 與 run 是同一輪。
- `canary`：確認錯誤率、延遲與 cohort 對應都在門檻內。
- `flag`：確認 feature flag 綁到正確分組，且 kill switch 可用。
- `rollback`：確認回退目標、觸發條件與時間限制都有留下紀錄。
- `health`：確認健康檢查回讀的是同一輪 run 的結果。

Gate 只讀兩份 JSON，不會部署、改變 flag、發 token 或呼叫外部 API。它輸出 `allowed`、`state` 與固定 reason code，讓同一組輸入可以在 deploy、QA 和稽核時重跑。

## 快速執行

```bash
python3 evidence_rollout_gate.py fixtures/intent.json fixtures/observation.json
```

預期結果：

```json
{
  "allowed": true,
  "state": "pipeline_ready",
  "reasons": []
}
```

## 測試

```bash
python3 -m unittest -v
```

測試涵蓋成功、identity drift、缺少或未知 stage、順序錯誤、狀態錯誤、digest drift、audit 缺失、canary 門檻、flag mapping、rollback contract、health readback，以及 deterministic retry。

## Requirement → behavior

| Requirement | Executable behavior |
| --- | --- |
| 同一輪 rollout 才能比較 | identity 不一致回傳 `identity_mismatch:*` |
| 五個 stage 都要存在 | 缺少 stage 回傳 `stage_missing:*` |
| stage 必須依序完成 | 回傳 `stage_order_invalid:*` |
| 每段都綁同一份證據 | digest 漂移回傳 `stage_digest_mismatch:*` |
| canary 必須在門檻內 | 回傳 `canary_p95_exceeded` 或 `canary_error_rate_exceeded` |
| flag 必須能對應 | 回傳 `flag_mapping_mismatch` 或 `flag_key_mismatch` |
| rollback 必須可執行 | 缺少 target、trigger 或 timeout 就阻擋 |
| health 必須回讀同一輪 | 回傳 `health_readback_mismatch` 或 `health_run_mismatch` |
| 所有結果可稽核 | 缺少 `audit_event_id` 就阻擋 |
