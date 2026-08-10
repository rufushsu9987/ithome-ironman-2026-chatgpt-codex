# 2026 iThome 鐵人賽：ChatGPT × Codex 企業級 AI 開發工作流

本專案保存 2026 iThome 鐵人賽系列「不只會寫 Code：用 ChatGPT × Codex 打造企業級 AI 開發工作流」的文章來源、圖解與可重現範例。

## 系列內容

| Day | 主題 | iThome | YouTube | 專案內容 |
| --- | --- | --- | --- | --- |
| 2 | 別急著叫 AI 寫 Code！把模糊需求變成可驗收規格 | [閱讀文章](https://ithelp.ithome.com.tw/articles/10401615) | [觀看影片](https://www.youtube.com/watch?v=eXcyDbvCT_k) | [文章、程式碼與架構圖](./day02/) |
| 3 | 多代理越多越快？用 Repository Context Pack 讓 Codex 有邊界地執行 | [閱讀文章](https://ithelp.ithome.com.tw/articles/10401737) | [觀看影片](https://www.youtube.com/watch?v=mW9jNtuN8Fo) | [文章、範例與圖解](./day03/) |
| 4 | 會跑不等於能改！用最小權限與工作樹隔離守住 Codex 執行邊界 | [閱讀文章](https://ithelp.ithome.com.tw/articles/10401856) | [觀看影片](https://www.youtube.com/watch?v=k2UEzgYGGyw) | [文章、範例與圖解](./day04/) |
| 5 | 每個 Agent 都說完成了？用 Verify Matrix 收斂測試、Diff 與交付證據 | [閱讀文章](https://ithelp.ithome.com.tw/articles/10402088) | [觀看影片](https://www.youtube.com/watch?v=SLtDRNtKy0s) | [文章、範例與圖解](./day05/) |
| 6 | 測試通過還不夠！用 Deliver Pack 讓下一個人接得上 | 待發布 | 待發布 | [文章、範例與圖解](./day06/) |
| 7 | 測試都通過，為什麼還不能發布？用 Release Gate 管好相依性、回滾與最終責任 | 待發布 | 待發布 | [文章、範例與圖解](./day07/) |

## Day 2 收錄內容

- `day02/article.md`：完整文章 Markdown 來源
- `day02/example-api/`：可執行的訂單 CSV 匯出服務與 6 項驗收測試
- `day02/diagrams/diagram_requirement_gate.svg`：需求收斂閘門
- `day02/diagrams/diagram_acceptance_layers.svg`：可驗收規格五層次
- `day02/diagrams/diagram_order_export_architecture.svg`：訂單 CSV 匯出非同步架構

## Day 3 收錄內容

- `day03/article.md`：Repository Context Pack 與 Plan Contract 完整文章來源
- `day03/example-context/`：可執行的 Context Gate 範例與測試
- `day03/diagrams/context_pack_flow.mmd`：Context Pack 流程圖原始檔
- `day03/diagrams/plan_contract.mmd`：Plan Contract 圖解原始檔
- Day 3 YouTube 影片：[mW9jNtuN8Fo](https://www.youtube.com/watch?v=mW9jNtuN8Fo)
- Day 3 iThome 文章：[10401737](https://ithelp.ithome.com.tw/articles/10401737)

## Day 4 收錄內容

- `day04/article.md`：Execution Contract、工作樹隔離與停止條件完整文章來源
- `day04/example-execution-guard/`：可執行的 Execution Guard 範例與 9 項測試
- `day04/diagrams/execution_boundary.mmd`：執行邊界流程圖原始檔
- `day04/diagrams/stop_conditions.mmd`：停止條件狀態圖原始檔
- Day 4 YouTube 影片：[k2UEzgYGGyw](https://www.youtube.com/watch?v=k2UEzgYGGyw)
- Day 4 iThome 文章：[10401856](https://ithelp.ithome.com.tw/articles/10401856)

## Day 5 收錄內容

- `day05/article.md`：Verify Matrix、測試證據與交付判斷完整文章來源
- `day05/example-verify-matrix/`：可執行的 Verify Matrix 範例與 12 項測試
- `day05/diagrams/verify_matrix.mmd`：Verify Matrix 流程圖原始檔
- `day05/diagrams/evidence_layers.mmd`：四層證據圖解原始檔
- Day 5 YouTube 影片：[SLtDRNtKy0s](https://www.youtube.com/watch?v=SLtDRNtKy0s)
- Day 5 iThome 文章：[10402088](https://ithelp.ithome.com.tw/articles/10402088)

## Day 6 收錄內容

- `day06/article.md`：Deliver Pack、交接狀態與責任邊界完整文章來源
- `day06/example-deliver-pack/`：可執行的 Deliver Pack 驗證器與 9 項測試
- `day06/diagrams/deliver_pack_flow.mmd`：Deliver Pack 流程圖原始檔
- `day06/diagrams/handoff_states.mmd`：Verified、Ready for handoff 與 Published 狀態圖原始檔
- Day 6 YouTube 影片：[DIRZ35Ha8mo](https://www.youtube.com/watch?v=DIRZ35Ha8mo)
- Day 6 iThome 文章：[10402184](https://ithelp.ithome.com.tw/articles/10402184)

## Day 7 收錄內容

- `day07/article.md`：Release Gate、相依性一致性、人工核准與 rollback 完整文章來源
- `day07/example-release-gate/`：可執行的 fail-closed Release Gate 驗證器、fixtures 與 7 項測試
- `day07/diagrams/release_gate_flow.mmd`：多個 Deliver Pack 進入 Release Gate 的流程圖原始檔
- `day07/diagrams/release_states.mmd`：OPEN、BLOCKED、READY 與 rollback 狀態圖原始檔
- Day 7 影片與 iThome 文章連結會在公開回讀完成後補上

## 使用方式

SVG 圖表可直接用瀏覽器開啟，也能轉成 PNG／JPG 後放入技術文章。文章中的範例著重：

1. 把模糊自然語言轉成 Given／When／Then。
2. 將 `OPEN` 未決項目留給團隊確認，不讓模型自行猜測。
3. 由 Codex 在明確邊界內實作、測試並交付可重現證據。
4. 用版本化 Context Pack 與 Plan Contract，讓多代理從同一份可驗證事實開始工作。

Day 5 之後的文章、影片與範例會持續加入本專案。
