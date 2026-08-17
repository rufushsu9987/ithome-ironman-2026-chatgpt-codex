# Day 23｜回滾成功就算恢復了嗎？用 Recovery Verification Gate 確認系統真的回到安全狀態

## 本日定位

Day 22 的 Rollback Gate 確認「是否有足夠 evidence 支持回滾，以及 target candidate 是否是 last known good」。但 rollback command 回傳成功，不等於服務已經恢復：traffic 可能還沒切回、資料修復可能未完成，或錯誤率只是暫時下降。

本日加入 Recovery Verification Gate。它只讀取 rollback intent、執行結果與 recovery observation，確認系統是否真的回到宣告的 target candidate、完成足夠 observation window、指標回到門檻內、required checks 全部通過，而且 evidence digest 沒有漂移。

## 文章主線

1. 從「回滾成功，但使用者還是刷不過卡」的情境開始。
2. 分開說明 rollback executed、service recovered 與 human closeout 的責任。
3. 先固定 rollback identity，避免把另一個 incident 的恢復結果套進來。
4. 驗證 rollback execution result，確認實際套用的 target candidate。
5. 要求 recovery observation window、樣本數與指標門檻都達標。
6. 將 health、traffic、data integrity 等 required checks 的缺口維持為 fail-closed。
7. 重新讀回 serving candidate 與 route state，避免「版本回去了，流量沒回去」。
8. 以 recovery evidence digest 把觀察結果綁回這次 rollback。
9. 用標準函式庫 Python 範例產生 deterministic reason code，不呼叫任何修復 API。
10. 把 Day 10–23 串成從新鮮 Context、變更與發布，走到 rollback 後恢復驗證的證據鏈。

## Given／When／Then 驗收條件

1. Given rollback 已完成、實際套用 target candidate、recovery window 完成且時間與樣本達標，availability、p95 latency、error rate 與 queue depth 都在門檻內，required checks 全為 `passed`，traffic 正在服務 target candidate，When 執行 Recovery Verification Gate，Then 回報 `allowed=true`、`state=recovery_verified`、`reasons=[]`。
2. Given intent 與 observation 的 rollback、run、candidate、source、input、environment 或 target 不同，When 執行 Gate，Then 回報 `blocked_identity` 與欄位差異。
3. Given rollback result 不是 `completed`，When 執行 Gate，Then 回報 `rollback_not_completed`。
4. Given 實際套用的 candidate 不是 intent 宣告的 target，When 執行 Gate，Then 回報 `rollback_target_mismatch`。
5. Given recovery window 尚未完成、秒數不足或樣本數不足，When 執行 Gate，Then 回報 `recovery_window_incomplete`、`recovery_window_too_short` 或 `recovery_sample_count_shortfall`。
6. Given availability 低於最低值，或 p95 latency、error rate、queue depth 超過上限，When 執行 Gate，Then 回報對應的 `recovery_metric_*` reason。
7. Given required check 缺少、結果為 `pending`、`skipped` 或 `failed`，When 執行 Gate，Then 回報 `recovery_check_missing:<name>` 或 `recovery_check_not_passed:<name>`。
8. Given traffic 不在 `serving`，或 serving candidate 不是 target，When 執行 Gate，Then 回報 `recovery_traffic_not_serving` 或 `recovery_serving_candidate_mismatch`。
9. Given recovery evidence 缺少，或 name／digest 與 intent 不一致，When 執行 Gate，Then fail-closed 並輸出 `recovery_evidence_missing` 或 `recovery_evidence_digest_mismatch`。
10. Given 相同 intent 與 observation 重試兩次，When 執行 Gate，Then 兩次 JSON 報告一致，且輸入物件不被修改。

## Runnable example

`example-recovery-verification-gate/` 使用 Python 標準函式庫實作唯讀 `evaluate_recovery(intent, observed)`：

- 比對 rollback identity。
- 驗證 rollback 執行結果與實際 target candidate。
- 驗證 recovery window、樣本數與四項 recovery metrics。
- 驗證 required checks、traffic serving identity 與 evidence digest。
- 回傳 deterministic reason code，不切流、不修資料、不重跑 deployment、不自動關閉 incident。

## 圖解與影片場景

- `diagrams/recovery_verification_gate_flow.mmd`：從 rollback executed 到恢復驗證與人工 closeout 的流程圖。
- `diagrams/recovery_verification_states.mmd`：EXECUTED、OBSERVING、BLOCKED_RECOVERY、RECOVERY_VERIFIED 與 HUMAN_CLOSEOUT 狀態圖。
- HTML deck 10 張：回滾成功的錯覺、三種狀態差異、identity、execution result、observation window、metrics、required checks、唯讀範例、Day 10–23 證據鏈與收束。

## 媒體交付 gates

- Deck：先由官方 `claude-code-slides` 0.6.0、`claude-editorial`、HTML CLI scaffold，再填內容；1920×1080、10 slides、每頁 layout marker 與 speaker notes。
- TTS：Fish Audio per-scene MP3，使用實測 audio duration 產生 timing 與 SRT；不得 silent。
- Video：clean H.264/AAC MP4、1920×1080、25 fps，不燒字幕。
- QA：companion tests、fixture CLI、Python／JavaScript syntax checks、官方 deck checker、FFprobe、full video/audio decode、volume、SRT timing、10 張 midpoint contact sheet、final-MP4 full-resolution frame、視覺檢查與 strict Media QA 全部 PASS。
- 外部：YouTube／字幕／iThome／GitHub 維持待後續 Release lane；Producer 不執行任何外部發布。
