# Day 25｜Evidence Retention Gate 旁白稿

本檔是 Day 25 HTML deck 的 speaker notes／Fish TTS 與 SRT 文字來源。每個 scene 對應一張投影片；capture 時會隱藏 notes 與導覽 chrome。

## Scene 1 — 結案了，證據還在嗎？

Incident 結案不代表 evidence 可以立刻消失。客戶、稽核或下一次事故仍可能需要 recovery、impact、learning 和 approval 的原始脈絡。今天用 Evidence Retention Gate 確認結案後的證據仍能被辨識和讀回。

## Scene 2 — 三個狀態，三種責任

Closeout verified 代表當時的結案前提通過。Retention ready 代表現在的證據仍可讀、沒有漂移、期限也足夠。Human retention decision 才是負責人真正決定 archive、hold 或 delete 的地方，三個狀態不能互相冒充。

## Scene 3 — 先固定 retention identity

留存檢查不能只看服務名稱。Incident、closeout、run、digest、environment 和 target 都要對上。只要 identity 漂移，就先停在 blocked identity，不把另一個事件的 archive 結果套過來。

## Scene 4 — Archive 完成不代表檔案可讀

Inventory 顯示 archive complete，只是一個摘要。Gate 還要確認每一份 required evidence 都存在、readable，而且 storage state 不是 missing 或 unknown。任何一項無法讀回，都不能假裝整批證據安全。

## Scene 5 — 每份 evidence 都要綁同一個 digest

Recovery、impact、follow-up、learning 和 approval 都要回到同一個 evidence digest。只要其中一份 digest 漂移，就必須建立新的 evidence chain，不能安靜地覆蓋原本的證據。

## Scene 6 — 留存期限要涵蓋現在與 policy

Retention 不只看檔案何時建立，還要看 retain until 是否已過期，以及能不能涵蓋宣告的最低 policy window。缺少 created 或 expiry timestamp，或 expiry 太短，都要輸出明確的 blocked reason。

## Scene 7 — Legal hold 與 access scope 也要驗證

如果 intent 宣告需要 legal hold，observation 必須看到 hold 仍然 active。讀取 scope 也必須精確指向同一個 incident，不接受只有 production 或服務名稱的模糊範圍。

## Scene 8 — 唯讀 Gate 輸出下一步

Python 範例只讀 intent 與 observation，依固定順序輸出 reason code。它不刪檔、不移檔、不建立 legal hold，也不呼叫 archive API。成功輸出 retention ready，代表條件齊全，不代表系統已替我們做處置。

## Scene 9 — Day 10 到 Day 25 的證據鏈

這條系列從 Context freshness、變更、發布、穩定性、SLO、人工核准一路走到 rollback、recovery 和 incident closeout。Day 25 再往後補上 evidence retention，讓結案之後仍然能被回讀、追溯和驗證。

## Scene 10 — 留存 ready 不等於可以刪

記住三句話：closeout verified 不等於 retention ready；每份 evidence 都要綁回同一個 digest 並且可讀；retention ready 仍不等於可以刪除或公開，最後的資料處置責任要留在人類手上。
