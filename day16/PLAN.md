# Day 16｜重現成功就能直接交付嗎？用 Artifact Promotion Gate 擋住錯誤產物

## 本日定位

Day 15 的 Reproducibility Gate 已經確認同一組 source、input、環境與 dependency lock 可以重跑。但「能重跑」仍不等於「可以把產物送進下一個交付階段」：資料夾裡可能混著上一個 run 的檔案，某一份 artifact 可能沒有通過完整 QA，或有人把 Gate 的 `allowed=true` 誤當成發布指令。

本日引入 Artifact Promotion Gate。它把一組準備晉級的 artifact 綁回同一個 run，檢查輸出 identity、digest、狀態、必要 QA 與 promotion request；只回報是否具備晉級條件，不自動複製檔案、不發布、不替 release owner 做最後決策。

## 生活情境

昨天的訂單匯出 run 已經可重現，今天準備把 bundle 送到 release-candidate。工程師在輸出資料夾找到 `verification-report.json`，但它其實來自前一次測試；另一份 bundle 雖然是本次產出，卻只有單元測試通過，還沒有完成完整性與相容性檢查。若只看檔名或「測試全綠」，錯誤產物就可能被推進下一階段。

## 核心方法

- `Promotion Intent`：固定 `intent_id`、`run_id`、source、input、environment、expected artifacts、target 與 owner。
- `Artifact Identity`：每份 artifact 都要帶回 `artifact_digest`、`produced_by_run` 與相同的 source／input／environment。
- `Required Checks`：每個 artifact 宣告必要檢查；`passed` 以外的 `pending`、`failed`、`skipped` 都要阻擋。
- `Exact Set`：缺少 expected artifact 或出現未宣告 artifact 都 fail-closed，不從資料夾裡猜一份「看起來最像」的檔案。
- `Promotion Boundary`：Gate 只產生 `promotable` 或 `blocked` 報告，不執行 promotion、不改 digest、不代替人類發布。

## Given／When／Then 驗收條件

1. Given intent 宣告的 artifact 全部存在、ready、digest 與 identity 相同且必要 checks 都是 `passed`，When 執行 Promotion Gate，Then 回報 `allowed=true`、`state=promotable`，且 `reasons` 為空。
2. Given artifact 的 `produced_by_run` 不等於目前 run，When 執行 Gate，Then 回報 `artifact_run_mismatch:<artifact>`。
3. Given artifact 狀態為 `pending` 或 `failed`，When 執行 Gate，Then 回報 `artifact_not_ready:<artifact>`，不能只因其他檢查通過就放行。
4. Given 必要 check 為 `skipped`、`failed` 或缺少，When 執行 Gate，Then 回報具體的 check reason，不把未驗證當成通過。
5. Given observed bundle 少了 expected artifact 或多了未宣告 artifact，When 執行 Gate，Then 回報 `artifact_missing:<id>` 或 `artifact_unknown:<id>`。
6. Given artifact digest、source commit、input digest 或 environment 不一致，When 執行 Gate，Then fail-closed 並指出漂移的 artifact。
7. Given promotion request 的 target、owner 或 requested 狀態不符合 intent，When 執行 Gate，Then 回報 promotion reason；Gate 不自行補填或放寬欄位。
8. Given 相同 intent 與 observation 重試兩次，When 執行 Gate，Then 兩次報告一致且輸入物件沒有被修改。

## Runnable example

`example-artifact-promotion-gate/` 使用 Python 標準函式庫實作唯讀 `evaluate_promotion(intent, observed)`，輸出 deterministic JSON 報告。測試涵蓋完整 bundle、舊 run、pending artifact、QA skipped、缺少／未知 artifact、digest 漂移、identity 漂移、promotion request 不符與 read-only retry。

## 圖解與影片場景

- `diagrams/artifact_promotion_flow.mmd`：從 Reproducibility Gate 通過，到建立 promotion intent、逐份驗證 artifact，最後交給 release owner 的流程。
- `diagrams/artifact_promotion_states.mmd`：DECLARED、CHECKING、PROMOTABLE、BLOCKED_STALE、BLOCKED_QA、BLOCKED_SET 與 NEEDS_REPLAN 狀態。
- HTML deck 10 張：問題、reproducible 不等於 promotable、artifact identity、exact set、QA checks、Gate 輸出、責任邊界、Day 10–16 證據鏈與收束。

## 媒體交付 gates

- Deck：官方 `claude-code-slides` 0.6.0、`claude-editorial`、HTML；1920×1080、10 slides、每頁 layout marker 與 speaker notes。
- TTS：Fish Audio per-scene MP3，實測 audio duration 產生 timing 與 SRT；不得 silent。
- Video：clean H.264/AAC MP4、1920×1080、25 fps，不燒字幕。
- QA：companion tests、fixture CLI、Python／JavaScript syntax checks、官方 deck checker、FFprobe、full video/audio decode、volume、SRT timing、10 張 midpoint contact sheet、final-MP4 full-resolution frame、視覺檢查與 strict Media QA 全部 PASS。
- 外部：YouTube／字幕／iThome／GitHub 維持待後續 Release lane；Producer 不執行任何外部發布。
