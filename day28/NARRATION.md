# Day 28 Speaker Notes／Fish TTS 來源

每個 scene 對應一張投影片；capture 時會隱藏 notes 與導覽 chrome。

## Scene 1 — rollout 不是一次推完就好

新版本部署完成，不代表 rollout 流程已經可控。今天我們把 canary、feature flag、rollback 和健康檢查綁回同一輪 rollout，先確認觀察的是不是同一件事，再決定能不能往下一關走。

## Scene 2 — Progressive Rollout Gate 在查什麼

Progressive Rollout Gate 是唯讀的 readiness check。它不部署、不改 flag，也不執行 rollback；它只檢查 identity、觀察證據、回退契約和健康檢查是否完整，最後用固定 reason code 說明能不能交給下一個責任邊界。

## Scene 3 — 分段闖關

流程固定分成五關：第一關確認 identity，第二關看 canary 的錯誤率與延遲，第三關確認 flag 分組，第四關確認 rollback 契約，第五關回讀同一輪健康結果。任一關不一致，就停在 blocked，不要繼續放大流量。

## Scene 4 — 先固定 rollout identity

同一個 rollout 的觀察都要綁回 release、environment、cohort、flag key、run 和 evidence digest。只要其中一欄漂移，就先回傳 blocked identity，不拿上一輪 rollout 的結果來湊這一輪結論。

## Scene 5 — canary 指標要一起看

canary 不是只看 p95。錯誤率、延遲、cohort 對應和 readback 都要屬於同一輪，而且要在門檻內。只要其中一個不符合，就進入 observe-and-stop，而不是自動放大流量。

## Scene 6 — feature flag 必須可對應

Feature flag 不只是開關。Gate 還要確認誰被開啟、分組是否正確，以及出問題時 kill switch 是否可用。key 正確但 cohort mapping 錯了，仍然不能算通過。

## Scene 7 — rollback readiness 是契約

Rollback 要在 rollout 前就說清楚：要回到哪個 target、什麼條件會觸發、多久內要完成判斷。Gate 不會替你執行 rollback，但會阻擋缺少契約的 rollout 繼續往前。

## Scene 8 — 健康檢查要回讀同一份結果

健康檢查、事件紀錄和 observation 必須屬於同一份 intent、同一個 run、同一個 cohort。舊 run 的 healthy 不能替新 release 背書，否則畫面是綠的，證據鏈卻已經斷了。

## Scene 9 — Python 範例只回報，不執行

Runnable example 只讀 intent 和 observation，輸出 allowed、state 與 reason code。它不讀 evidence 內容、不發 token、不呼叫外部 API。同一組輸入可以在 deploy、QA 和稽核流程中重跑。

## Scene 10 — pipeline ready 不是全面上線

記住三件事：先比對同一份 rollout identity；每一段都要有同一份 digest 和 audit event；pipeline ready 只代表可以交給下一個責任邊界，不是已經對所有使用者生效。
