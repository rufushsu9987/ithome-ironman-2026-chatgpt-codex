# 2026 iThome 鐵人賽：ChatGPT × Codex 企業級 AI 開發工作流

本專案保存 2026 iThome 鐵人賽系列「不只會寫 Code：用 ChatGPT × Codex 打造企業級 AI 開發工作流」的文章來源、圖解與可重現範例。

## 系列內容

[解說頻道](https://youtube.com/channel/UCSwTYj59dr3-qVO_AQu8vyA?si=ZDHYFy30xRNX8zc7)

| Day | 主題 | 
| --- | --- |
| 1 | 從「會寫 Code」到可治理：為什麼企業需要 AI 開發工作流 | 
| 2 | 別急著叫 AI 寫 Code！用 ChatGPT × Codex 把模糊需求變成可驗收規格 |
| 3 | 多代理越多越快？用 Repository Context Pack 讓 Codex 有邊界地執行 | 
| 4 | 會跑不等於能改！用最小權限與工作樹隔離守住 Codex 執行邊界 |
| 5 | 每個 Agent 都說完成了？用 Verify Matrix 收斂測試、Diff 與交付證據 |
| 6 | 測試通過還不夠！用 Deliver Pack 讓下一個人接得上 |
| 7 | 測試都通過，為什麼還不能發布？用 Release Gate 管好相依性、回滾與最終責任 | 
| 8 | 發布之後才是真正的考驗！用 Audit Trail 與 Incident Pack 讓 AI 變更可追溯、可復原 | 
| 9 | 事故處理完就結束了？用 Learning Pack 把生產證據帶回下一次 AI 變更 |
| 10 | Learning Pack 放進 Context 就安全了嗎？用 Freshness Gate 擋住過期規則 | 
| 11 | Freshness Gate 通過就能一路改下去嗎？用 Change Budget 擋住範圍膨脹 |
| 12 | 測試通過就算是這次變更的證據嗎？用 Evidence Binding 綁住 diff、測試與 review |
| 13 | 測試都通過，怎麼知道需求沒有漏掉？用 Acceptance Coverage 補齊驗收證據 |
| 14 | 驗收證據都齊了，真的能交付嗎？用 Traceability Gate 把需求、變更與發布決策串起來 |
| 15 | 需求、變更都串起來了，明天還能重現嗎？用 Reproducibility Gate 鎖住環境與輸入 | 
| 16 | 重現成功就能直接交付嗎？用 Artifact Promotion Gate 擋住錯誤產物 | 
| 17 | Artifact 可以晉級，真的能安全發布嗎？用 Release Candidate Gate 鎖住最後一哩 |
| 18 | Release Candidate 通過就真的上線了嗎？用 Deployment Verification Gate 核對實際狀態 |
| 19 | Deployment Verified 就穩定了嗎？用 Post-Deployment Stability Gate 觀察真實流量 | 
| 20 | Stability 通過，使用者真的沒受影響嗎？用 SLO Impact Gate 看真實可靠性 |
| 21 | 證據都通過就能發布嗎？用 Human Approval Gate 把不可逆動作交回人類 |
| 22 | 出問題要回滾，但誰來決定回滾到哪？用 Rollback Gate 把風險寫成可驗收的 evidence |
| 23 | 回滾成功就算恢復了嗎？用 Recovery Verification Gate 確認系統真的回到安全狀態 | 
| 24 | 恢復驗證通過就能結案嗎？用 Incident Closeout Gate 把復原、學習與追蹤責任綁起來 | 
| 25 | Incident 結案後就能刪證據嗎？用 Evidence Retention Gate 守住留存期限與回讀能力 |
| 26 | 證據留住了，誰都能讀嗎？用 Evidence Access Gate 守住最小權限與稽核範圍 | 
| 27 | Evidence 都通過了，整條 Incident Pipeline 真的接得起來嗎？用 Lifecycle Gate 串起 Closeout、Retention 與 Access | 
| 28 | rollout 不是一次推完就好！用 Progressive Rollout Gate 把 canary、flag、rollback 與健康檢查綁成可觀察流程 |
| 29 | 放量不是看到綠燈就全開！用 Rollout Promotion Gate 把觀察窗、分段決策與責任交接綁在一起 |  |
| 30 | AI 會跑不等於能交付！用 Delivery Contract 把 30 天工作流收成可回讀的工程閉環 |
