# Day 25 runnable example：Evidence Retention Gate

這個範例把「incident 可以結案」之後的證據留存，做成一個唯讀、可重跑、fail-closed 的判斷層。它不刪檔、不移動資料、不建立 legal hold，也不替團隊呼叫 archive API。

## 執行

```bash
cd day25/example-evidence-retention-gate
python3 -m unittest -v
python3 -m py_compile evidence_retention_gate.py test_evidence_retention_gate.py
python3 evidence_retention_gate.py fixtures/intent.json fixtures/observation.json
```

成功 fixture 應輸出：

```json
{
  "allowed": true,
  "state": "retention_ready",
  "reasons": []
}
```

## 覆蓋的驗收行為

| 行為 | Gate 判斷 | 測試 |
| --- | --- | --- |
| 同一個 incident／closeout／run／digest | 先比對 identity，漂移立即阻擋 | `test_identity_drift_is_blocked_before_retention_checks` |
| archive inventory 已完成 | 必須是 `inventory_verified` 且 `archive_complete=true` | `test_inventory_must_be_verified_and_archive_complete` |
| required evidence 完整 | 缺少 recovery、impact、follow-up、learning 或 approval 就阻擋 | `test_missing_required_evidence_is_fail_closed` |
| evidence 可回讀且儲存狀態有效 | `readable=true`，storage 為 `online` 或 `archived` | `test_unreadable_or_unknown_storage_is_blocked` |
| digest 沒有漂移 | 每一項 evidence 都要綁定同一個 digest | `test_digest_drift_is_blocked_per_evidence_item` |
| 留存期限涵蓋政策與現在 | `retain_until_epoch >= now + min_retention_seconds` | `test_retention_window_must_cover_now_and_policy` |
| legal hold 與 scope | 需要時 hold 必須 active，讀取 scope 必須精確一致 | `test_legal_hold_and_access_scope_are_required` |
| 重試不改輸入 | 相同輸入得到相同 reason code | `test_retry_is_deterministic_and_does_not_mutate_inputs` |

`allowed=true` 只代表目前的 retention evidence 足夠，並不代表可以刪除、移轉、公開或自動關閉任何事件。
