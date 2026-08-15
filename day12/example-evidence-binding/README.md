# Day 12：Evidence Binding 範例

這個 Python 標準函式庫範例接在 Day 11 Change Budget 後面，檢查 diff、tests、review 與 artifact 是否真的屬於同一個 Change Intent。

`evidence_binding.py` 是唯讀、deterministic、fail-closed 的 Gate：它不執行測試、不修改 git、不重寫原始證據，也不把相似的 commit 或時間戳猜成同一份 evidence。

## 執行完整測試

```bash
python3 -m unittest -v
python3 -m py_compile evidence_binding.py test_evidence_binding.py
```

目前驗證範圍：

| 行為 | 測試 |
| --- | --- |
| 同一 intent、context、commit 與 observation 的證據放行 | `test_matching_bundle_is_bound` |
| intent／context／source commit 不一致阻擋 | `test_identity_mismatch_is_blocked` |
| diff path 超出 Change Budget 阻擋 | `test_diff_path_outside_scope_is_blocked` |
| 測試未通過或缺少 digest 阻擋 | `test_test_status_and_digest_are_required` |
| review 不是 approved 阻擋 | `test_review_must_be_approved` |
| 缺少 required evidence kind 阻擋 | `test_required_evidence_kind_is_required` |
| artifact identity 重複或綁錯 commit 阻擋 | `test_artifact_identity_is_unique_and_bound` |
| 相同輸入 deterministic 且不修改輸入 | `test_same_input_is_deterministic_and_read_only` |

## 從 fixture 執行 Gate

```bash
python3 evidence_binding.py fixtures/intent.json fixtures/evidence.json
```

成功 fixture 會輸出 `allowed: true`、`state: bound`、空的 `reasons`，並列出 identity、required evidence 與 artifact 檢查結果；退出碼為 0。

若把 evidence 改成另一個 `source_commit`、把測試狀態改成 `failed`、把 review 改成 `pending`，或加入 `services/billing/api.py`，Gate 會輸出具體 reason code，並以非 0 退出。

## 設計界線

- Gate 只比較 intent 與 runner 提供的 evidence，不執行外部命令。
- Gate 不會替缺少的 `source_commit`、digest 或 review 補值。
- Gate 通過只代表證據可以交給 Verify，不代表功能正確、可以 merge 或可以發布。

## 檔案

- `evidence_binding.py`：identity、scope、tests、review、required evidence 與 artifact 檢查。
- `test_evidence_binding.py`：Python `unittest` 行為測試。
- `fixtures/intent.json`：本次 `orders-export` 變更的核准意圖。
- `fixtures/evidence.json`：與 intent 完整綁定的成功證據。
