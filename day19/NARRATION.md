# Day 19｜Post-Deployment Stability Gate 旁白稿

本檔是 Day 19 HTML deck 的 speaker notes／Fish TTS 與 SRT 文字來源。每個 scene 對應一張投影片；capture 時會隱藏 notes 與導覽 chrome。

## Scene 1 — Deployment Verified 不等於穩定

Deployment Verification Gate 通過，只代表某個時間點的部署、replica 和 traffic 對得上。五分鐘後錯誤率可能上升，所以今天再加入一段 observation window，確認服務不是只有一瞬間看起來正常。

## Scene 2 — Verification 和 Stability 問不同問題

Day 18 問的是：現在部署的是不是這個 candidate。Day 19 問的是：在一段真實流量期間，這個 candidate 是否持續健康。兩個問題都要回答，才能避免把瞬間綠燈當成穩定。

## Scene 3 — 先固定 identity

不要看到最新的 dashboard row 就直接判斷。先固定 intent、run、candidate、source、input、environment 和 target。觀察資料如果不是同一個 identity，就算 metrics 很漂亮也不能放行。

## Scene 4 — Observation window 要完整

一筆成功請求不能代表穩定。Gate 會檢查 observation window 已經完成、持續時間達標，而且樣本數足夠。window 還在收集或樣本太少時，先留下 blocked reason，不猜測結果。

## Scene 5 — 三個 metrics 一起看

穩定性不是只看 error rate。error rate、p95 latency 和 saturation 分別代表失敗、變慢和資源壓力。任何一項超過 intent 宣告的門檻，Gate 都會 fail-closed，保留超標的 observation。

## Scene 6 — Required checks 仍然要有證據

window、health、errors、latency、saturation 和 traffic 都是 required checks。只有 passed 才算證據。skipped、pending、failed 或缺少欄位，都不能被包裝成穩定。

## Scene 7 — Traffic 可能在驗證後漂移

就算前一個 Gate 看到正確 candidate，後續 route 仍可能切到別的版本。Stability Gate 會再讀回 serving candidate 和 route state；只要不是同一個 candidate 且仍在 serving，就回報 traffic mismatch。

## Scene 8 — 唯讀 Gate 的輸出

Python 範例把 identity、window、samples、metrics、checks 和 traffic 放在同一份 observation 裡比對。成功時回報 post deployment stable；任何缺口都輸出 deterministic reason，不調整容量，也不自行 rollback。

## Scene 9 — Day 10 到 Day 19

Day 10 到 Day 18 逐層確認 context、範圍、證據、需求、重現、artifact、release candidate 和部署狀態。Day 19 再觀察一段真實流量，讓證據鏈從「部署了什麼」走到「持續跑得怎麼樣」。

## Scene 10 — 今天的結論

記住一句話：verified 不等於 stable。先固定 identity，再等待完整 window，檢查樣本、error rate、latency、saturation 和 traffic。穩定性是可回讀的證據，不是 AI 自動改變服務的許可。
