# SLO Impact Gate 範例

這個小範例用 Python 標準函式庫，唯讀判斷一個 deployment candidate 是否有足夠證據顯示沒有超過使用者可靠性門檻。

## 執行

```bash
cd day20/example-slo-impact-gate
python3 -m unittest -v
python3 -m py_compile slo_impact_gate.py test_slo_impact_gate.py
python3 slo_impact_gate.py fixtures/intent.json fixtures/observation.json
```

成功 fixture 的 process exit code 是 `0`，輸出包含：

```json
{
  "allowed": true,
  "state": "slo_impact_clear",
  "reasons": []
}
```

若用測試中的 blocked fixture，Gate 會回報具體 reason code；CLI 會以非零 exit code fail-closed，而不會把不完整證據當成成功。

## 驗收對照

| Given | When | Then |
| --- | --- | --- |
| window 完成、samples 足夠，三項 SLO 指標在門檻內 | 執行 `evaluate_impact` | `slo_impact_clear` |
| availability 低於 SLO | 執行 `evaluate_impact` | `metric_availability_below_target` |
| p95 latency 或 burn rate 超標 | 執行 `evaluate_impact` | 對應的 `metric_*_exceeded` |
| check 缺少或不是 `passed` | 執行 `evaluate_impact` | `check_missing:*` 或 `check_not_passed:*` |
| serving candidate 漂移 | 執行 `evaluate_impact` | `serving_candidate_mismatch` |
| 相同輸入重試 | 再執行一次 | JSON 相同，輸入不被修改 |

Gate 不會修改部署、調整 threshold、切換 route、回滾或發表結果。它只產生可以交給 release owner 的證據。
