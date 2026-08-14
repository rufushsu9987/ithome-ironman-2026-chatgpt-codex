# Day 9：Learning Pack 範例

這個範例把 Day 8 的 Incident Pack 往下一次變更延伸：從已解決事故提煉可回溯、有限範圍、經人工核准的 Learning Pack，再 idempotently 套用到指定 Context。

## 執行測試

```bash
python3 -m unittest -v
```

目前驗證範圍：

| 行為 | 測試 |
| --- | --- |
| 已解決事故可建立 approved learning pack | `test_build_approved_pack_from_resolved_incident` |
| 未解決事故不能進入學習包 | `test_open_incident_is_blocked` |
| 缺少 evidence 或 scope 時阻擋 | `test_missing_evidence_or_scope_is_blocked` |
| approved 套用必須有人工核准 | `test_approved_without_human_approval_cannot_apply` |
| 不同 Context 不可混用 | `test_cross_context_apply_is_rejected` |
| 重試不重複加入 learning_id | `test_apply_is_idempotent` |

## 從 fixture 產生 Learning Pack

```bash
python3 learning_pack.py fixtures/learning.json context.json
```

成功輸出會包含：

```json
{
  "context_id": "orders-export",
  "learning_ids": ["learn-export-async-001"],
  "status": "approved"
}
```

## 檔案

- `learning_pack.py`：驗證、彙整與套用 Learning Pack。
- `test_learning_pack.py`：標準函式庫 `unittest` 測試。
- `fixtures/learning.json`：一筆由 resolved incident 提煉、已經人工核准的學習。
- `context.json`：可套用 learning refs 的最小 Context fixture。
