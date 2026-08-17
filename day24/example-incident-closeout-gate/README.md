# Incident Closeout Gate

這個範例模擬 recovery verified 之後的唯讀結案資格判斷。它不呼叫 incident、ticket、database、traffic 或通知 API，也不會修改輸入 JSON。

## 執行

```bash
cd day24/example-incident-closeout-gate
python3 -m unittest -v
python3 -m py_compile incident_closeout_gate.py test_incident_closeout_gate.py
python3 incident_closeout_gate.py fixtures/intent.json fixtures/observation.json
```

成功輸出：

```json
{
  "allowed": true,
  "state": "closeout_eligible",
  "reasons": []
}
```

## 行為對照

| 驗收條件 | 實作行為 | 測試 |
| --- | --- | --- |
| 同一個 incident identity | 比對 incident、recovery、run、candidate、source、input、environment、target | `test_identity_drift_is_blocked_before_other_checks` |
| Recovery 已驗證且 impact window 達標 | 檢查 recovery state、時間與 samples | `test_recovery_and_impact_window_are_required` |
| Critical follow-up 有責任人與期限 | 檢查 owner、due time、status、digest | `test_followup_owner_due_and_status_are_required` |
| Postmortem／learning 可回放 | 檢查 incident id 與 evidence digest | `test_learning_and_postmortem_digest_drift_are_blocked` |
| 人類核准有效 | 檢查 role、scope、decision、age 與 identity | `test_approval_scope_role_and_age_are_checked` |
| 可重試且不改輸入 | 同一輸入得到相同 reason code | `test_retry_is_deterministic_and_does_not_mutate_inputs` |

`allowed=true` 只代表結案前提齊全，不代表 incident 已關閉。最後的 closeout 仍由人類 owner 執行。
