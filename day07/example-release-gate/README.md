# Day 7 Release Gate 範例

Day 6 的 Deliver Pack 只回答「下一個人能不能接手」。Day 7 再往前一步，回答「多個交接包能不能一起進入發布窗口」。

這個不依賴第三方套件的 Python 範例採 fail-closed：只有所有相依套件的交接包、版本與 source commit 對齊，未處理的 OPEN item 已清空，有人類核准，且回滾條件與責任人完整時，才輸出 `READY_FOR_RELEASE`。

## 會檢查什麼

- release plan 的 `release_id`、版本、source commit、owner 與 dependencies 完整。
- 每個 dependency pack 都是 `READY_FOR_HANDOFF`，且版本與 source commit 對齊。
- artifact path 必須是相對路徑，不可含絕對路徑或 `..` 路徑穿越。
- 不可存在未處理的 OPEN item。
- release owner 必須提供 human approval；`agent` 不可自我核准發布。
- rollback 必須有 owner、觸發條件與可執行步驟。

## 執行

```bash
python3 -m unittest -v
python3 release_gate.py \
  --plan fixtures/plan.json \
  --packs fixtures/packs.json \
  --approvals fixtures/approvals.json \
  --rollback fixtures/rollback.json \
  --out RELEASE_GATE.md
```

成功輸出：

```text
Ran 7 tests ...
OK
RELEASE_GATE_READY id=release-v7 version=2026.08.10 dependencies=2 rollback_owner=oncall
```

若刪除 dependency、改變版本、留下 OPEN item、把 reviewer 改成 `agent`、移除 rollback trigger，或放入絕對路徑，命令會輸出 `RELEASE_GATE_BLOCKED` 並以非零狀態結束。

## 邊界

Release Gate 只證明「可以進入發布窗口」，不會上傳、部署、合併或對外發布；正式發布仍需依照產品的授權與外部驗證流程執行。
