# Day 6 Deliver Pack 範例

這個不依賴第三方套件的 Python 範例，把 Day 5 的 Verify Matrix 證據整理成可交接的 Deliver Pack。它不會部署、合併或發布；它只驗證交接包裡的身分、證據、變更範圍、OPEN 項目與下一步責任人是否完整。

## 會檢查什麼

- Plan 與 verification 的 `context_id`、`context_version`、`source_commit` 一致。
- 每個 task 都有 Contract、Process、Behavior、Review 四層 `pass`。
- Process 命令有非空 `argv`、`exit_code=0` 與 evidence。
- Behavior 的 acceptance refs 與 Plan 完整對應。
- Review 的 diff path 是相對路徑，不能含 `..`，且 reviewer 不能在要求人工 Review 時填 `agent`。
- 交接摘要、OPEN item 的 owner／action，以及 next step 的 owner／action 都非空。

## 執行

```bash
python3 -m unittest -v
python3 deliver_pack.py \
  --plan fixtures/plan.json \
  --verification fixtures/verification.json \
  --change fixtures/change.json \
  --out DELIVER_PACK.md
```

驗證成功會寫出 `DELIVER_PACK.md`，並印出：

```text
DELIVER_PACK_READY context=orders-export version=3 tasks=2 acceptance=4 evidence=10 open_items=1
NEXT_OWNER release-manager
```

範例採用 fail-closed：身分漂移、未驗證狀態、缺少 layer、命令失敗、acceptance 缺口、不安全路徑、沒有交接責任人，都會輸出 `DELIVER_PACK_BLOCKED` 並以非零狀態結束。
