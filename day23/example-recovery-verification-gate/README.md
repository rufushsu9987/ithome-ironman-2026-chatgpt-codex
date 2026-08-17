# Recovery Verification Gate

這個範例模擬 rollback 之後的唯讀恢復驗證。它不呼叫 deployment、traffic、database 或 incident API，也不會修改輸入 JSON。

## 一鍵執行

```bash
cd day23/example-recovery-verification-gate
python3 -m unittest -v
python3 -m py_compile recovery_verification_gate.py test_recovery_verification_gate.py
python3 recovery_verification_gate.py fixtures/intent.json fixtures/observation.json
```

成功 fixture 應輸出：

```json
{
  "allowed": true,
  "state": "recovery_verified",
  "reasons": []
}
```

## 輸入與輸出

- `fixtures/intent.json`：rollback identity、恢復門檻、required checks 與 recovery evidence digest。
- `fixtures/observation.json`：實際 rollback 結果、recovery window、metrics、checks、traffic 與 evidence。
- `recovery_verification_gate.py`：只讀、deterministic 的判斷器。
- `test_recovery_verification_gate.py`：成功、identity drift、rollback／target、window／sample、metric、check、traffic／digest 與 retry 案例。

`allowed=true` 只代表恢復證據通過；它不是自動關閉 incident，也不是發布、切流或修改資料的許可。最後的 closeout 仍由具責任的人讀取 evidence 後決定。
