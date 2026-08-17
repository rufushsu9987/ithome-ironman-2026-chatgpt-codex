# Day 27｜Lifecycle Gate 題綱與交付計畫

## 本日定位

Day 24–26 已經分別處理 Incident Closeout、Evidence Retention 與 Evidence Access。Day 27 不再新增一個會讀資料或發權限的服務，而是把三道既有 Gate 接成一個唯讀的 Lifecycle Gate，驗證它們是否描述同一條 evidence pipeline。

## 讀者痛點

每個 stage 都顯示通過，不代表 stage 之間綁的是同一個 incident、run 或 evidence digest。若只把三個布林值串在一起，可能把另一個事件的 retention 或 approval 誤當成目前 pipeline 的證據。

## 核心承諾

完成本日後，讀者可以用固定的 identity、stage 順序、state、digest、readback、approval 與 audit 條件，判斷 pipeline 是否為 `pipeline_ready`；遇到任何漂移則輸出可測試的 reason code 並 fail-closed。

## Canonical source

- `article.md`：本日文章與驗收條件。
- `example-evidence-lifecycle-gate/`：Python 標準函式庫、fixtures 與 10 項測試。
- `diagrams/evidence_lifecycle_gate_flow.mmd`：三道 Gate 的流程圖。
- `diagrams/evidence_lifecycle_states.mmd`：`pipeline_ready`／`blocked_pipeline` 狀態圖。
- `NARRATION.md`：10 個 Fish TTS scene，與 10 張 HTML slide 一一對應。
- `../ithome-promo-runs/day27/deck/`：官方 scaffold 產生後填入內容的 canonical HTML deck。

## Lifecycle contract

Identity 欄位：`incident_id`、`closeout_id`、`run_id`、`evidence_digest`、`environment_id`、`target`。

Stage 順序：`closeout → retention → access`。

Stage 成功狀態：

- `closeout` → `closed`
- `retention` → `retention_ready`
- `access` → `access_eligible`

每個 stage 還必須符合：

- `evidence_digest` 與 intent 一致。
- `audit_event_id` 存在。
- retention 的 `readback_passed` 為 `true`。
- access 的 `approval_bound` 為 `true`。

## Slide／scene mapping

| Scene | Layout marker | 核心畫面 | 旁白重點 |
| --- | --- | --- | --- |
| 1 | `editorial-cover` | 三道局部綠燈，整條鏈仍可能斷 | 從常見事故情境切入 |
| 2 | `hero-statement` | 三個不同責任狀態 | retention、access、grant 不可混成一個狀態 |
| 3 | `before-after` | 三個布林值 vs 同一條證據鏈 | 局部通過不代表 pipeline ready |
| 4 | `layered-architecture` | identity、digest、audit 四層 | 先固定 evidence identity |
| 5 | `flow-architecture` | Closeout → Retention → Access | 明確順序與責任邊界 |
| 6 | `evidence-claim` | 每個 stage 的 digest/readback/approval | 綠燈必須屬於同一份 evidence |
| 7 | `code-walkthrough` | runnable CLI 的 JSON 結果 | deterministic、side-effect-free |
| 8 | `risk-matrix` | identity、stage、digest、audit 的阻擋原因 | fail-closed 與 reason code |
| 9 | `timeline` | observe → compare → report → handoff | `pipeline_ready` 不等於已授權 |
| 10 | `closing-manifesto` | 四個交接動作 | retain → bind → verify → authorize |

## Runnable example QA

最小測試條件：

- 成功案例回傳 `allowed=true`、`state=pipeline_ready`。
- identity 漂移先回傳 `blocked_identity`。
- 缺 stage、未知 stage、順序錯誤都要阻擋。
- stage state、digest、audit event 都要逐段驗證。
- retention readback 與 access approval 缺失要阻擋。
- 相同輸入重跑結果一致，且函式不 mutate input。

## Media QA gates

- 官方 `claude-code-slides` 0.6.0 CLI 先建立 HTML scaffold；canonical deck 只在 scaffold 基礎上填內容。
- `node /Users/hsu/Projects/claude-code-slides-source/bin/codex-slides.mjs check <deck-dir> --json` 必須 exit 0，`errors=[]`、`warnings=[]`，10 slides／10 notes／10 unique layouts。
- 每頁在 1920×1080、`render=video` 模式逐頁 capture；notes 與 deck chrome 隱藏。
- 每個 scene 使用 Fish Audio TTS，音訊需非空、可由 FFprobe 測得 duration，最後合成 H.264/AAC、1920×1080、固定 25fps MP4。
- 產生獨立 UTF-8 SRT；每個 cue 一行、寬度不超過 42 display units、時間單調且落在 MP4 duration 內。
- 執行 FFprobe、video/audio full decode、volume check、10 張 midpoint contact sheet、至少一張 final MP4 full-resolution frame。
- 先產生 `PENDING_VISUAL_REVIEW`，由獨立視覺檢查後再以 finalizer 轉成 `PASS`。

## 外部邊界

本輪只修改 Day 27 本機內容與產製檔案；不開 Chrome、不操作 iThome／YouTube／OAuth、不 commit／push／PR。Release lane 之後才處理外部發布。
