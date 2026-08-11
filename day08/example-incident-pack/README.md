# Day 8：Audit Trail／Incident Pack 範例

這個範例把 Day 7 的 Release Gate 往發布後延伸：用 JSONL 保存不可重複的事件，再把事件整理成可以交接給值班人員的 Incident Pack。

## 執行測試

```bash
python3 -m unittest -v
```

目前驗證範圍：

| 行為 | 測試 |
| --- | --- |
| 回滾事故產生 resolved pack | `test_rollback_incident_is_resolved_with_traceable_timeline` |
| 未解決事故不能被報成成功 | `test_open_incident_cannot_be_reported_as_success` |
| 缺少 deployed 事件時阻擋 | `test_missing_deployed_event_blocks_pack` |
| 不同 change_id 不可混合 | `test_mixed_change_ids_are_rejected` |
| 重複 event_id 不可追加 | `test_duplicate_event_id_is_rejected_when_appending` |

## 直接從 fixture 產生 Incident Pack

```bash
python3 incident_pack.py fixtures/audit.jsonl orders-export-20260811
```

預期結論包含：

```json
{
  "status": "resolved",
  "resolution": "rollback",
  "last_event_id": "e6"
}
```

## 檔案

- `incident_pack.py`：事件驗證、JSONL 追加、Incident Pack 彙整。
- `test_incident_pack.py`：標準函式庫 `unittest` 測試。
- `fixtures/audit.jsonl`：一次健康檢查失敗、最後完成回滾的事件時間線。
