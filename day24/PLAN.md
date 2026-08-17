# Day 24｜恢復驗證通過就能結案嗎？用 Incident Closeout Gate 把復原、學習與追蹤責任綁起來

## 本日定位

Day 23 的 Recovery Verification Gate 確認 rollback 後服務真的回到 target candidate、traffic、metrics 與 required checks 都符合門檻。但 recovery verified 仍不等於 incident 可以直接關閉：customer impact 可能還在收尾、postmortem 尚未完成、追蹤工作沒有 owner，或 learning pack 還沒有綁回原事件。

本日加入 Incident Closeout Gate。它只讀取 recovery evidence、incident observation、follow-up register、learning pack 與 closeout approval，確認恢復、影響範圍、後續責任與學習資料都綁在同一個 incident identity 上。Gate 不關閉 incident、不修改 ticket、不建立任務，也不替人類做最後結案決定。

## 文章主線

1. 從「服務恢復了，但下週同一個問題又發生」的情境開始。
2. 分開說明 recovery verified、closeout eligible 與 human closeout 的責任。
3. 先固定 incident、recovery、run、candidate、environment 與 target identity。
4. 驗證 recovery state 與 customer-impact window，避免只看到版本回去了。
5. 要求所有 critical follow-up 都有 owner、期限與可讀的狀態。
6. 把 postmortem、learning pack 與 evidence digest 綁回同一個事件。
7. 驗證 closeout owner 的核准 scope，不把另一個 incident 的核准套過來。
8. 用標準函式庫 Python 範例產生 deterministic reason code。
9. 把「可以結案」和「已經結案」分成兩個狀態。
10. 串起 Day 10–24：從新鮮 Context 走到恢復後仍可學習、可追蹤的責任鏈。

## Given／When／Then 驗收條件

1. Given recovery state 為 `recovery_verified`、customer-impact window 已完成、identity 全部一致、所有 critical follow-up 都有 owner／due time 且狀態為 `completed` 或 `accepted`，postmortem 與 learning pack 都綁定同一個 evidence digest，closeout owner 以正確 scope 核准，When 執行 Incident Closeout Gate，Then 回報 `allowed=true`、`state=closeout_eligible`、`reasons=[]`。
2. Given incident、recovery、run、candidate、source、input、environment 或 target 任一欄位漂移，When 執行 Gate，Then 回報 `blocked_identity` 與對應差異。
3. Given recovery state 不是 `recovery_verified`，When 執行 Gate，Then 回報 `recovery_not_verified`。
4. Given customer-impact window 尚未完成、秒數不足或樣本數不足，When 執行 Gate，Then 回報 `impact_window_incomplete`、`impact_window_too_short` 或 `impact_sample_count_shortfall`。
5. Given critical follow-up 缺少、沒有 owner、沒有期限、過期或狀態為 `pending`／`skipped`，When 執行 Gate，Then 回報具體的 `followup_*` reason。
6. Given postmortem 缺少或 incident／digest 不一致，When 執行 Gate，Then 回報 `postmortem_missing`、`postmortem_identity_mismatch` 或 `postmortem_digest_mismatch`。
7. Given learning pack 缺少、狀態不是 `ready`，或沒有綁回 incident 與 evidence digest，When 執行 Gate，Then fail-closed 並輸出對應 reason。
8. Given closeout approval 缺少、decision 不是 `approved`、role 不符、scope 不符或超過有效期限，When 執行 Gate，Then 回報對應的 `closeout_approval_*` reason。
9. Given 相同 intent 與 observation 重試兩次，When 執行 Gate，Then 兩次 JSON 報告一致，且輸入物件沒有被修改。

## Runnable example

`example-incident-closeout-gate/` 使用 Python 標準函式庫實作唯讀 `evaluate_closeout(intent, observed)`：

- 比對 incident 與 recovery identity。
- 驗證 recovery state、customer-impact window 與 sample count。
- 驗證 critical follow-up 的 owner、期限與完成狀態。
- 驗證 postmortem、learning pack 與 evidence digest 的關聯。
- 驗證 closeout approval 的 role、scope、decision 與有效期限。
- 回傳 deterministic reason code，不關閉 incident、不改 ticket、不建立任務。

## 圖解與影片場景

- `diagrams/incident_closeout_gate_flow.mmd`：從 recovery verified 到 human closeout 的流程圖。
- `diagrams/incident_closeout_states.mmd`：RECOVERY_VERIFIED、IMPACT_REVIEW、FOLLOWUP_BLOCKED、CLOSEOUT_ELIGIBLE 與 HUMAN_CLOSEOUT 狀態圖。
- HTML deck 10 張：恢復不等於結案、三種狀態、identity、影響窗口、follow-up、postmortem／learning、唯讀 CLI、reason code、Day 10–24 證據鏈與收束。

## 媒體交付 gates

- Deck：先由官方 `claude-code-slides` 0.6.0、`claude-editorial`、HTML CLI scaffold，再填內容；1920×1080、10 slides、每頁 layout marker 與 speaker notes。
- TTS：Fish Audio per-scene MP3，使用實測 audio duration 產生 timing 與 SRT；不得 silent。
- Video：clean H.264/AAC MP4、1920×1080、25 fps，不燒字幕。
- QA：companion tests、fixture CLI、Python／JavaScript syntax checks、官方 deck checker、FFprobe、full video/audio decode、volume、SRT timing、10 張 midpoint contact sheet、final-MP4 full-resolution frame、視覺檢查與 strict Media QA 全部 PASS。
- 外部：YouTube／字幕／iThome／GitHub 維持待後續 Release lane；Producer 不執行任何外部發布。
