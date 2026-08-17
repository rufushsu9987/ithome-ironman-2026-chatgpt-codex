# Day 14｜驗收證據都齊了，真的能交付嗎？用 Traceability Gate 把需求、變更與發布決策串起來

## 本日定位

Day 13 的 Acceptance Coverage 已經回答「每個 acceptance 是否都有通過且連回 evidence」。本日再補最後一段：這些 evidence 是否屬於同一個 change，且是否真的有一個可追溯的 release decision。核心方法是 Traceability Gate，將 intent、acceptance、change、artifact 與 release approval 綁成一條可回查的鏈。

## 生活情境

一個匯出功能的測試全綠，三個 acceptance 也都有測試 log。準備發布時，才發現其中一份 log 來自昨天的 commit，review 看的是另一個 change，release approval 也沒有記錄由誰做出。每份資料看起來都是真的，但放在一起不能證明這次發布安全。

## 核心痛點

- 測試證據有了，卻不知道它證明的是哪一個 change。
- acceptance、diff、review 與 release approval 可能來自不同 source commit。
- 有人把 `allowed=true` 當成發布命令，讓驗證器越權。
- 阻擋理由太模糊，下一個人不知道該補哪一份證據。

## 本日方法

Traceability Gate 是唯讀、deterministic、fail-closed 的檢查器：

1. 從 Change Intent 固定 `intent_id`、`context_id`、`source_commit`、`acceptance_ids`、`change_ids` 與 `release_owner`。
2. 逐項檢查 acceptance result 是否通過，且 evidence artifact 反向連回同一個 acceptance。
3. 逐項檢查 change 是否存在，且 change 與 artifact 互相連結。
4. 檢查所有 artifact 與 release approval 的 source commit 是否一致。
5. 檢查 approval 狀態與負責人，不代替人類按下發布。

## 可驗收條件

- Given 所有 acceptance 都是 `passed`，When 每個 result 都連到反向綁定的 artifact，Then `all_acceptances_traceable=true`。
- Given intent 宣告 `CH-01`，When trace bundle 沒有該 change，Then 回報 `change_missing:CH-01`。
- Given change 指向 artifact，When artifact 沒有反向列出該 change，Then 回報 `change_artifact_not_linked:<change>:<artifact>`。
- Given evidence、release approval 與 intent 的 commit 不同，When 執行 Gate，Then fail-closed 並列出對應 mismatch reason。
- Given approval 尚未完成或 approval owner 不同，When 執行 Gate，Then 回報 `release_not_approved` 或 `release_owner_mismatch`。
- Given相同輸入重試兩次，When執行Gate，Then兩次報告一致且輸入沒有被修改。

## Runnable example

`example-traceability-gate/` 使用 Python 標準函式庫，輸入 `fixtures/intent.json` 與 `fixtures/trace.json`，輸出 deterministic JSON。範例涵蓋：完整 trace、缺少 acceptance、failed acceptance、錯誤反向 link、缺少 change、commit 漂移、未核准 release、未知 artifact 與 read-only/idempotent 行為。

## 圖解

- `diagrams/traceability_gate_flow.mmd`：從 intent freeze 到 release decision 的資料流。
- `diagrams/traceability_gate_states.mmd`：TRACEABLE、BLOCKED_* 與重新產生證據的狀態轉移。

## Deck 與影片

- 8 張 16:9、1920×1080 HTML slides。
- 官方 `claude-code-slides` 0.6.0 scaffold，template `claude-editorial`。
- 每頁有 `data-layout` 與 speaker notes；notes 是 TTS／SRT 來源，capture 時隱藏。
- 每頁獨立 HTML capture，依 Fish Audio 實測 duration 組成固定 25 fps clean H.264/AAC MP4。
- 字幕為獨立 UTF-8 SRT，不燒錄進畫面。

## 本機完成 gates

- article、PLAN、example、fixtures、diagrams 存在且無 secrets／本機絕對路徑。
- `python3 -m unittest -v`、`py_compile`、fixture CLI 均以實際輸出驗證。
- 官方 deck checker exit 0、errors 空、warnings 空，slides／notes／layouts／unique layouts 對應。
- per-scene TTS 非空且 ffprobe duration > 0；manifest `tts.used=true`。
- 8 張 capture 均為 1920×1080、active=1、notesVisible=false。
- 最終 MP4 通過 FFprobe、full video/audio decode、volume、SRT timing、midpoint contact sheet、full-resolution frame 與 strict Media QA。
- `上傳資訊.md` 只記錄待上傳 metadata；Producer 不執行 iThome、YouTube、GitHub 外部寫入。
