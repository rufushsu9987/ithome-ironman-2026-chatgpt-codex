# Day 3 Context Gate

這個 Python 標準函式庫範例把 Repository Context Pack 與 Plan 變成可執行的前置閘門，避免 Codex 或其他 agent 在錯誤上下文、越界路徑或未核准計畫下開始修改。

## 執行

```bash
python3 -m unittest -v
python3 context_gate.py context_pack.json plan.json
```

## 會檢查什麼？

- Context Pack 的版本、來源 commit、路徑白名單、唯讀範圍與驗證命令。
- `open_questions` 是否已清空。
- Plan 的 `context_id`／`context_version` 與 Context Pack 是否一致。
- task id 是否重複、依賴是否不存在或形成循環。
- task 路徑是否超出白名單或碰到唯讀／敏感範圍。
- 每個 task 是否有驗收條件與驗證命令。

這是教學用的最小 gate，不會取代實際 CI、分支保護、權限系統或人工 Code Review。
