# Day 12｜測試通過就算是這次變更的證據嗎？用 Evidence Binding 綁住 diff、測試與 review

## 題綱與定位

Day 10 用 Freshness Gate 確認 Context、source commit 與 Learning 仍然有效；Day 11 用 Change Budget 確認 agent 執行中沒有超出原本核准的路徑、命令、檔案數與 diff 上限。下一個缺口是：即使每份證據看起來都是真的，也可能把不同 intent、不同 commit 或不同執行的 diff、測試與 review 拼在一起。

本日引入 Evidence Binding：把同一個 `intent_id`、`context_id`、`source_commit` 與 `observation_id` 綁在 diff、測試結果、review 與 artifact 上，讓系統能回答「這份證據是不是屬於這一次變更」，而不只回答「這份測試曾經通過」。

## 暫定標題

Day 12｜測試通過就算是這次變更的證據嗎？用 Evidence Binding 綁住 diff、測試與 review

## 生活情境與痛點

交付前桌上有三份資料：一份 diff、一份測試報告、一個已核准的 review。每一份單獨看都合理，但測試報告可能來自上一個 commit，review 可能核准的是另一個 intent。若只看檔名或「PASS」字樣，最後會把別人的證據當成這次工作的證據。

## 核心方法

- `Evidence Identity`：每份證據都帶有 `intent_id`、`context_id`、`source_commit` 與 `observation_id`。
- `Evidence Bundle`：把 diff、tests、review 與 artifact metadata 放進同一個可驗證 bundle。
- `Required Evidence`：明確列出本次驗收需要的 evidence kind，不接受缺一份的「大概完整」。
- `fail-closed`：任何身分不一致、路徑越界、測試未通過、review 尚未核准或 artifact 綁錯，都回報穩定 reason code。
- `read-only`：Gate 只驗證 runner 已產生的證據，不重跑測試、不修改 diff、不把舊報告改成新報告。

## Given／When／Then 驗收條件

1. Given diff、tests、review 都帶有相同 intent、context、source commit 與 observation，When 執行 Evidence Binding Gate，Then 回報 `allowed=true`、`state=bound`。
2. Given 測試報告的 `source_commit` 與 intent 不同，When 執行 Gate，Then 回報 `source_commit_mismatch`，不能因測試狀態是 `passed` 而放行。
3. Given diff 含有不在 Change Budget allowlist 的路徑，When 執行 Gate，Then 回報 `path_out_of_scope:<path>`。
4. Given test status 不是 `passed` 或缺少 result digest，When 執行 Gate，Then 回報 `test_not_passed` 或 `test_result_digest_missing`。
5. Given review status 不是 `approved`，When 執行 Gate，Then 回報 `review_not_approved`，不把 pending 當成核准。
6. Given required evidence kind 缺少 diff、tests 或 review 任一項，When 執行 Gate，Then 回報 `required_evidence_missing:<kind>`。
7. Given artifact 使用重複的 `artifact_id` 或綁到不同 source commit，When 執行 Gate，Then fail-closed 並指出具體 artifact。
8. Given相同 intent 與 evidence 重試兩次，When 執行 Gate，Then 兩次報告相同，輸入物件不被修改。

## 可執行範例

`example-evidence-binding/` 使用 Python 標準函式庫實作唯讀 `evaluate_binding(intent, evidence)`，輸出 deterministic JSON 報告。測試涵蓋成功綁定、identity mismatch、path 越界、測試失敗、review pending、缺少 required evidence、artifact 綁錯與 read-only retry。

## 圖解與影片場景

- `diagrams/evidence_binding_flow.mmd`：從 Freshness／Budget 通過，到建立 evidence bundle、逐項綁定，再交給 Verify 的流程。
- `diagrams/evidence_binding_states.mmd`：COLLECTING、BOUND、BLOCKED_IDENTITY、BLOCKED_MISSING、READY_VERIFY 狀態。
- HTML deck 8 張：錯接證據的生活情境、四個 binding identity、Evidence Bundle、fail-closed、reason code、測試證據與責任鏈收束。

## 媒體交付 gates

- Deck：可編輯、自洽的 1920×1080 HTML、8 slides、8 組 speaker notes，notes 不出現在畫面。
- TTS：Fish Audio per-scene MP3，依實際 audio duration 產生 timing 與 SRT。
- Video：clean H.264/AAC MP4、1920×1080、25 fps，不燒字幕。
- QA：companion tests、py_compile、Node syntax、AutoCut／deck strict check、FFprobe、full video/audio decode、volume、SRT timing、8 張 midpoint contact sheet、至少一張 full-resolution frame、Media QA manifest 全部 PASS。
- 外部：YouTube／字幕／iThome／GitHub 均維持待每日 Release lane；Producer 不執行任何外部發布或同步。
