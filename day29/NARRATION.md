# Day 29 Speaker Notes：Rollout Promotion Gate

## Scene 1 — 綠燈不等於可以全開

新版本先放給一小群使用者，dashboard 看起來很健康，團隊就想直接放到全部使用者。今天要補上的不是另一個部署工具，而是一道 promotion readiness check，先確認觀察夠不夠、下一步是否符合政策。

## Scene 2 — Promotion Gate 只回答能不能交接

Rollout Promotion Gate 是唯讀檢查。它不改 feature flag、不切 traffic，也不替 release owner 做決策。它只把 observation、metrics、policy、approval 和 handoff 綁在同一個 promotion identity 上，回答能不能交給下一個責任邊界。

## Scene 3 — 一筆漂亮數字不等於穩定

第一關是 observation。要先確認觀察窗已完成、樣本數足夠，而且資料屬於同一個 run。即使最新一筆 error rate 是零，觀察時間不足，也只能停在 blocked observation。

## Scene 4 — 五層 identity 讓證據對得上

這次至少要綁定 release、environment、current cohort、target cohort、run、promotion、digest 和 policy version。只要其中一欄漂移，就不能拿另一輪的綠燈完成這次 promotion。

## Scene 5 — 固定五段順序

Promotion 流程固定是 observe、metrics、policy、approval、handoff。先看資料夠不夠，再看指標，再看放量步幅，接著確認核准，最後把清楚的決策交給下一個 owner。任一關失敗就停止。

## Scene 6 — Metrics 要看完整組合

error rate、p95 latency 和 saturation 要一起看。平均值漂亮，不代表尾端使用者沒有變慢；錯誤率沒超標，也不代表資源沒有逼近上限。三項都通過，才算 metrics passed。

## Scene 7 — 目標 cohort 不能跳級

目前是 canary-10，不代表下一步可以任意跳到 all-users。Intent 要寫清楚允許的 target cohort、最大 step 和 policy version。超過步幅就回報固定 reason code，不把風險藏在一句可以繼續。

## Scene 8 — Python 範例只讀、可重跑

Runnable example 只讀 intent 和 observation，輸出 promotion ready 或 reason code。它不碰 traffic，也不修改輸入。相同 promotion id 已經執行過時，會回報 duplicate promotion，避免 retry 變成重複放量。

## Scene 9 — Gate、Owner、Executor 分工

Gate 通過只是 evidence 完整。Release owner 仍要決定 promote 或 hold，Executor 才能在明確 handoff 下改變 traffic。執行之後要留下新的 event 和新的 observation，不能重用舊綠燈。

## Scene 10 — 把放量決策交接清楚

記住三件事：觀察窗完整才有資格談 promotion；promotion ready 不等於 traffic changed；每次 promotion 都要有 scope、owner、promotion id 和 idempotency key。能被觀察、被核准、被交接，才是可控的 rollout。
