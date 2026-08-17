# Day 26 runnable example：Evidence Access Gate

這個範例把「誰可以讀 retained evidence」做成一個唯讀、可重跑、fail-closed 的判斷層。它不讀取 evidence 內容、不發 token、不修改 IAM、不建立 signed URL，也不把 `access_eligible` 假裝成 `access_granted`。

## 執行

```bash
cd day26/example-evidence-access-gate
python3 -m unittest -v
python3 -m py_compile evidence_access_gate.py test_evidence_access_gate.py
python3 evidence_access_gate.py fixtures/intent.json fixtures/observation.json
```

成功 fixture 應輸出：

```json
{
  "allowed": true,
  "state": "access_eligible",
  "reasons": []
}
```

## 覆蓋的驗收行為

| 行為 | Gate 判斷 | 測試 |
| --- | --- | --- |
| 同一個 incident、closeout、run、digest、environment、target | identity 先比對，漂移立即阻擋 | `test_identity_drift_is_blocked_before_scope_checks` |
| requester role 與 purpose | 兩個 allowlist 分開檢查 | `test_role_and_purpose_are_separate_allowlists` |
| evidence surface | 只能申請 intent 宣告的 evidence | `test_evidence_and_field_scope_are_minimal` |
| field scope | requested fields 必須是允許且實際存在的欄位 | `test_evidence_and_field_scope_are_minimal`、`test_missing_or_empty_field_scope_is_fail_closed` |
| inventory 可回讀與 digest | `readable=true`、storage state 有效、digest 相同 | `test_unreadable_or_digest_drifted_inventory_is_blocked` |
| access time window | 時間不能在未來、不能過期或超過 policy | `test_access_window_must_be_current_and_short` |
| human approval | scope、requester、purpose、identity 與年齡都要正確 | `test_approval_scope_requester_and_age_are_checked` |
| audit anchor | event id、request digest、evidence digest 與 recorded time 必須存在 | `test_audit_anchor_must_bind_the_request_and_evidence` |
| retry | 相同輸入得到相同 reason code，輸入不被修改 | `test_retry_is_deterministic_and_does_not_mutate_inputs` |

`allowed=true` 只代表這次 request 具備交給授權執行層的前提，不代表任何檔案已被讀取、下載或公開。
