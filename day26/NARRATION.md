# Day 26 Speaker Notes／Fish TTS 來源

每個 scene 對應一張投影片；capture 時會隱藏 notes 與導覽 chrome。

## Scene 1 — 證據留住了，誰都能讀嗎？

Day 25 確認 evidence 還在、可回讀、期限也有效。但留住證據，不代表所有人都能讀。今天把 access request 的角色、目的、欄位和期限，變成另一道可以驗證的 Gate。

## Scene 2 — retention、access、grant 是三個狀態

Retention ready 代表證據還存在。Access eligible 代表這次請求符合前提。Access granted 則是授權執行層真的放行。三個狀態要分開，Gate 不能預告已經讀到資料。

## Scene 3 — 先把 request 綁回同一個 identity

Access request 必須綁住 incident、closeout、run、digest、environment 和 target。只要任一欄位漂移，就先停在 blocked identity，不把另一個事件的核准搬過來。

## Scene 4 — role 和 purpose 不是裝飾

合法角色不代表任何目的都合法，合法目的也不代表可以讀整包 evidence。Gate 會分開檢查 requester role、purpose 和允許的 evidence surface，讓下一步 reason code 足夠具體。

## Scene 5 — 最小欄位範圍比整包可讀安全

Intent 先宣告每個 evidence 可以讀哪些欄位。Request 只能提出完成目的所需的子集合。多一個 raw payload，即使它存在、即使 requester 權限很高，也要被 field scope exceeded 擋下來。

## Scene 6 — access window 必須短而且可回讀

Request 要有 requested time 和 expiry time，不能在未來、不能已過期，也不能超過 policy 的最長秒數。需要延長時，建立新的 request 和 approval，不偷偷修改舊紀錄。

## Scene 7 — approval 和 audit 都要綁 scope

Approved 不是萬用通行證。Approval 必須對應同一個 requester、purpose、target 和 digest。之後還要留下 event id、request digest 和 evidence digest，讓真正的讀取可以被追蹤。

## Scene 8 — Python 範例只回報 access eligible

Runnable example 只讀 intent、request、inventory、approval 和 audit anchor。同一組輸入會得到同一組 reason code。成功代表可以交給授權執行層，不代表已經發 token 或讀取檔案。

## Scene 9 — 從 retention 到 audited read

Day 10 到 Day 25 把 context、變更、發布、恢復、結案與留存串起來。Day 26 再加上讀取邊界，讓證據同時保護調查者的需要與資料被讀取時的範圍。

## Scene 10 — 留存和讀取是兩道不同的 Gate

記住三句話：retention ready 不等於 access eligible；access 要限制 role、purpose、evidence、fields 和時間；access eligible 也不等於 access granted，真正讀取要由授權系統執行並留下 audit anchor。
