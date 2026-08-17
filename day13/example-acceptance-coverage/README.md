# Day 13：Acceptance Coverage 範例

這個 Python 標準函式庫範例接在 Day 12 Evidence Binding 後面，檢查一份變更的每個驗收條件，是否都有通過結果與正確綁定的 evidence artifact。

`acceptance_coverage.py` 是唯讀、deterministic、fail-closed 的 Gate：它不執行測試、不補猜缺少的 evidence、不修改 intent 或 runner 輸入。它只回答一個問題：這次交付是否把所有宣告的 acceptance criteria 都覆蓋起來？

## 執行完整測試

```bash
python3 -m unittest -v
python3 -m py_compile acceptance_coverage.py test_acceptance_coverage.py
```

目前驗證範圍：

| 行為 | 測試 |
| --- | --- |
| 每個 acceptance 都有通過且綁定的 evidence | `test_every_acceptance_has_passing_evidence` |
| 缺少 acceptance 結果阻擋 | `test_missing_acceptance_is_blocked` |
| acceptance 失敗阻擋 | `test_failed_acceptance_is_blocked` |
| acceptance 沒有 evidence 阻擋 | `test_missing_evidence_is_blocked` |
| evidence 沒有反向綁定 acceptance 阻擋 | `test_evidence_must_link_back_to_acceptance` |
| 未宣告的 acceptance 阻擋 | `test_unknown_acceptance_is_blocked` |
| intent／context／source commit 不一致阻擋 | `test_identity_mismatch_is_blocked` |
| evidence id 重複阻擋 | `test_duplicate_evidence_id_is_blocked` |
| 相同輸入 deterministic 且不修改輸入 | `test_same_input_is_deterministic_and_read_only` |

## 從 fixture 執行 Gate

```bash
python3 acceptance_coverage.py fixtures/intent.json fixtures/evidence.json
```

成功 fixture 會輸出 `allowed: true`、`state: covered`、空的 `reasons`，並列出 acceptance 數量與 identity 檢查；退出碼為 0。若刪除一個 acceptance、把 status 改成 `failed`，或把 artifact 的 `acceptance_ids` 改錯，Gate 會輸出具體 reason code，並以非 0 退出。

## 設計界線

- Gate 只比較 frozen intent 與 runner 提供的 evidence，不執行外部命令。
- Gate 不會把「整體測試通過」推論成所有需求都已驗證。
- Gate 通過只代表驗收條件有完整 evidence coverage，不代表功能正確、可以 merge 或可以發布。
- 若需求改變，應建立新的 intent 與 acceptance ids；不要修改舊 bundle 來讓覆蓋率看起來完整。

## 檔案

- `acceptance_coverage.py`：acceptance、identity、狀態與 evidence link 檢查。
- `test_acceptance_coverage.py`：Python `unittest` 行為測試。
- `fixtures/intent.json`：本次變更宣告的 acceptance ids。
- `fixtures/evidence.json`：與 intent 完整綁定的成功 evidence。
