# Fixtures

- `intent.json`：宣告這次 run 可以晉級到 `release-candidate` 的 artifact 清單、digest、必要 checks 與 owner。
- `observation.json`：runner 回報的實際 bundle。每份 artifact 都反向帶回 run、source、input、environment 與 checks。

執行成功 fixture：

```bash
python3 ../artifact_promotion_gate.py fixtures/intent.json fixtures/observation.json
```

Gate 只回報 `promotable`，不會複製檔案或發布。
