# Day 21｜證據都通過就能發布嗎？用 Human Approval Gate 把不可逆動作交回人類

## 本日定位

Day 20 的 SLO Impact Gate 確認這次變更沒有超過使用者可靠性門檻，但「證據 clear」仍不等於「可以執行不可逆動作」。本日補上 Human Approval Gate：在 deployment、migration、公開發布或權限變更前，唯讀驗證核准是否綁定同一個 intent、run、candidate、source、input、environment 與 target，且具備正確角色、有效期限、範圍與人數。

Gate 只回答「這份核准證據是否足以交給 release owner 進行下一步」；不部署、不發布、不切流、不 rollback，也不替人類做最後決策。

## 文章主線

1. 從「所有 dashboard 都綠了，但按下發布後就不能回頭」的生活情境開始。
2. 分開說明 automated evidence clear 與 human authorization 的責任。
3. 先固定 change identity，避免拿別的 run 或 candidate 的核准來套用。
4. 要求必要 evidence 的 state 與 digest 都和 intent 宣告一致。
5. 驗證 approver role、minimum approvals、distinct approvers、approval age 與 scope。
6. 將 rejected、expired、self-approval、scope drift 與 count shortfall 寫成 deterministic reason code。
7. 以標準函式庫 Python 範例產生唯讀、可重跑的核准判斷。
8. 把 Day 10–21 串成從 context 新鮮度走到「人類授權不可逆動作」的證據鏈。

## Given／When／Then 驗收條件

1. Given intent 宣告必要 evidence、最少兩位 release owner、15 分鐘有效期限，observation 綁定同一 candidate 與 target，兩位不同 approver 都核准且 scope 正確，When 執行 Human Approval Gate，Then 回報 `allowed=true`、`state=approval_eligible`、`reasons=[]`。
2. Given required evidence 缺少或 state 不符，When 執行 Gate，Then 回報 `evidence_missing:<name>` 或 `evidence_state_mismatch:<name>`。
3. Given evidence digest 與 intent 不一致，When 執行 Gate，Then 回報 `evidence_digest_mismatch:<name>`。
4. Given approval decision 為 `rejected`，When 執行 Gate，Then 回報 `approval_not_approved:<approver>`，且有效核准數不足時回報 `approval_count_shortfall`。
5. Given approval 超過 max age，When 執行 Gate，Then 回報 `approval_expired:<approver>`。
6. Given approver role 不符、scope 不符或 approver 是 proposer，When 執行 Gate，Then fail-closed 並輸出對應 reason code。
7. Given approver 重複或有效核准人數不足，When 執行 Gate，Then 回報 `approver_not_distinct` 或 `approval_count_shortfall`。
8. Given intent 與 observation 的 source、input、environment、run 或 target 漂移，When 執行 Gate，Then fail-closed，不把漂亮的核准紀錄套到另一個變更。
9. Given 相同 intent 與 observation 重試兩次，When 執行 Gate，Then 兩次 JSON 報告一致且輸入物件沒有被修改。

## Runnable example

`example-human-approval-gate/` 使用 Python 標準函式庫實作唯讀 `evaluate_approval(intent, observed)`：

- 比對 change identity。
- 比對 required evidence 的 state 與 digest。
- 驗證 approval policy：人數、角色、有效期限、範圍、distinct 與禁止 self-approval。
- 回傳 deterministic reason code，不執行 deployment、publish、rollback 或權限變更。

## 圖解與影片場景

- `diagrams/human_approval_gate_flow.mmd`：從 automated evidence clear 到核准適用性的流程圖。
- `diagrams/human_approval_states.mmd`：DECLARED、EVIDENCE_BOUND、AWAITING_APPROVAL、BLOCKED_APPROVAL、APPROVAL_ELIGIBLE 與 HUMAN_ACTION 狀態圖。
- HTML deck 10 張：不可逆風險、automated evidence 與 human authorization 的差異、identity、evidence binding、approval policy、reason code、唯讀範例、Day 10–21 證據鏈與收束。

## 媒體交付 gates

- Deck：先由官方 `claude-code-slides` 0.6.0、`claude-editorial`、HTML CLI scaffold，再填內容；1920×1080、10 slides、每頁 layout marker 與 speaker notes。
- TTS：Fish Audio per-scene MP3，實測 audio duration 產生 timing 與 SRT；不得 silent。
- Video：clean H.264/AAC MP4、1920×1080、25 fps，不燒字幕。
- QA：companion tests、fixture CLI、Python／JavaScript syntax checks、官方 deck checker、FFprobe、full video/audio decode、volume、SRT timing、10 張 midpoint contact sheet、final-MP4 full-resolution frame、視覺檢查與 strict Media QA 全部 PASS。
- 外部：YouTube／字幕／iThome／GitHub 維持待後續 Release lane；Producer 不執行任何外部發布。
