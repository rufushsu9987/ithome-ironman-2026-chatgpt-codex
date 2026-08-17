# Day 14：Traceability Gate 範例

這個範例用 Python 標準函式庫，檢查一個變更的需求、實際 change、evidence artifact 與 release approval 是否能連成同一條可回查的責任鏈。

Traceability Gate 是唯讀、deterministic、fail-closed 的驗證器：

- 不執行測試，也不替測試產生 evidence。
- 不修改 intent、trace bundle 或任何 artifact。
- 不代替 release owner 核准發布。
- 所有 identity、雙向 link、commit 與 approval 條件都不符合時，輸出具體 reason code。

## 一鍵驗證

```bash
cd day14/example-traceability-gate
python3 -m unittest -v
python3 -m py_compile traceability_gate.py test_traceability.py
python3 traceability_gate.py fixtures/intent.json fixtures/trace.json
```

成功 fixture 會輸出：

```json
{
  "allowed": true,
  "state": "traceable",
  "reasons": []
}
```

CLI 遇到阻擋情境時會以非 0 結束，讓上游 pipeline 不能把未知當成通過。

## 需求對應

| 需求 | 實作與測試 |
| --- | --- |
| 每個 acceptance 都有 passed result 與反向 evidence | `test_complete_trace_is_allowed`、`test_missing_acceptance_result_is_blocked` |
| evidence 屬於同一個 source commit | `test_identity_mismatch_is_blocked`、`test_stale_artifact_commit_is_blocked` |
| change 與 artifact 雙向連結 | `test_change_artifact_must_link_back` |
| release owner 明確核准 | `test_release_requires_explicit_approval` |
| 缺少或不存在的 artifact fail-closed | `test_unknown_artifact_reference_is_blocked` |
| 輸入不被修改、重試結果一致 | `test_same_input_is_deterministic_and_read_only` |

## 輸入結構

- `fixtures/intent.json`：本次變更事先固定的 intent、acceptance、change 與 release owner。
- `fixtures/trace.json`：runner 產生的 acceptance results、changes、artifacts 與 release approval。

## Reason code 範例

- `acceptance_missing:AC-03`
- `acceptance_not_passed:AC-01`
- `artifact_not_linked:AC-01:artifact-02`
- `change_missing:CH-01`
- `change_artifact_not_linked:CH-01:artifact-01`
- `source_commit_mismatch`
- `release_not_approved`
- `release_owner_mismatch`

通過 Traceability Gate 只代表資料可以被逐項回查；仍要交給 Verify Matrix、Deliver Pack 與 Release Gate，不代表程式已部署或文章、影片已發布。
