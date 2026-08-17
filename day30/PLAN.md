# Day 30｜Delivery Contract 題綱與交付計畫

## 本日定位

前 29 天把 AI 工程工作流從需求、Context、執行、Verify、Review、Release，一路延伸到 rollout、incident、evidence 與 promotion。最後一個常見缺口是：每個局部檢查都通過，卻沒有人能回答「這一包交付物是否真的能被下一個責任邊界接手」。

Day 30 用 Delivery Contract Gate 收束整條系列。它是唯讀的交付 readiness check，不發布文章、不上傳影片、不改 production；它只把同一輪 run 的 stage evidence、交付物 inventory、QA 結果與 handoff 綁在一起。

## 核心主張

`delivery_ready` 不是「已經公開」，而是：

1. Context、Plan、Execute、Verify、Review、Deliver 依正確順序完成。
2. 每個 stage 都屬於同一份 contract identity、run 與 evidence digest。
3. article、example、deck、video、subtitles、media QA 都有可回讀的證據。
4. 外部發布仍停在 release lane，不能被本機 Producer 偷換成已發布。
5. 下一個 owner 收到明確的 decision、scope 與 idempotency key。

## Identity contract

- `series_id`
- `day`
- `contract_id`
- `run_id`
- `source_digest`
- `evidence_digest`
- `policy_version`
- `owner`
- `target`

## Stage contract

| Stage | State | 必要證據 |
| --- | --- | --- |
| context | `context_bound` | source digest、run、audit |
| plan | `plan_approved` | scope、acceptance、audit |
| execute | `executed_scoped` | changed scope、run、audit |
| verify | `verified` | tests、syntax、media QA、digest、audit |
| review | `review_complete` | reviewer、decision、audit |
| deliver | `deliverable_bound` | inventory、owner、audit |

固定順序：

```text
context → plan → execute → verify → review → deliver
```

## Runnable example QA

- 成功案例回傳 `allowed=true`、`state=delivery_ready`。
- identity 漂移先回傳 `blocked_identity`。
- 缺少、未知或順序錯誤的 stage 要 fail closed。
- stage state、digest、audit event 都要逐段驗證。
- 必要交付物缺少、狀態不是 `verified`、bytes 為 0 或路徑是絕對路徑都要阻擋。
- external boundary 不可從 `release_lane` 偷換成已發布。
- handoff 欄位不足或 idempotency key 不一致要阻擋。
- 相同 `contract_id` 已執行時要回報 `duplicate_delivery`。
- 相同輸入重跑結果一致，且函式不 mutate input。

## Slide／scene mapping

| Scene | Layout marker | 核心畫面 | 旁白重點 |
| --- | --- | --- | --- |
| 1 | `editorial-cover` | 30 天最後一關不是按發布 | 從「都綠了，能不能交付」切入 |
| 2 | `hero-statement` | delivery ready 與 published 分離 | readiness 不是外部結果 |
| 3 | `before-after` | 六個局部綠燈 vs 一份 contract | 需要同一份 identity |
| 4 | `layered-architecture` | identity、stage、artifact、handoff | 交付契約的四層證據 |
| 5 | `flow-architecture` | context → plan → execute → verify → review → deliver | 順序是契約 |
| 6 | `metric-spotlight` | artifact inventory 與 QA | 有檔案不等於有證據 |
| 7 | `evidence-claim` | release lane 邊界 | 本機 ready 不偷換成 public |
| 8 | `code-walkthrough` | Python CLI proof | deterministic、side-effect-free |
| 9 | `comparison-matrix` | Producer、Reviewer、Release owner | 責任交接清楚 |
| 10 | `closing-manifesto` | 30 天閉環 | context → verify → deliver → handoff |

## Media QA contract

- 官方 `claude-code-slides` 0.6.0 CLI 先建立 HTML scaffold；canonical deck 只在 scaffold 基礎上填內容。
- 官方 checker 必須 exit 0，`errors=[]`、`warnings=[]`，10 slides／10 notes／10 unique layouts。
- 每頁在 1920×1080、`render=video` 模式逐頁 capture；notes 與 deck chrome 隱藏。
- 每個 scene 使用 Fish Audio TTS，音訊需非空且 duration 可由 FFprobe 測量。
- 最終為 H.264/AAC、1920×1080、固定 25fps clean MP4。
- 產生獨立 UTF-8 SRT；每個 cue 恰好一個 physical text line，最大 42 display units，時間單調且落在 MP4 duration 內。
- 執行 FFprobe、video/audio full decode、volume check、10 張 midpoint contact sheet、至少一張 final MP4 full-resolution frame。
- deterministic builder 先產生 `PENDING_VISUAL_REVIEW`；獨立視覺檢查後才由 finalizer 轉成 `PASS`。

## 外部邊界

本輪只修改 Day 30 本機內容與產製檔案；不開 Chrome、不操作 iThome／YouTube／OAuth、不 commit／push／PR。Release lane 之後才處理外部發布。
