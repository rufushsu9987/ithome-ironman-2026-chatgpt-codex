# Day 24｜恢復驗證通過就能結案嗎？用 Incident Closeout Gate 把復原、學習與追蹤責任綁起來

本檔是 Day 24 HTML deck 的 speaker notes／Fish TTS 與 SRT 文字來源。每個 scene 對應一張投影片；capture 時會隱藏 notes 與導覽 chrome。

## Scene 1 — 恢復了，不等於可以結案

Rollback 後服務恢復，還不代表 incident 可以直接關閉。客戶影響、後續修正、postmortem 和下一次要學到的規則，都還需要有人接住。今天用 Incident Closeout Gate 把這些責任綁回同一個事件。

## Scene 2 — 三個狀態，三種責任

Recovery verified 是服務證據通過。Closeout eligible 是結案前提齊全。Human closeout 才是負責人真正做出的結案決定。這三個狀態不能互相冒充，也不能因為 dashboard 變綠就跳過中間的 evidence。

## Scene 3 — 先固定 incident identity

結案 evidence 必須知道自己屬於哪一次 incident、哪一次 recovery、哪個 run、哪個 candidate 和哪個 environment。只要 identity 漂移，就先停在 blocked identity，不把別的事件結果套過來。

## Scene 4 — 恢復後還要看影響窗口

Recovery Gate 確認服務回到安全 candidate，但 Closeout Gate 還要確認 customer impact window 已完成，時間和樣本數都達標。只看一分鐘的漂亮指標，不能代表整段影響已經收尾。

## Scene 5 — Follow-up 要有人負責

Monitoring、data audit、runbook 和 learning pack 等 critical follow-up，都要有 owner、期限和可讀狀態。缺 owner、過期或停在 pending，都是結案阻擋條件，不能把工作清單留給沒有人負責的未來。

## Scene 6 — Postmortem 與 learning pack 要綁回 digest

Postmortem 和 learning pack 不是兩個孤立檔案。它們要綁住相同的 incident id 和 evidence digest，讓下一次載入 Context 時，知道這份教訓來自哪一次已驗證的事故。

## Scene 7 — Closeout approval 也有 scope

最後仍然需要人類 owner 核准，但核准要有正確 role、正確 scope、有效時間，而且要對應同一個 incident。不是拿到一筆 approved 就可以關閉任何事件。

## Scene 8 — 唯讀 Gate 輸出下一步

Python 範例只讀 intent 與 observation，依固定順序輸出 reason code。它不關閉 incident、不建立任務，也不呼叫修復 API。成功輸出 closeout eligible，代表前提齊全，不代表系統已經替我們結案。

## Scene 9 — Day 10 到 Day 24 的證據鏈

這條系列從 Context freshness、變更證據、發布、穩定性、SLO、人工核准一路走到 rollback 和 recovery。Day 24 再把 impact、follow-up、learning 和 human closeout 接上，讓恢復後的責任也能被回讀。

## Scene 10 — 結案也要能被驗證

記住三句話：recovery verified 不等於 closeout eligible；結案前要把影響、追蹤、postmortem 和 learning 綁回同一個 digest；closeout eligible 仍不等於已結案，最後的責任要留在人類手上。
