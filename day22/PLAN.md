# Day 22｜出問題要回滾，但誰來決定回滾到哪？用 Rollback Gate 把風險寫成可驗收的 evidence

## 本日定位

延續 Day 21 的 Human Approval Gate，Day 22 處理「發布或部署後真的異常」的場景。Rollback Gate 是一個唯讀判斷層，在 rollback 執行前驗證：rollback target 是否為 intent 宣告的 last known good、觸發 rollback 的 evidence 是否完整且與本次 run 綁定、stop-loss 條件是否明確，以及決策角色是否符合 policy。Gate 只輸出 rollback eligible 的 evidence，不自動rollback、不改流量、不改 serving state、不替 release owner 或 incident commander 做最終決定。

## 文章主線

1. 從「上線後付款失敗率上升，團隊本能想rollback」的生活情境開始。
2. 說明 deployed 與 safe to keep 的差異，以及 rollback 也是狀態改變。
3. 先固定 rollback intent identity，避免拿別的 run 或 candidate 的判斷來套用。
4. 要求 target candidate 必須是 last known good，並綁定 evidence digest。
5. 寫明 stop-loss 條件與 observation window，避免恐慌中rollback。
6. 把 trigger evidence 的完整性也放進 Gate。
7. 用 deterministic reason code 清楚表達阻擋原因。
8. 以標準函式庫 Python 範例產生唯讀、可重跑的 rollback 判斷。
9. 把 Day 10–22 串成從 context 新鮮度走到 rollback evidence 的證據鏈。

## Given／When／Then 驗收條件

1. Given intent 宣告 target candidate 為 last known good、兩位 release owner、10 分鐘 observation window，observation 綁定同一 run 且 evidence 完整，When 執行 Rollback Gate，Then 回報 `allowed=true`、`state=rollback_eligible`、`reasons=[]`。
2. Given source/target/run/environment identity 漂移，When 執行 Gate，Then 回報 `identity_mismatch:<field>`。
3. Given target candidate 不是 last known good，When 執行 Gate，Then 回報 `blocked_target`。
4. Given trigger evidence 缺少、state 不符或 digest 不一致，When 執行 Gate，Then 回報 `blocked_evidence:<name>`。
5. Given observation window 不足或 stop-loss 條件未明確觸發，When 執行 Gate，Then 回報 `blocked_stop_loss`。
6. Given requester 無權決定 rollback 或同一筆 change 已超過最大 rollback 次數，When 執行 Gate，Then 回報 `blocked_policy:<reason>`。
7. Given 相同 intent 與 observation 重試兩次，When 執行 Gate，Then 兩次 JSON 報告一致且輸入物件沒有被修改。
8. Given target candidate 等於目前 serving candidate，When 執行 Gate，Then 回報 `blocked_target:serving_candidate_equals_target`。
9. Given trigger evidence 顯示特定 tenant 超標而非全局超標，When 執行 Gate，Then 可回報 `rollback_eligible_with_scope` 並附加 scope 限制，不自動視為全量 rollback。

## Runnable example

`example-rollback-gate/` 使用 Python 標準函式庫實作唯讀 `evaluate_rollback(intent, observed)`：

- 比對 change identity。
- 比對 target candidate 的 last known good evidence。
- 驗證 trigger evidence 的完整性與 stop-loss 條件。
- 回傳 deterministic reason code，不執行 deployment、rollback、publish、權限或流量變更。

## 圖解與影片場景

- `diagrams/rollback_gate_flow.mmd`：從異常觸發到 rollback eligible 的流程圖。
- `diagrams/rollback_states.mmd`：DECLARED、EVIDENCE_BOUND、TARGET_VALID、STOP_LOSS_CHECKED、ROLLBACK_ELIGIBLE、BLOCKED_* 狀態圖。
- HTML deck 10 張：回滾風險、身份綁定、target candidate、evidence 完整性、stop-loss、reason code、唯讀範例、Day 10–22 證據鏈與收束。

## 媒體交付 gates

- Deck：先由官方 `claude-code-slides` 0.6.0、`claude-editorial`、HTML CLI scaffold，再填內容；1920×1080、10 slides、每頁 layout marker 與 speaker notes。
- TTS：Fish Audio per-scene MP3，實測 audio duration 產生 timing 與 SRT；不得 silent。
- Video：clean H.264/AAC MP4、1920×1080、25 fps，不燒字幕。
- QA：companion tests、fixture CLI、Python／JavaScript syntax checks、官方 deck checker、FFprobe、full video/audio decode、volume、SRT timing、10 張 midpoint contact sheet、final-MP4 full-resolution frame、視覺檢查與 strict Media QA 全部 PASS。
- 外部：YouTube／字幕／iThome／GitHub 維持待後續 Release lane；Producer 不執行任何外部發布。
