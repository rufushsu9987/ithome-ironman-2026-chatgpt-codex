# Day 19｜Deployment Verified 就穩定了嗎？用 Post-Deployment Stability Gate 觀察真實流量

## 本日定位

Day 18 的 Deployment Verification Gate 已經確認 deployment、rollout、replica、required checks 與 traffic 在某個觀察時點一致。但「這一刻看起來健康」仍不等於「服務在一段時間內穩定」。本日補上 Post-Deployment Stability Gate：唯讀檢查部署後觀察窗是否完整、樣本是否足夠、error rate／p95 latency／saturation 是否在門檻內，以及 traffic 是否持續服務同一個 candidate。

Gate 只回報 `post_deployment_stable` 或具體的 `blocked` reason；不調整 autoscaling、不切 traffic、不 rollback，也不替 release owner 宣稱發布成功。

## 文章主線

1. 從「剛驗證完成，但五分鐘後錯誤率開始升高」的情境開始。
2. 分開說明 Deployment Verification 與穩定性觀察的責任。
3. 固定 candidate、run、source、input、environment 與 target identity。
4. 要求完整 observation window 與足夠樣本，避免只挑一筆漂亮數字。
5. 將 error rate、p95 latency、saturation 變成可驗收的門檻。
6. 把 required checks 的 `skipped`、`pending`、`failed` 維持為 fail-closed。
7. 驗證 traffic 持續服務同一 candidate，避免驗證後 route 漂移。
8. 以唯讀、deterministic 的 Python Gate 示範 reason code。
9. 把 Day 10–19 串成從 context 新鮮度走到部署後穩定性的證據鏈。

## Given／When／Then 驗收條件

1. Given observation window 已完成且達到最短秒數，樣本數足夠，三項 metrics 都在門檻內，required checks 全為 `passed`，traffic 持續服務同一 candidate，When 執行 Stability Gate，Then 回報 `allowed=true`、`state=post_deployment_stable`、`reasons=[]`。
2. Given window 尚未完成或實際秒數不足，When 執行 Gate，Then 回報 `observation_window_incomplete` 或 `observation_window_too_short`。
3. Given樣本數少於 intent 宣告的數量，When執行 Gate，Then 回報 `sample_count_shortfall`。
4. Given error rate、p95 latency 或 saturation 超過門檻，When 執行 Gate，Then 回報對應的 `metric_*_exceeded` reason。
5. Given required check 缺少、結果為 `skipped`、`pending` 或 `failed`，When 執行 Gate，Then 回報 `check_missing:<name>` 或 `check_not_passed:<name>`。
6. Given traffic route 不在 `serving`，或實際 serving candidate 已漂移，When 執行 Gate，Then 回報 `traffic_not_serving` 或 `serving_candidate_mismatch`。
7. Given intent 與 observation 的 source、input、environment、run 或 target 漂移，When 執行 Gate，Then fail-closed。
8. Given相同 intent 與 observation 重試兩次，When執行 Gate，Then兩次 JSON 報告一致且輸入物件沒有被修改。

## Runnable example

`example-post-deployment-stability-gate/` 使用 Python 標準函式庫實作唯讀 `evaluate_stability(intent, observed)`：

- 比對 intent 與 observation 的 intent、run、candidate、source、input、environment 與 target。
- 驗證 observation window 是否完成、秒數與樣本數是否達標。
- 驗證 error rate、p95 latency 與 saturation 不超過各自門檻。
- 驗證 required checks 與 traffic serving identity。
- 回傳 deterministic reason code，不部署、不切流、不 rollback，也不修改輸入。

## 圖解與影片場景

- `diagrams/stability_gate_flow.mmd`：從 Deployment Verified 進入 observation window，再檢查樣本、metrics、checks 與 traffic。
- `diagrams/stability_gate_states.mmd`：DECLARED、OBSERVING、BLOCKED_WINDOW、BLOCKED_METRICS、BLOCKED_TRAFFIC、POST_DEPLOYMENT_STABLE 與 RELEASED_BY_HUMAN 狀態。
- HTML deck 10 張：問題、verification 與 stability 的差異、identity、window、metrics、checks、traffic、唯讀範例、Day 10–19 證據鏈與收束。

## 媒體交付 gates

- Deck：官方 `claude-code-slides` 0.6.0、`claude-editorial`、HTML；1920×1080、10 slides、每頁 layout marker 與 speaker notes。
- TTS：Fish Audio per-scene MP3，實測 audio duration 產生 timing 與 SRT；不得 silent。
- Video：clean H.264/AAC MP4、1920×1080、25 fps，不燒字幕。
- QA：companion tests、fixture CLI、Python／JavaScript syntax checks、官方 deck checker、FFprobe、full video/audio decode、volume、SRT timing、10 張 midpoint contact sheet、final-MP4 full-resolution frame、視覺檢查與 strict Media QA 全部 PASS。
- 外部：YouTube／字幕／iThome／GitHub 維持待後續 Release lane；Producer 不執行任何外部發布。
