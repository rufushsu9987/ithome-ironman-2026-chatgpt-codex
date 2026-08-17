# Day 27 Runnable Example：Incident Evidence Lifecycle Gate

這個範例把 Day 24–26 的三道 gate 串成一個唯讀的 pipeline readiness check：

- `closeout`：Incident 是否完成復原、學習與責任交接。
- `retention`：Evidence 是否仍在、可回讀、digest 沒有漂移。
- `access`：Evidence 的讀取請求是否已具備最小範圍與核准依據。

Lifecycle Gate 不會刪除 evidence、不會讀取內容、不會發 token，也不會呼叫外部 API。它只回傳 `allowed`、`state` 與可追蹤的 `reasons`，把「整條管線是否接得起來」變成可以重跑的檢查。

## 快速執行

```bash
python3 evidence_lifecycle_gate.py fixtures/intent.json fixtures/observation.json
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

目前共 10 項測試，涵蓋成功、identity drift、缺 stage、順序錯誤、digest drift、狀態錯誤、readback／approval 缺失、audit 缺失、未知 stage 與 deterministic retry。

## Requirement → behavior

| Requirement | Executable behavior |
| --- | --- |
| 三道 gate 必須全部存在 | 缺少任一 stage 回傳 `stage_missing:*` |
| stage 必須依序完成 | 順序錯誤回傳 `stage_order_invalid:*` |
| 所有 stage 綁同一份 evidence | digest 漂移回傳 `stage_digest_mismatch:*` |
| Retention 必須能回讀 | `readback_passed` 不是 `true` 就阻擋 |
| Access 必須有綁定核准 | `approval_bound` 不是 `true` 就阻擋 |
| 每一段都要可稽核 | 缺少 `audit_event_id` 就阻擋 |
| 重跑不能改輸入 | 相同輸入產生相同結果，且 input 不被 mutate |
