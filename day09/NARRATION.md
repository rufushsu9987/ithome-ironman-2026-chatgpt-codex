# Day 9｜Learning Pack 與證據回流白話版講稿

## Scene 1 — 事故恢復不是學會

Day 8 處理了事故發生後的追蹤與復原，但服務恢復不代表團隊已經學會。Day 9 要把已確認的生產證據整理成 Learning Pack，經過人工核准後帶回下一次 AI 變更，避免每次事故都從零開始。

## Scene 2 — 事故之後的缺口

想像訂單匯出事故已經回滾完成，Incident Pack 也標記 resolved。兩週後，新的 agent 要修改同一個服務，卻不知道上次事故告訴我們大檔案要交給背景 worker、回滾後要重新驗證。這就是恢復和學習之間的缺口。

## Scene 3 — 可拒絕的學習流程

Learning Pack 的重點不是自動產生一份漂亮摘要，而是保留 proposed、approved、applied 的狀態。AI 可以從事件與測試提出候選；人類確認證據、範圍與責任後，才把 learning id 版本化並套用到下一個 Context。

## Scene 4 — 可回溯的欄位

一筆 Learning Pack 至少要有 learning id、原始 incident、change id、source commit、evidence refs、scope、owner 和 approval。這些欄位讓下一個人知道規則從哪裡來、適用在哪裡，以及誰對它負責。缺少其中一項，就不應該直接套用。

## Scene 5 — Fail-closed 邊界

這裡延續前幾天的 fail-closed 原則。事故還沒 resolved、證據不完整、沒有人工核准，或 learning 與目前 Context 不同，都要阻擋。AI 可以整理候選內容，但不能自己核准自己的摘要，更不能把它直接寫進共享規則。

## Scene 6 — 安全套用與重試

即使 Learning Pack 已核准，套用時仍然要檢查 context id 與適用範圍。這筆 orders-export 的學習不能套到 billing；服務內的規則也不能擴大成整個 Repository。最後用 learning id 做 idempotency key，讓 CI 或 agent 重試時不會重複加入。

## Scene 7 — 測試證據

Day 9 的範例用六項測試鎖住邊界：resolved incident 才能建立學習、缺少 evidence 或 scope 要阻擋、沒有人工核准不能套用、跨 Context 要拒絕，而同一個 learning id 重試兩次仍只加入一次。這讓「回流」不是口號，而是可以重跑的證據。

## Scene 8 — Close the loop

Day 8 的 Incident Pack 讓我們知道這次事故是否恢復；Day 9 的 Learning Pack 把已確認的證據帶回下一次 Context。只有 resolved、approved、有限範圍和 idempotent 套用都成立，責任鏈才完成回饋。ChatGPT 可以整理，Codex 可以在邊界內執行，人類仍然負責核准。
