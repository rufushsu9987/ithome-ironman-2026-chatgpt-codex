# Day 17｜Artifact 可以晉級，真的能安全發布嗎？用 Release Candidate Gate 鎖住最後一哩

## 本日定位

Day 16 的 Artifact Promotion Gate 已經確認 bundle 精確、完整，而且屬於同一個 run。但「artifact 可以晉級」仍不等於「現在可以安全發布」：發布還有 target、release window、rollback、smoke checks 與最後責任人。若少了其中一項，驗證器可能把一個看似完整的 bundle 推進不該進入的時間窗。

本日引入 Release Candidate Gate。它把已晉級的 artifact 綁回同一個 release candidate，檢查發布目標、時間窗、必要 checks、rollback bundle 與人類核准；只回報 candidate 是否具備進入發布決策的條件，不執行部署、不切換流量、不替 release owner 按下發布。

## 文章主線

1. 從「bundle 都 ready 了，為什麼還不能發布？」的生活情境開始。
2. 分開說明 Artifact Promotion 與 Release Candidate 的責任。
3. 固定 candidate、target、release window 與 approval owner。
4. 把 release bundle、manifest、rollback bundle 綁回同一個 run 與 source identity。
5. 用 required checks 擋住 skipped、pending 與未完成的 smoke／compatibility 檢查。
6. 用 rollback readiness 與 digest 比對，避免只有前進路徑、沒有退路。
7. 以唯讀、deterministic、fail-closed 的 Python Gate 示範 reason code。
8. 把 Day 10–17 串成從 Context 新鮮度到發布前決策的證據鏈。

## Given／When／Then 驗收條件

1. Given candidate 的 artifact 集合完整、狀態為 ready、digest 與 run identity 一致，And required checks 都是 `passed`，And release window 正在開放，And rollback bundle ready，And approval target／owner 正確，When 執行 Release Candidate Gate，Then 回報 `allowed=true`、`state=releasable`、`reasons=[]`。
2. Given candidate artifact 來自另一個 run，When 執行 Gate，Then 回報 `artifact_run_mismatch:<artifact>`，不可因檔名相同而放行。
3. Given expected artifact 缺少或 observed bundle 出現未知 artifact，When 執行 Gate，Then 回報 `artifact_missing:<id>` 或 `artifact_unknown:<id>`。
4. Given artifact 為 `pending`、`failed` 或 digest 不符，When 執行 Gate，Then fail-closed 並指出具體 artifact。
5. Given required check 為 `skipped`、`failed` 或缺少，When 執行 Gate，Then 回報 check reason；`skipped` 不得當成 passed。
6. Given現在時間早於或晚於 release window，When 執行 Gate，Then 回報 `release_window_not_open` 或 `release_window_expired`。
7. Given rollback bundle 缺少、尚未 ready 或 digest 不符，When 執行 Gate，Then 回報 rollback reason，不接受「發布後再準備」。
8. Given approval 的 target、owner 或 granted 狀態不符合 intent，When 執行 Gate，Then 回報 approval reason；Gate 不自行補填欄位。
9. Given intent 與 observation 的 source、input、environment 或 candidate identity 漂移，When 執行 Gate，Then fail-closed。
10. Given相同 intent 與 observation 重試兩次，When執行 Gate，Then兩次 JSON 報告一致且輸入物件沒有被修改。

## Runnable example

`example-release-candidate-gate/` 使用 Python 標準函式庫實作唯讀 `evaluate_release_candidate(intent, observed)`：

- 驗證 candidate identity、run、source、input 與 environment。
- 驗證 expected artifact 的 exact set、status、digest 與產出 run。
- 驗證 required checks、release window、rollback bundle 與 approval。
- 以 deterministic reason code 讓下一步可以直接定位缺口。
- 不複製檔案、不修改輸入、不部署、不發布。

## 圖解與影片場景

- `diagrams/release_candidate_gate_flow.mmd`：從 Artifact Promotion 通過後建立 candidate，到 release window、rollback、checks 與 approval 的流程。
- `diagrams/release_candidate_states.mmd`：DECLARED、CHECKING、WAITING_WINDOW、BLOCKED_ROLLBACK、BLOCKED_APPROVAL、RELEASABLE 與 RELEASED_BY_HUMAN 狀態。
- HTML deck 10 張：問題、promotion 不等於 release、candidate identity、release window、exact set、checks、rollback、approval、Day 10–17 證據鏈與收束。

## 媒體交付 gates

- Deck：官方 `claude-code-slides` 0.6.0、`claude-editorial`、HTML；1920×1080、10 slides、每頁 layout marker 與 speaker notes。
- TTS：Fish Audio per-scene MP3，實測 audio duration 產生 timing 與 SRT；不得 silent。
- Video：clean H.264/AAC MP4、1920×1080、25 fps，不燒字幕。
- QA：companion tests、fixture CLI、Python／JavaScript syntax checks、官方 deck checker、FFprobe、full video/audio decode、volume、SRT timing、10 張 midpoint contact sheet、final-MP4 full-resolution frame、視覺檢查與 strict Media QA 全部 PASS。
- 外部：YouTube／字幕／iThome／GitHub 維持待後續 Release lane；Producer 不執行任何外部發布。
