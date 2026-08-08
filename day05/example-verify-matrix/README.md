# Day 5 Verify Matrix 範例

這個不依賴第三方套件的 Python 範例，把「代理人說完成了」改成可檢查的證據矩陣。它不會執行測試、不會批准 diff，也不會發布；它只驗證執行完成後提交的 manifest 是否足以進入 Deliver。

## 四層證據

| 層 | 驗證內容 |
| --- | --- |
| Contract | `context_id`、版本、`source_commit` 是否仍與 Plan 相同 |
| Process | 每個驗證命令是否真的有 `exit_code=0` 與可追溯 log |
| Behavior | Plan 宣告的每個 acceptance ref 是否都有 pass 結果與證據 |
| Review | diff 是否在白名單內、沒有碰唯讀路徑，且有人類 Review |

## 執行

```bash
python3 -m unittest -v
python3 verify_matrix.py policy.json plan.json verification.json
```

本次實際驗證結果：

```text
Ran 12 tests
OK
VERIFY_OK context=orders-export version=3 tasks=2 acceptance=4 evidence=10
TASK_VERIFIED id=export-api acceptance=2 evidence=5
TASK_VERIFIED id=export-worker acceptance=2 evidence=5
LAYERS contract,process,behavior,review
NEXT_STATE deliver
```

範例故意採用 fail-closed：context drift、命令失敗、缺少 acceptance 證據、diff 越過白名單、碰到唯讀路徑或 agent 自我核准，都會輸出 `VERIFY_BLOCKED` 並以非零狀態結束。
