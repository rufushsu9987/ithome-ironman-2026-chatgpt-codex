# Day 20｜Stability 通過，使用者真的沒受影響嗎？用 SLO Impact Gate 看真實可靠性

## 本日定位

Day 19 的 Post-Deployment Stability Gate 確認服務在一段 observation window 內持續健康，但「服務看起來穩定」還不等於「這次變更沒有傷害使用者」。本日把穩定性觀察再往使用者結果推進：以 SLO、error budget burn rate、p95 latency、availability 與 serving identity 建立 SLO Impact Gate。

Gate 是唯讀判斷層，只回答這次 candidate 是否有足夠證據顯示沒有超過使用者可靠性門檻；不改 SLO、不重寫 metrics、不切 traffic、不 rollback，也不替 release owner 宣告成功。

## 文章主線

1. 從「dashboard 綠了，但結帳請求變慢」的生活情境開始。
2. 分開說明 deployment verified、post-deployment stable 與 SLO impact clear 的責任。
3. 先固定 intent、run、candidate、source、input、environment 與 target。
4. 要求完整 observation window 與足夠樣本，避免只挑一筆漂亮請求。
5. 把 availability、p95 latency 與 error budget burn rate 寫成可驗收門檻。
6. 將 required checks 的 `skipped`、`pending`、`failed` 和缺欄位維持為 fail-closed。
7. 重新驗證 serving candidate 與 route state，避免證據和實際流量脫鉤。
8. 以標準函式庫 Python 範例產生 deterministic reason code。
9. 把 Day 10–20 串成從 Context 新鮮度走到使用者可靠性的證據鏈。

## Given／When／Then 驗收條件

1. Given observation window 已完成、時間與樣本達標，availability 不低於 SLO，p95 latency 與 burn rate 都在門檻內，required checks 全為 `passed`，traffic 持續服務同一 candidate，When 執行 SLO Impact Gate，Then 回報 `allowed=true`、`state=slo_impact_clear`、`reasons=[]`。
2. Given window 尚未完成或實際秒數不足，When 執行 Gate，Then 回報 `observation_window_incomplete` 或 `observation_window_too_short`。
3. Given 樣本數少於 intent 宣告的數量，When 執行 Gate，Then 回報 `sample_count_shortfall`。
4. Given availability 低於最低 SLO，When 執行 Gate，Then 回報 `metric_availability_below_target`。
5. Given p95 latency 或 error budget burn rate 超過門檻，When 執行 Gate，Then 回報對應的 `metric_*_exceeded` reason。
6. Given required check 缺少、結果為 `skipped`、`pending` 或 `failed`，When 執行 Gate，Then 回報 `check_missing:<name>` 或 `check_not_passed:<name>`。
7. Given traffic route 不在 `serving`，或實際 serving candidate 已漂移，When 執行 Gate，Then 回報 `traffic_not_serving` 或 `serving_candidate_mismatch`。
8. Given intent 與 observation 的 source、input、environment、run 或 target 漂移，When 執行 Gate，Then fail-closed。
9. Given 相同 intent 與 observation 重試兩次，When 執行 Gate，Then 兩次 JSON 報告一致且輸入物件沒有被修改。

## Runnable example

`example-slo-impact-gate/` 使用 Python 標準函式庫實作唯讀 `evaluate_impact(intent, observed)`：

- 比對 intent 與 observation 的 identity 欄位。
- 驗證 observation window 的完成狀態、持續時間與樣本數。
- 驗證 availability、p95 latency 與 error budget burn rate。
- 驗證 required checks 與 traffic serving identity。
- 回傳 deterministic reason code，不部署、不切流、不 rollback，也不修改輸入。

## 圖解與影片場景

- `diagrams/slo_impact_gate_flow.mmd`：從 Stability Verified 進入使用者影響判斷的流程圖。
- `diagrams/slo_impact_states.mmd`：DECLARED、OBSERVING、BLOCKED_SLO、BLOCKED_EVIDENCE、SLO_IMPACT_CLEAR 與 HUMAN_DECISION 狀態圖。
- HTML deck 10 張：問題、三層 Gate 的差異、identity、window、SLO 指標、error budget、唯讀範例、Day 10–20 證據鏈與收束。

## 媒體交付 gates

- Deck：官方 `claude-code-slides` 0.6.0、`claude-editorial`、HTML；1920×1080、10 slides、每頁 layout marker 與 speaker notes。
- TTS：Fish Audio per-scene MP3，實測 audio duration 產生 timing 與 SRT；不得 silent。
- Video：clean H.264/AAC MP4、1920×1080、25 fps，不燒字幕。
- QA：companion tests、fixture CLI、Python／JavaScript syntax checks、官方 deck checker、FFprobe、full video/audio decode、volume、SRT timing、10 張 midpoint contact sheet、final-MP4 full-resolution frame、視覺檢查與 strict Media QA 全部 PASS。
- 外部：YouTube／字幕／iThome／GitHub 維持待後續 Release lane；Producer 不執行任何外部發布。
