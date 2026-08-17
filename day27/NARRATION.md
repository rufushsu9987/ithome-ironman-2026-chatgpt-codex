# Day 27 Speaker Notes／Fish TTS 來源

每個 scene 對應一張投影片；capture 時會隱藏 notes 與導覽 chrome。

## Scene 1 — 三道 Gate 都 PASS，真的接得起來嗎？

前幾天我們分別處理了事故結案、證據留存和證據讀取。今天要問一個更實際的問題：三段都說 PASS，整條 Incident Evidence Pipeline 真的接得起來嗎？如果它們指向不同的 incident、run 或 digest，最後交出去的可能是一條假的證據鏈。

## Scene 2 — Lifecycle Gate 的角色

Day 27 不再新增一個孤立檢查，而是做一個 Lifecycle Gate。它只讀取前面三道 Gate 的結果，確認 stage 順序、共同身份、evidence digest、必要證明和 audit event 都一致。它不會關閉 incident、不會刪除 evidence，也不會發放權限。

## Scene 3 — 單點 PASS 不等於 Pipeline Ready

單一 Gate 通過，只代表自己的範圍成立。Closeout 說事故可以結案，Retention 說證據還留得住，Access 說請求具備讀取前提。Lifecycle Gate 要再確認，這三個結果是不是屬於同一個 incident，而且真的可以一段接一段交出去。

## Scene 4 — 先鎖共同 Identity 與 Digest

第一道檢查是共同身份：incident、closeout、run、environment 和 target。接著檢查 evidence digest。只要其中一段的 digest 不同，就代表證據可能已漂移，不能因為其他 stage 曾經通過，就把它們拼在一起。

## Scene 5 — Stage 順序就是責任順序

這條 pipeline 的順序是 Closeout、Retention、Access。Access 不能跳過 Retention 的 readback；Retention 也不能接上另一個 incident 的 Closeout。順序錯誤時，Lifecycle Gate 會回傳具體 reason，而不是讓最後一段 PASS 蓋掉前面的缺口。

## Scene 6 — 每一段都要有自己的證明

除了狀態與 digest，每個 stage 都要有 audit event。Retention 需要 readback proof，Access 需要綁定 approval。這些欄位不是裝飾，而是讓下一個 owner 能回答：這個 PASS 是誰、在什麼範圍、依哪一次檢查產生的。

## Scene 7 — Runnable Example：把交接契約跑出來

範例使用兩份 JSON：intent 描述預期的 pipeline，observation 描述三個 stage 的實際回報。Lifecycle Gate 只回傳 allowed、state 和 reasons，不執行任何外部動作。相同輸入可以重跑，結果也會保持一致。

## Scene 8 — pipeline_ready 與 blocked_pipeline

所有條件都成立時，結果是 pipeline_ready，代表可以交給下一個 owner 審查。缺 stage、順序錯誤、digest 漂移或 audit 缺失時，結果是 blocked_pipeline，並列出具體原因。這裡的 ready 是交接資格，不是自動執行許可。

## Scene 9 — 先驗證證據鏈，再接不可逆動作

落地時先統一三道 Gate 的 identity 和輸出格式，再用唯讀 Lifecycle Gate 觀察實際交接。接著把 reason code 接到 runbook 和監控。等人類 owner 確認證據鏈穩定後，才討論哪些動作能交給受控 executor。

## Scene 10 — 小結：讓每個 PASS 都接得上

Day 24 到 Day 26 守住結案、留存和讀取；Day 27 把它們串成 Lifecycle Gate。真正可靠的 PASS，必須說清楚它屬於哪個 incident、接在什麼 stage、把哪份 evidence 交給誰。身份、順序、digest、證明和 audit 都對上，才是 pipeline_ready。
