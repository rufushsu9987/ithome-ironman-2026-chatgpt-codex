# Day 10：Freshness Gate 範例

這個 Python 標準函式庫範例把 Day 9 的 Learning Pack 再往執行前推一步：在 Codex 開始修改前，檢查 Context 與 learning 是否仍然新鮮、同一個 source commit、未過期且沒有超出 scope。

Freshness Gate 是唯讀、deterministic、fail-closed 的驗證器：它只輸出 JSON 報告，不修改 Context、不延長 expiry、不核准 learning，也不執行部署。

## 執行完整測試

```bash
python3 -m unittest -v
python3 -m py_compile freshness_gate.py test_freshness_gate.py
```

目前驗證範圍：

| 行為 | 測試 |
| --- | --- |
| 新鮮 Context 放行 | `test_fresh_context_is_allowed` |
| source commit 漂移阻擋 | `test_source_commit_drift_is_blocked` |
| Context 超過 max age 阻擋 | `test_context_age_is_blocked` |
| retired／expired／缺 evidence 阻擋 | `test_retired_expired_and_missing_evidence_learning_is_blocked` |
| 跨 Context 與 scope 越界阻擋 | `test_cross_context_and_out_of_scope_paths_are_blocked` |
| 相同輸入 deterministic、read-only | `test_same_input_is_deterministic_and_read_only` |

## 從 fixture 執行 Gate

```bash
python3 freshness_gate.py fixtures/context.json fixtures/request.json
```

成功路徑會輸出：

```json
{
  "allowed": true,
  "state": "fresh",
  "reasons": []
}
```

如果 source commit 不同，程式會輸出 `source_commit_mismatch` 並以非 0 退出；這是刻意的 fail-closed 行為。

## 檔案

- `freshness_gate.py`：Context、Learning、expiry 與 scope 檢查。
- `test_freshness_gate.py`：Python `unittest` 行為測試。
- `fixtures/context.json`：`orders-export` 的 Context Pack 與已核准 learning。
- `fixtures/request.json`：本次工作要檢查的 source commit、path 與時間。
