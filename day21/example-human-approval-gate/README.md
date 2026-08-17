# Human Approval Gate 範例

這個小範例用 Python 標準函式庫，唯讀判斷一組 human approval 是否真的適用於同一個 change intent。它會驗證 identity、required evidence、approver role、approval age、scope、distinct approvers、minimum count 與禁止 self-approval。

## 執行

```bash
cd day21/example-human-approval-gate
python3 -m unittest -v
python3 -m py_compile human_approval_gate.py test_human_approval_gate.py
python3 human_approval_gate.py fixtures/intent.json fixtures/observation.json
```

成功 fixture 的 process exit code 是 `0`，輸出包含：

```json
{
  "allowed": true,
  "state": "approval_eligible",
  "reasons": []
}
```

若用測試中的 blocked fixture，Gate 會回報具體 reason code；CLI 會以非零 exit code fail-closed，而不會把不完整核准當成已授權。

## 驗收對照

| Given | When | Then |
| --- | --- | --- |
| required evidence、兩位不同 release owner、scope 與 identity 都一致 | 執行 `evaluate_approval` | `approval_eligible` |
| evidence 缺少、state 或 digest 不一致 | 執行 `evaluate_approval` | `evidence_*` reason |
| 核准過期、角色錯誤或 scope 漂移 | 執行 `evaluate_approval` | `approval_expired:*`、`approver_role_mismatch:*` 或 `approval_scope_mismatch:*` |
| proposer 核准自己的變更 | 執行 `evaluate_approval` | `self_approval:*` |
| rejected 或有效核准人數不足 | 執行 `evaluate_approval` | `approval_not_approved:*` 與／或 `approval_count_shortfall` |
| 相同輸入重試 | 再執行一次 | JSON 相同，輸入不被修改 |

Gate 不會修改 deployment、調整 threshold、切換 route、回滾、發布或改變權限。它只產生可以交給 release owner 的 evidence。
