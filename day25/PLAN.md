# Day 25｜Incident 結案後就能刪證據嗎？用 Evidence Retention Gate 守住留存期限與回讀能力

## 本日定位

Day 24 的 Incident Closeout Gate 確認 recovery、impact、follow-up、learning 與 human closeout 都接得起來；今天再往後看證據生命週期。Incident 結案，不代表 evidence 可以立刻消失。Evidence Retention Gate 只讀取 inventory、digest、留存期限、legal hold 與 access scope，確認結案後的證據仍然能被辨識和回讀。

## 題綱與主線

1. 從「事故結案後，客戶與稽核還要追問」的情境開始。
2. 分開說明 `closeout_verified`、`retention_ready` 與 `human_retention_decision`。
3. 先固定 incident、closeout、run、environment 與 evidence digest。
4. 驗證 archive inventory 不是摘要，而是每份 evidence 都存在且可讀。
5. 用同一個 digest 綁住 recovery、impact、follow-up、learning 與 approval。
6. 以 `retain_until_epoch` 同時檢查現在是否過期，以及是否涵蓋最低 policy window。
7. 把 legal hold 與 access scope 做成明確的 fail-closed 條件。
8. 用標準函式庫 Python 範例輸出 deterministic reason code，不刪除、不移檔、不建立 hold。
9. 把 Day 10–25 的證據鏈延伸到「結案之後仍可證明」。
10. 以人類 retention decision 收束，保留 archive、delete 與 legal review 的責任邊界。

## Given／When／Then 驗收條件

1. Given intent 與 observation 的 incident、closeout、run、digest、environment、target 一致，inventory 已驗證、archive 完整，每份 required evidence 可讀且 storage state 有效，留存期限涵蓋現在與最低 policy window，legal hold 與 scope 正確，When 執行 Evidence Retention Gate，Then 回報 `allowed=true`、`state=retention_ready`、`reasons=[]`。
2. Given identity 任一欄位不同，When 執行 Gate，Then 先回報 `blocked_identity` 與欄位差異，不繼續套用其他事件的結果。
3. Given inventory 尚未驗證或 archive 尚未完成，When 執行 Gate，Then 回報 `retention_inventory_not_verified` 或 `retention_archive_incomplete`。
4. Given required evidence 缺少、不可讀或 storage state 為 `missing`／`unknown`，When 執行 Gate，Then 回報對應的 `evidence_missing:*`、`evidence_not_readable:*` 或 `evidence_storage_invalid:*`。
5. Given 任一 evidence 的 digest 與 intent 不一致，When 執行 Gate，Then 回報 `evidence_digest_mismatch:*`。
6. Given `retain_until_epoch` 已過期、未涵蓋最低 policy window、缺少 timestamp，When 執行 Gate，Then 回報 `evidence_retention_expired:*`、`evidence_retention_too_short:*` 或 timestamp reason。
7. Given `legal_hold_required=true` 但 hold 非 active，或 access scope 不精確相等，When 執行 Gate，Then 回報 `legal_hold_missing` 或 `access_scope_mismatch`。
8. Given 相同 intent 與 observation 重試兩次，When 執行 Gate，Then 兩次 JSON 報告一致，且輸入物件不被修改。

## Runnable example

`example-evidence-retention-gate/` 使用 Python 標準函式庫實作唯讀 `evaluate_retention(intent, observed)`：

- 比對 incident／closeout／run／digest／environment／target identity。
- 驗證 inventory、archive、readability、storage state 與 required evidence。
- 驗證每份 evidence 的 digest、建立時間與留存截止時間。
- 驗證 legal hold 與 incident-scoped access。
- 回傳 deterministic reason code，不刪除、不移動、不建立 hold，也不呼叫任何外部 API。

## 圖解與影片場景

- `diagrams/evidence_retention_gate_flow.mmd`：從 closeout 到 retention ready 與 human retention decision 的流程圖。
- `diagrams/evidence_retention_states.mmd`：Inventory、Evidence、Retention 與 Human Decision 狀態圖。
- HTML deck 10 張：結案後的證據問題、三個狀態、identity、inventory、digest、retention window、legal hold、唯讀範例、Day 10–25 證據鏈與收束。

## 媒體交付 gates

- Deck：先由官方 `claude-code-slides` 0.6.0、`claude-editorial`、HTML CLI scaffold，再填內容；1920×1080、10 slides、每頁 layout marker 與 speaker notes。
- TTS：Fish Audio per-scene MP3，使用實測 audio duration 產生 timing 與 SRT；不得 silent。
- Video：clean H.264/AAC MP4、1920×1080、25 fps，不燒字幕。
- QA：companion tests、fixture／CLI、Python／JavaScript syntax checks、官方 deck checker、FFprobe、full video/audio decode、volume、SRT timing、10 張 midpoint contact sheet、final-MP4 full-resolution frame、視覺檢查與 strict Media QA 全部 PASS。
- 外部：YouTube／字幕／iThome／GitHub 維持待後續 Release lane；Producer 不執行任何外部發布。
