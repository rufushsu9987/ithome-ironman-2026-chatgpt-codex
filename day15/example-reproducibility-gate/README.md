# Reproducibility Gate 範例

這個小範例用 Python 標準函式庫檢查一次 AI change run 是否具備可重現的最低證據：

1. intent 與 run 的 `context_id`、`source_commit`、`input_digest`、`environment_id` 必須一致。
2. toolchain 與 dependency lock digest 必須逐項相同。
3. intent 宣告的每個 expected output 都要存在、狀態為 `ready`，並反向帶回相同 source、input 與 environment identity。
4. 缺少、漂移、未知或尚未完成的輸出都用 deterministic reason code 阻擋。
5. Gate 只讀取輸入，不執行測試、不修改 digest、不替人類批准發布。

## 執行

```bash
cd day15/example-reproducibility-gate
python3 -m unittest -v
python3 -m py_compile reproducibility_gate.py test_reproducibility.py
python3 reproducibility_gate.py fixtures/intent.json fixtures/run.json
```

成功 fixture 應輸出 `allowed: true`、`state: reproducible`、`reasons: []`，CLI 退出碼為 0。若把 source commit、input digest、toolchain、lock 或 output identity 改掉，CLI 會以非 0 退出並列出可行動的 reason code。
