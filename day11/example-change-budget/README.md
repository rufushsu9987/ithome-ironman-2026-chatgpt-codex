# Day 11：Change Budget 範例

這個 Python 標準函式庫範例接在 Day 10 Freshness Gate 後面，檢查 agent 執行中的實際變更是否仍符合原本核准的 Change Intent。

`change_budget.py` 是唯讀、deterministic、fail-closed 的 Gate：它不執行命令、不修改 git、不自動放寬預算，只比較 intent 與 runner 提供的 observation，輸出 JSON 報告。

## 執行完整測試

```bash
python3 -m unittest -v
python3 -m py_compile change_budget.py test_change_budget.py
```

目前驗證範圍：

| 行為 | 測試 |
| --- | --- |
| 符合 intent 的變更放行 | `test_matching_change_is_allowed` |
| 路徑不在 allowlist 阻擋 | `test_path_outside_allowlist_is_blocked` |
| forbidden path 強制阻擋 | `test_forbidden_path_is_blocked_even_if_otherwise_in_scope` |
| 檔案數超過上限阻擋 | `test_file_count_budget_is_blocked` |
| diff 行數超過上限阻擋 | `test_diff_line_budget_is_blocked` |
| command allowlist 與數量檢查 | `test_command_allowlist_and_count_are_enforced` |
| Context／source commit mismatch | `test_context_and_commit_mismatch_are_blocked` |
| deterministic、read-only retry | `test_same_input_is_deterministic_and_read_only` |

## 從 fixture 執行 Gate

```bash
python3 change_budget.py fixtures/intent.json fixtures/observed.json
```

成功路徑會輸出 `allowed: true`、`state: allowed`、空的 `reasons`，並列出檔案數、diff 行數與命令數的實際檢查值；退出碼為 0。

若把 observation 改成包含 `services/billing/api.py`、`.github/workflows/ci.yml` 或 `rm -rf ...`，Gate 會輸出具體的 `path_out_of_scope`、`path_forbidden` 或 `command_not_allowed`，並以非 0 退出。

## 檔案

- `change_budget.py`：Change Intent、path、command、file count 與 diff budget 檢查。
- `test_change_budget.py`：Python `unittest` 行為測試。
- `fixtures/intent.json`：本次 `orders-export` 變更的核准意圖。
- `fixtures/observed.json`：符合預算的執行觀測資料。
