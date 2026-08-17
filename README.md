# 2026 iThome 鐵人賽：ChatGPT × Codex 企業級 AI 開發工作流

本專案保存 2026 iThome 鐵人賽系列「不只會寫 Code：用 ChatGPT × Codex 打造企業級 AI 開發工作流」的文章來源、圖解與可重現範例。

## 系列內容

| Day | 主題 | iThome | YouTube | 專案內容 |
| --- | --- | --- | --- | --- |
| 1 | 從「會寫 Code」到可治理：為什麼企業需要 AI 開發工作流 | [閱讀文章](https://ithelp.ithome.com.tw/articles/10401215) | [觀看影片](https://www.youtube.com/watch?v=tX3immUNyMk) | [文章、程式碼與圖解](./day01/) |
| 2 | 別急著叫 AI 寫 Code！用 ChatGPT × Codex 把模糊需求變成可驗收規格 | [閱讀文章](https://ithelp.ithome.com.tw/articles/10401615) | [觀看影片](https://www.youtube.com/watch?v=eXcyDbvCT_k) | [文章、程式碼與圖解](./day02/) |
| 3 | 多代理越多越快？用 Repository Context Pack 讓 Codex 有邊界地執行 | [閱讀文章](https://ithelp.ithome.com.tw/articles/10401737) | [觀看影片](https://www.youtube.com/watch?v=mW9jNtuN8Fo) | [文章、程式碼與圖解](./day03/) |
| 4 | 會跑不等於能改！用最小權限與工作樹隔離守住 Codex 執行邊界 | [閱讀文章](https://ithelp.ithome.com.tw/articles/10401856) | [觀看影片](https://www.youtube.com/watch?v=k2UEzgYGGyw) | [文章、程式碼與圖解](./day04/) |
| 5 | 每個 Agent 都說完成了？用 Verify Matrix 收斂測試、Diff 與交付證據 | [閱讀文章](https://ithelp.ithome.com.tw/articles/10402088) | [觀看影片](https://www.youtube.com/watch?v=SLtDRNtKy0s) | [文章、程式碼與圖解](./day05/) |
| 6 | 測試通過還不夠！用 Deliver Pack 讓下一個人接得上 | [閱讀文章](https://ithelp.ithome.com.tw/articles/10402184) | [觀看影片](https://www.youtube.com/watch?v=DIRZ35Ha8mo) | [文章、程式碼與圖解](./day06/) |
| 7 | 測試都通過，為什麼還不能發布？用 Release Gate 管好相依性、回滾與最終責任 | [閱讀文章](https://ithelp.ithome.com.tw/articles/10402339) | [觀看影片](https://www.youtube.com/watch?v=ZuFy4cbZ2EU) | [文章、程式碼與圖解](./day07/) |
| 8 | 發布之後才是真正的考驗！用 Audit Trail 與 Incident Pack 讓 AI 變更可追溯、可復原 | 待發布 | [觀看影片](https://www.youtube.com/watch?v=nZ_tF2Hj754) | [文章、程式碼與圖解](./day08/) |
| 9 | 事故處理完就結束了？用 Learning Pack 把生產證據帶回下一次 AI 變更 | [閱讀文章](https://ithelp.ithome.com.tw/articles/10402613) | [觀看影片](https://www.youtube.com/watch?v=gKLJz1hjh5o) | [文章、程式碼與圖解](./day09/) |
| 10 | Learning Pack 放進 Context 就安全了嗎？用 Freshness Gate 擋住過期規則 | [閱讀文章](https://ithelp.ithome.com.tw/articles/10402721) | [觀看影片](https://www.youtube.com/watch?v=Jt_6iBtCFjs) | [文章、程式碼與圖解](./day10/) |
| 11 | Freshness Gate 通過就能一路改下去嗎？用 Change Budget 擋住範圍膨脹 | [閱讀文章](https://ithelp.ithome.com.tw/articles/10402889) | [觀看影片](https://www.youtube.com/watch?v=sWSrKdn0Hr4) | [文章、程式碼與圖解](./day11/) |
| 12 | 測試通過就算是這次變更的證據嗎？用 Evidence Binding 綁住 diff、測試與 review | [閱讀文章](https://ithelp.ithome.com.tw/articles/10403128) | 待上傳 | [文章、程式碼與圖解](./day12/) |
| 13 | 測試都通過，怎麼知道需求沒有漏掉？用 Acceptance Coverage 補齊驗收證據 | [閱讀文章](https://ithelp.ithome.com.tw/articles/10403422) | [觀看影片](https://www.youtube.com/watch?v=jEiTypirhQE) | [文章、程式碼與圖解](./day13/) |
| 14 | 驗收證據都齊了，真的能交付嗎？用 Traceability Gate 把需求、變更與發布決策串起來 | 待發布 | 待上傳 | [文章、程式碼與圖解](./day14/) |
| 15 | 需求、變更都串起來了，明天還能重現嗎？用 Reproducibility Gate 鎖住環境與輸入 | 待發布 | 待上傳 | [文章、程式碼與圖解](./day15/) |
| 16 | 重現成功就能直接交付嗎？用 Artifact Promotion Gate 擋住錯誤產物 | 待發布 | 待上傳 | [文章、程式碼與圖解](./day16/) |
| 17 | Artifact 可以晉級，真的能安全發布嗎？用 Release Candidate Gate 鎖住最後一哩 | 待發布 | 待上傳 | [文章、程式碼與圖解](./day17/) |
| 18 | Release Candidate 通過就真的上線了嗎？用 Deployment Verification Gate 核對實際狀態 | 待發布 | 待上傳 | [文章、程式碼與圖解](./day18/) |
| 19 | Deployment Verified 就穩定了嗎？用 Post-Deployment Stability Gate 觀察真實流量 | 待發布 | 待上傳 | [文章、程式碼與圖解](./day19/) |
| 20 | Stability 通過，使用者真的沒受影響嗎？用 SLO Impact Gate 看真實可靠性 | 待發布 | 待上傳 | [文章、程式碼與圖解](./day20/) |
| 21 | 證據都通過就能發布嗎？用 Human Approval Gate 把不可逆動作交回人類 | 待發布 | 待上傳 | [文章、程式碼與圖解](./day21/) |
| 22 | 出問題要回滾，但誰來決定回滾到哪？用 Rollback Gate 把風險寫成可驗收的 evidence | 待發布 | 待上傳 | [文章、程式碼與圖解](./day22/) |
| 23 | 回滾成功就算恢復了嗎？用 Recovery Verification Gate 確認系統真的回到安全狀態 | 待發布 | 待上傳 | [文章、程式碼與圖解](./day23/) |
| 24 | 恢復驗證通過就能結案嗎？用 Incident Closeout Gate 把復原、學習與追蹤責任綁起來 | 待發布 | 待上傳 | [文章、程式碼與圖解](./day24/) |
| 25 | Incident 結案後就能刪證據嗎？用 Evidence Retention Gate 守住留存期限與回讀能力 | 待發布 | 待上傳 | [文章、程式碼與圖解](./day25/) |
| 26 | 證據留住了，誰都能讀嗎？用 Evidence Access Gate 守住最小權限與稽核範圍 | 待發布 | 待上傳 | [文章、程式碼與圖解](./day26/) |
| 27 | Evidence 都通過了，整條 Incident Pipeline 真的接得起來嗎？用 Lifecycle Gate 串起 Closeout、Retention 與 Access | 待發布 | 待上傳 | [文章、程式碼與圖解](./day27/) |
| 28 | rollout 不是一次推完就好！用 Progressive Rollout Gate 把 canary、flag、rollback 與健康檢查綁成可觀察流程 | 待發布 | 待上傳 | [文章、程式碼與圖解](./day28/) |
| 29 | 放量不是看到綠燈就全開！用 Rollout Promotion Gate 把觀察窗、分段決策與責任交接綁在一起 | 待發布 | 待上傳 | [文章、程式碼與圖解](./day29/) |
| 30 | AI 會跑不等於能交付！用 Delivery Contract 把 30 天工作流收成可回讀的工程閉環 | 待發布 | 待上傳 | [文章、程式碼與圖解](./day30/) |

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
- Day 7 YouTube 影片：[[ZuFy4cbZ2EU](https://www.youtube.com/watch?v=ZuFy4cbZ2EU](https://youtu.be/CxkXkj0WBbY?si=KVppCOuNHouV5GwD))
- Day 7 iThome 文章：[10402339](https://ithelp.ithome.com.tw/articles/10402339)

## Day 8 收錄內容

- `day08/article.md`：發布後 Audit Trail、Incident Pack 與事故復原完整文章來源
- `day08/example-incident-pack/`：可執行的事件驗證、JSONL Audit Trail 與 Incident Pack 範例，含 5 項測試
- `day08/diagrams/incident_lifecycle.mmd`：發布後健康檢查、事故處理與回滾流程圖原始檔
- `day08/autocut-deck/`：Day 8 AutoCut HTML deck、theme、slides.js、template.json
- Day 8 影片：`day08-cc-final.mp4`（正式交付檔，不納入 Git repository）
- Day 8 封面：`day08-fish-tts-thumbnail.jpg`
- Day 8 字幕：`day08-fish-tts-subtitles.srt`（YouTube 繁體中文 CC）
- Day 8 YouTube 影片：[nZ_tF2Hj754](https://www.youtube.com/watch?v=nZ_tF2Hj754)
- Day 8 iThome 文章：待發布

## Day 8 影片 QA

- AutoCut deck：8 張投影片逐張擷取，旁白 notes 保留作 TTS／SRT 來源但不顯示在影片畫面
- FFprobe：H.264 1920x1080 25fps / AAC mono 44.1kHz / 214.584s
- Full decode：exit 0
- Audio sanity：mean -16.8 dB、max -1.5 dB
- Contact sheet：8 張投影片中點影格全部通過視覺檢查
- Subtitles：25 個 SRT cues，上傳為 `zh-TW` YouTube CC，status `serving`

## Day 9 收錄內容

- `day09/article.md`：Learning Pack、證據回流與人工核准完整文章來源
- `day09/example-learning-pack/`：可執行的 Learning Pack 驗證器與 idempotent 套用範例
- `day09/diagrams/learning_feedback_loop.mmd`：事故證據回流至下一次 Context 的流程圖原始檔
- `day09/autocut-deck/`：Day 9 AutoCut HTML deck、theme、slides.js、template.json
- Day 9 YouTube 影片：[gKLJz1hjh5o](https://www.youtube.com/watch?v=gKLJz1hjh5o)
- Day 9 iThome 文章：[10402613](https://ithelp.ithome.com.tw/articles/10402613)

## Day 9 影片 QA

- AutoCut deck：8 張投影片逐張擷取，旁白 notes 保留作 TTS／SRT 來源但不顯示在影片畫面
- FFprobe：H.264 1920x1080 25fps / AAC / 153.124s
- Full decode：exit 0
- Audio sanity：mean -29.7 dB、max -11.4 dB，非靜音且未 clipping
- Contact sheet：8 張投影片中點影格全部通過視覺檢查
- Subtitles：8 個 SRT cues，上傳為 `zh-TW` YouTube CC，status `serving`

## Day 10 收錄內容

- `day10/PLAN.md`：Freshness Gate 題綱、驗收條件與媒體交付 gates
- `day10/article.md`：Context 新鮮度、source commit、learning expiry 與 scope 完整文章來源
- `day10/example-freshness-gate/`：可執行的唯讀 Freshness Gate 與 6 項測試
- `day10/diagrams/freshness_gate_flow.mmd`：執行前 freshness 檢查流程圖原始檔
- `day10/diagrams/freshness_states.mmd`：Fresh／Stale／Drifted／Blocked 狀態圖原始檔
- Day 10 YouTube 影片：[Jt_6iBtCFjs](https://www.youtube.com/watch?v=Jt_6iBtCFjs)
- Day 10 字幕：`zh-TW` YouTube CC，status `serving`
- Day 10 iThome 文章：[10402721](https://ithelp.ithome.com.tw/articles/10402721)

## Day 11 收錄內容

- `day11/PLAN.md`：Change Budget 題綱、驗收條件與媒體交付 gates
- `day11/article.md`：路徑、命令、檔案數與 diff 預算的完整文章來源
- `day11/example-change-budget/`：可執行的唯讀 Change Budget Gate、fixtures 與 8 項測試
- `day11/diagrams/change_budget_flow.mmd`：Change Budget 執行流程圖原始檔
- `day11/diagrams/change_budget_states.mmd`：Budget 狀態圖原始檔
- Day 11 YouTube 影片：[sWSrKdn0Hr4](https://www.youtube.com/watch?v=sWSrKdn0Hr4)
- Day 11 字幕：`zh-TW` YouTube CC，53 個單行 cues，status `serving`
- Day 11 iThome 文章：[10402889](https://ithelp.ithome.com.tw/articles/10402889)

## Day 12 收錄內容

- `day12/PLAN.md`：Evidence Binding 題綱、驗收條件與媒體交付 gates
- `day12/article.md`：把 diff、tests、review 綁到同一個 intent 與 observation 的完整文章來源
- `day12/example-evidence-binding/`：可執行的唯讀 Evidence Binding Gate 與 8 項測試
- `day12/diagrams/evidence_binding_flow.mmd`：Evidence Binding 流程圖原始檔
- `day12/diagrams/evidence_binding_states.mmd`：Evidence Binding 狀態圖原始檔
- Day 12 影片：待上傳（本機交付檔，不納入 Git repository）
- Day 12 字幕：待上傳（獨立 UTF-8 SRT）
- Day 12 iThome 文章：待發布

## Day 13 收錄內容

- `day13/PLAN.md`：Acceptance Coverage 題綱、驗收條件與媒體交付 gates
- `day13/article.md`：逐項檢查 acceptance、測試結果與 evidence link 的完整文章來源
- `day13/example-acceptance-coverage/`：可執行的唯讀 Acceptance Coverage Gate 與 9 項測試
- `day13/diagrams/acceptance_coverage_flow.mmd`：Acceptance Coverage 流程圖原始檔
- `day13/diagrams/acceptance_coverage_states.mmd`：Acceptance Coverage 狀態圖原始檔
- Day 13 影片：待上傳（本機交付檔，不納入 Git repository）
- Day 13 字幕：待上傳（獨立 UTF-8 SRT）
- Day 13 iThome 文章：待發布

## Day 15 收錄內容

- `day15/PLAN.md`：Reproducibility Gate 題綱、驗收條件與媒體交付 gates
- `day15/article.md`：source、input、environment、toolchain、dependency lock 與 output identity 的完整文章來源
- `day15/example-reproducibility-gate/`：可執行的唯讀 Reproducibility Gate、fixtures 與 10 項測試
- `day15/diagrams/reproducibility_gate_flow.mmd`：重現前提與 output identity 流程圖原始檔
- `day15/diagrams/reproducibility_states.mmd`：DECLARED、REPRODUCIBLE 與 BLOCKED 狀態圖原始檔
- Day 15 影片：待上傳（本機 clean MP4，不納入 Git repository）
- Day 15 字幕：待上傳（獨立 UTF-8 SRT）
- Day 15 iThome 文章：待發布

## Day 29 收錄內容

- `day29/PLAN.md`：Rollout Promotion Gate 題綱、promotion identity、五段 gate 與交付條件
- `day29/article.md`：觀察窗、metrics、cohort policy、approval、handoff 與 idempotency 的完整文章來源
- `day29/example-rollout-promotion-gate/`：可執行的唯讀 promotion readiness gate、fixtures 與 11 項測試
- `day29/diagrams/rollout_promotion_gate_flow.mmd`：observe → metrics → policy → approval → handoff 流程圖原始檔
- `day29/diagrams/rollout_promotion_states.mmd`：promotion state machine 原始檔
- Day 29 影片：待上傳（本機 clean MP4，不納入 Git repository）
- Day 29 字幕：待上傳（獨立 UTF-8 SRT，zh-TW CC）
- Day 29 iThome 文章：待發布

## Day 29 本機 Media QA

- Canonical deck：`ithome-promo-runs/day29/deck/index.html`（local producer workspace）
- Deck provenance：官方 `claude-code-slides` 0.6.0 CLI scaffold、`claude-editorial`、HTML
- FFprobe：H.264 1920x1080、25fps、AAC mono 44.1kHz、169.08s
- Full decode：video/audio exit 0；volume mean -29.3 dB、peak -12.2 dB
- Capture：10 張 HTML slide frames，1920x1080，notes/chrome 隱藏
- Fish TTS：10 個 scene segments，全部非空且可測 duration
- Subtitles：60 個 UTF-8 SRT cues，單 cue 單行、單調且落在 MP4 duration 內
- Visual QA：10 張 midpoint contact sheet 與 final MP4 full-resolution frame 通過獨立視覺檢查
- Status：本機 artifacts verified；YouTube／iThome／GitHub 均未執行外部寫入

## 使用方式

SVG 圖表可直接用瀏覽器開啟，也能轉成 PNG／JPG 後放入技術文章。文章中的範例著重：

1. 把模糊自然語言轉成 Given／When／Then。
2. 將 `OPEN` 未決項目留給團隊確認，不讓模型自行猜測。
3. 由 Codex 在明確邊界內實作、測試並交付可重現證據。
4. 用版本化 Context Pack 與 Plan Contract，讓多代理從同一份可驗證事實開始工作。
