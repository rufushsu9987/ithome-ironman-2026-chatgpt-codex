# Day 13 製作計畫

## 暫定標題

Day 13｜測試都通過，怎麼知道需求沒有漏掉？用 Acceptance Coverage 補齊驗收證據

## 題綱與定位

Day 12 的 Evidence Binding 已經確認 diff、tests、review 屬於同一個 intent、context、source commit 與 observation。但「證據接對」仍不等於「每個需求都有被證明」。一份整體測試可能是綠色，卻漏掉一個 Given／When／Then；一個 review 也可能只看過部分 acceptance。Day 13 引入 Acceptance Coverage，逐項檢查宣告的 acceptance ids 是否都有通過結果、可追溯 evidence 與正確 identity。

## 生活情境與痛點

團隊說「測試全綠，可以交付」，但需求其實有 AC-01 到 AC-03 三個條件。測試報告只證明 AC-01，review 只提到 AC-02，AC-03 沒有人負責也沒有證據。測試數量與通過狀態看起來漂亮，需求覆蓋卻是不完整的。

## 核心方法

- `Acceptance IDs`：在 intent 中先列出本次工作的驗收條件，不用測試名稱猜需求。
- `Coverage Result`：每個 acceptance 都要有 `status=passed` 與一個或多個 evidence ids。
- `Reverse Link`：artifact 也要反向列出它證明哪些 acceptance，避免只在結果端填一個漂亮連結。
- `Identity Check`：沿用 Day 12，intent、context、source commit 不一致就阻擋。
- `fail-closed`：缺少 acceptance、失敗、未知 acceptance、未綁定 evidence 或重複 evidence id，都不能進 Verify。
- `read-only`：Gate 只產生 deterministic report，不修改 intent、evidence 或測試結果。

## Given／When／Then 驗收條件

1. Given 每個宣告的 acceptance 都有 `status=passed` 與正確 evidence，When 執行 Coverage Gate，Then 回報 `allowed=true`、`state=covered`。
2. Given 少了任一 acceptance result，When 執行 Gate，Then 回報 `acceptance_missing:<id>`。
3. Given 某 acceptance status 不是 passed，When 執行 Gate，Then 回報 `acceptance_not_passed:<id>`。
4. Given acceptance 沒有 evidence，When 執行 Gate，Then 回報 `evidence_missing:<id>`。
5. Given evidence id 存在但 artifact 沒有反向列出該 acceptance，When 執行 Gate，Then 回報 `evidence_not_linked:<id>:<evidence_id>`。
6. Given evidence 宣告未存在的 acceptance，When 執行 Gate，Then 回報 `acceptance_unknown:<id>`。
7. Given intent、context 或 source commit 不一致，When 執行 Gate，Then fail-closed，不能因其他 acceptance 通過而放行。
8. Given 相同輸入重試兩次，When 執行 Gate，Then 兩次報告相同，且輸入物件不被修改。

## 可執行範例

`day13/example-acceptance-coverage/` 使用 Python 標準函式庫實作唯讀 `evaluate_coverage(intent, evidence)`，fixture 宣告 AC-01～AC-03。9 項 `unittest` 測試涵蓋完整覆蓋、缺少／失敗／錯綁 acceptance、identity mismatch、重複 evidence id 與 deterministic read-only retry。

## 圖解與影片場景

- `diagrams/acceptance_coverage_flow.mmd`：Acceptance 宣告、Evidence Binding、逐項結果與 Coverage Gate 的流程。
- `diagrams/acceptance_coverage_states.mmd`：DECLARED、COLLECTING、COVERED、BLOCKED 與 READY_VERIFY 狀態。
- HTML deck 8 張：測試全綠仍漏需求、Acceptance IDs、coverage map、缺證據阻擋、reverse link、測試證據與責任鏈收束。

## 交付 gates

- canonical `article.md` 第一行只有標題，其餘為繁體中文 Markdown 正文；含 runnable example、Given／When／Then、table、Mermaid 與 GitHub links。
- companion example 完整 `python3 -m unittest -v`、`py_compile` 與 fixture CLI 執行成功。
- HTML deck 固定 1920×1080，8 張投影片，speaker notes 與畫面分離；由正式 claude-code-slides 0.6.0 scaffold 產生並通過官方 checker。
- Fish Audio per-scene MP3；manifest 的 slide duration 以 `ffprobe` 實際結果為準，TTS 不得為 silent。
- 每張投影片獨立擷取 1920×1080，notes 隱藏，建立 8 張 midpoint contact sheet 與至少一張 final-MP4 full-resolution frame。
- clean H.264/AAC MP4 固定 25 fps，字幕為獨立 UTF-8 SRT，不燒入畫面。
- FFprobe、full decode、volume、SRT timing、視覺檢查與 copied-artifact re-probe 全部 PASS。
- `上傳資訊.md` 僅記錄真實本機 artifact、`youtube_status=待上傳`、`ithome_status=待發布`、`github_status=待同步`；不含 OAuth、API key 或假想 watch URL。
- Producer 不執行 iThome、YouTube、GitHub 外部寫入。
