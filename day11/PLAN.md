# Day 11｜Freshness Gate 通過就能一路改下去嗎？用 Change Budget 擋住範圍膨脹

## 題綱與定位

Day 10 已經在執行前檢查 Context 的身分、source commit、有效期限、Learning 證據與 scope。下一個缺口不是「前提是否新鮮」，而是「執行開始後，變更是否仍然是原本核准的那一件事」。本日引入 Change Budget：把允許的路徑、命令、檔案數與 diff 行數寫成可重跑的變更意圖，讓 agent 在執行中超出邊界時停止，交回人類重新規劃。

## 生活情境與痛點

一開始只要求修改 `services/export/**` 的匯出 API，agent 途中發現測試不方便，順手改了 billing、CI workflow 與共用設定。每個修改單獨看似合理，但最後已經不是原本核准的變更。Freshness Gate 只能證明使用的 Context 沒過期，不能證明實際 diff 沒有膨脹。

## 核心方法

- `Change Intent`：固定 intent_id、context_id、source_commit、acceptance_ids 與允許的路徑。
- `Change Budget`：限制 max_files_changed、max_diff_lines、max_commands，並使用 command allowlist。
- `Runtime Observation`：由外部 runner 提供目前變更報告；Gate 只讀取，不執行命令、不修改 git。
- `fail-closed`：任一路徑、命令或數量超過預算，回報穩定 reason code，狀態為 `blocked`。
- `replan`：預算不夠不是讓 agent 自己放寬，而是重新建立 intent，重新經過 Freshness 與人類確認。

## Given／When／Then 驗收條件

1. Given 變更路徑、source commit、命令與數量都符合 intent，When 執行 Budget Gate，Then 回報 `allowed=true`、`state=allowed`，且 reasons 為空。
2. Given 任一路徑不在 allowlist 或落入 forbidden path，When 執行 Gate，Then 回報 `allowed=false` 並指出具體 path。
3. Given changed files 或 diff lines 超過上限，When 執行 Gate，Then 回報 `max_files_changed_exceeded` 或 `max_diff_lines_exceeded`，不能自動增加上限。
4. Given runner 回報未列入 allowlist 的 command，When 執行 Gate，Then 回報 `command_not_allowed:<command>`。
5. Given context_id 或 source_commit 不一致，When 執行 Gate，Then fail-closed，不把「看起來相近」當成相同變更。
6. Given 相同 intent 與 observation 重試兩次，When 執行 Gate，Then 報告相同，輸入物件不被修改。

## 可執行範例

`example-change-budget/` 使用 Python 標準函式庫實作唯讀 `evaluate_budget(intent, observed)`，輸出 deterministic JSON 報告。測試涵蓋放行、path 越界、forbidden path、檔案數、diff 行數、command allowlist／數量、Context／commit mismatch 與 read-only retry。

## 圖解與影片場景

- `diagrams/change_budget_flow.mmd`：Freshness 通過後建立 intent、執行、觀測、超出預算時阻擋的流程。
- `diagrams/change_budget_states.mmd`：PLANNED、RUNNING、BLOCKED_BUDGET、NEEDS_REPLAN、READY_VERIFY 狀態。
- HTML deck 8 張：問題、Change Intent、四層 Budget、執行中觀測、reason code、測試證據、責任鏈收束。

## 媒體交付 gates

- Deck：1920×1080 HTML、8 slides、8 組 speaker notes、notes 不出現在畫面。
- TTS：Fish Audio per-scene MP3，實際 audio duration 產生 timing 與 SRT。
- Video：clean H.264/AAC MP4、1920×1080、25 fps，不燒字幕。
- QA：companion tests、py_compile、Node syntax、strict deck check、FFprobe、full video/audio decode、volume、SRT bounds、8 張 midpoint contact sheet、full-resolution frame、Media QA manifest 全部 PASS。
- 外部：YouTube／字幕／iThome／GitHub 均維持待每日 Release lane，Producer 不執行任何外部發布。
