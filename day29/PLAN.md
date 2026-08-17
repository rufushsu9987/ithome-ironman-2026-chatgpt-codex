# Day 29｜Rollout Promotion Gate 題綱與交付計畫

## 本日定位

Day 28 用 Progressive Rollout Gate 確認同一輪 rollout 的 identity、canary、flag、rollback 與 health evidence 可以接起來。但 `pipeline_ready` 只代表「這一輪的前提完整」，還沒有回答下一個問題：現在能不能把流量從目前 cohort 推到下一個 cohort？

Day 29 引入 Rollout Promotion Gate，處理分段放量的決策邊界。它是唯讀的 promotion readiness check，不改 feature flag、不切 traffic、不執行 promotion，也不替 release owner 宣稱全面上線。

## 核心主張

Rollout Promotion Gate 只在同一份 promotion intent 下檢查四件事：

1. 觀察窗是否完整，樣本是否足夠。
2. 目前 cohort 的 error rate、p95 latency、saturation 是否都在門檻內。
3. 目標 cohort 與放量步幅是否符合政策，沒有跳過必要階段。
4. approval、handoff 與 idempotency evidence 是否能交給下一個責任邊界。

通過時輸出 `promotion_ready`；任一條件不成立則輸出固定 reason code，並停在 `blocked_promotion` 或 `blocked_identity`。

## Identity contract

- `release_id`
- `environment`
- `current_cohort`
- `target_cohort`
- `run_id`
- `promotion_id`
- `evidence_digest`
- `policy_version`

## Promotion contract

| Stage | State | 必要證據 |
| --- | --- | --- |
| observe | `window_complete` | window 秒數、sample count、same run、audit |
| metrics | `metrics_passed` | error rate、p95、saturation、digest、audit |
| policy | `step_allowed` | current／target cohort、step size、policy version |
| approval | `approval_bound` | owner、scope、promotion id、expiry、audit |
| handoff | `handoff_ready` | next owner、decision、idempotency key、audit |

固定順序：

```text
observe → metrics → policy → approval → handoff
```

## Runnable example QA

- 成功案例回傳 `allowed=true`、`state=promotion_ready`。
- identity 漂移先回傳 `blocked_identity`。
- observation window 不完整或 sample count 不足要阻擋。
- error rate、p95、saturation 任一超標要阻擋。
- current／target cohort 不一致、step size 跳太大或 target 不在 allowlist 要阻擋。
- approval scope、owner、expiry 缺失要阻擋。
- handoff owner、decision、idempotency key 缺失要阻擋。
- 相同 `promotion_id` 已執行時要回傳 `duplicate_promotion`，不能重複放量。
- 相同輸入重跑結果一致，且函式不 mutate input。

## Slide／scene mapping

| Scene | Layout marker | 核心畫面 | 旁白重點 |
| --- | --- | --- | --- |
| 1 | `editorial-cover` | 綠燈不等於可以全開 | 從 10% 放到 100% 的誤判切入 |
| 2 | `hero-statement` | promotion 與 execution 分離 | Gate 只回答能否交給下一關 |
| 3 | `before-after` | 看到一筆 metrics vs 完整觀察窗 | 單點漂亮數字不能代表穩定 |
| 4 | `layered-architecture` | identity、observation、policy、handoff | 先綁同一輪 evidence |
| 5 | `flow-architecture` | observe → metrics → policy → approval → handoff | 五段固定順序 |
| 6 | `metric-spotlight` | window、sample、error、p95 | 觀察條件要可驗收 |
| 7 | `evidence-claim` | cohort step policy | 目標 cohort 不能跳級 |
| 8 | `code-walkthrough` | Python CLI proof | deterministic、side-effect-free |
| 9 | `comparison-matrix` | Gate、owner、executor 的責任差異 | promotion_ready 不等於 traffic changed |
| 10 | `closing-manifesto` | 可交接的 promotion decision | verify → approve → handoff |

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

本輪只修改 Day 29 本機內容與產製檔案；不開 Chrome、不操作 iThome／YouTube／OAuth、不 commit／push／PR。Release lane 之後才處理外部發布。
