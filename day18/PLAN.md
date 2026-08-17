# Day 18｜Release Candidate 通過就真的上線了嗎？用 Deployment Verification Gate 核對實際狀態

## 本日定位

Day 17 的 Release Candidate Gate 已經確認 candidate 有正確的 target、release window、required checks、rollback 與人工核准。但「releasable」仍然只是「可以交給 release owner 做發布決策」；它不是部署完成的證明。

本日引入 Deployment Verification Gate。它接在部署動作之後，唯讀比對實際觀察到的 deployment、rollout、replica、health、smoke 與 traffic serving 狀態，並確認所有狀態仍然屬於同一個 candidate、artifact digest、config digest 與 run。Gate 只回報 `deployment_verified` 或具體的 `blocked` reason，不部署、不切流量、不替人類宣稱服務已上線。

## 本日驗收

| Given | When | Then |
| --- | --- | --- |
| deployment available、rollout complete、identity 一致、replica 全 ready、required checks 全 passed、traffic serving 同一 candidate | 執行 Gate | `allowed=true`、`state=deployment_verified`、`reasons=[]` |
| candidate、digest、version、config 或 target 漂移 | 執行 Gate | fail-closed 並回報具體 identity reason |
| rollout 未完成、deployment 不 available 或 replica 不足 | 執行 Gate | 回報 rollout／availability／replica reason |
| check 缺少、skipped、pending 或 failed | 執行 Gate | 回報 `check_missing:*` 或 `check_not_passed:*` |
| traffic 仍服務舊 candidate | 執行 Gate | 回報 `serving_candidate_mismatch` |
| 同一輸入重試兩次 | 執行 Gate | JSON 一致且輸入不被修改 |

## Runnable example

`example-deployment-verification-gate/` 使用 Python 標準函式庫實作唯讀 `evaluate_deployment(intent, observed)`：

- 驗證 intent、run、candidate、source、input、environment 與 target。
- 驗證 deployment availability、rollout、artifact／config digest、version 與 replica health。
- 驗證 required checks 與 traffic serving identity。
- 不部署、不更新 route、不修改輸入，也不把結果寫回外部平台。

## 圖解與影片場景

- `diagrams/deployment_verification_gate_flow.mmd`：部署後的唯讀驗證流程。
- `diagrams/deployment_verification_states.mmd`：觀察、blocked 與 verified 狀態。
- HTML deck 10 張：問題、identity、rollout、replica、checks、traffic、範例、證據鏈與收束。

## 媒體交付 gates

- Deck：官方 `claude-code-slides` 0.6.0、`claude-editorial`、HTML；1920×1080、10 slides、每頁 layout marker 與 speaker notes。
- TTS：Fish Audio per-scene MP3，實測 audio duration 產生 timing 與 SRT；不得 silent。
- Video：clean H.264/AAC MP4、1920×1080、25 fps，不燒字幕。
- QA：companion tests、fixture CLI、Python／JavaScript syntax checks、官方 deck checker、FFprobe、full video/audio decode、volume、SRT timing、10 張 midpoint contact sheet、final-MP4 full-resolution frame、視覺檢查與 strict Media QA 全部 PASS。
- 外部：YouTube／字幕／iThome／GitHub 維持待後續 Release lane；Producer 不執行任何外部發布。
