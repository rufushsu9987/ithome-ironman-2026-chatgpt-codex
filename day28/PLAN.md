# Day 28｜Progressive Rollout Gate 題綱與交付計畫

## 本日定位

Day 27 把 Incident Closeout、Evidence Retention 與 Evidence Access 接成一條可稽核的 Lifecycle Pipeline。Day 28 往前一步，處理另一個常見情境：新版本不是部署成功就結束，而是要分段放量；每一段都必須知道自己觀察的是哪一輪 rollout。

## 核心主張

Progressive Rollout Gate 是唯讀的 readiness check。它不部署、不改 feature flag、不執行 rollback，只驗證同一份 rollout intent 下的 identity、canary、flag、rollback 與 health evidence 是否完整、依序、可回讀、可稽核。

## Identity contract

- `release_id`
- `environment`
- `cohort`
- `flag_key`
- `run_id`
- `evidence_digest`

## Stage contract

| Stage | State | 必要證據 |
| --- | --- | --- |
| identity | `identity_bound` | identity 與 intent 一致、audit event |
| canary | `canary_passed` | p95、error rate、cohort match、digest、audit |
| flag | `flag_bound` | key、mapping、kill switch、digest、audit |
| rollback | `rollback_ready` | target、trigger、timeout、digest、audit |
| health | `health_passed` | same run、readback match、digest、audit |

固定順序：

```text
identity → canary → flag → rollback → health
```

## Runnable example QA

- 成功案例回傳 `allowed=true`、`state=pipeline_ready`。
- identity 漂移先回傳 `blocked_identity`。
- 缺少或未知 stage 要 fail closed。
- stage order 錯誤要回傳固定 reason code。
- 每個 stage 的 state、digest、audit event 都要檢查。
- canary p95／error rate 超標要阻擋。
- flag key、mapping、kill switch 不一致要阻擋。
- rollback target、trigger、timeout 不完整要阻擋。
- health readback 或 run 不一致要阻擋。
- 相同輸入重跑結果一致，且函式不 mutate input。

## Slide／scene mapping

| Scene | Layout marker | 核心畫面 | 旁白重點 |
| --- | --- | --- | --- |
| 1 | `editorial-cover` | rollout 不是一次推完 | 從看似成功的上線情境切入 |
| 2 | `hero-statement` | 三個常見誤判 | canary、flag、rollback 可能不是同一輪 |
| 3 | `process-steps` | 五段闖關流程 | identity → canary → flag → rollback → health |
| 4 | `layered-architecture` | rollout identity 層次 | 先固定 release、環境、cohort 與 run |
| 5 | `metric-spotlight` | canary 指標 | p95、error rate、cohort、readback 一起看 |
| 6 | `evidence-claim` | flag mapping | key、group、owner 要屬於同一份 intent |
| 7 | `flow-architecture` | rollback contract | target、trigger、timeout 明確化 |
| 8 | `comparison-matrix` | health readback | same run、same intent、same cohort |
| 9 | `code-walkthrough` | Python CLI proof | deterministic、side-effect-free |
| 10 | `closing-manifesto` | handoff decision | pipeline ready 不等於全面上線 |

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

本輪只修改 Day 28 本機內容與產製檔案；不開 Chrome、不操作 iThome／YouTube／OAuth、不 commit／push／PR。Release lane 之後才處理外部發布。
