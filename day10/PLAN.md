# Day 10 製作計畫

## 題目假設

Day 2～9 已經把需求、Context、執行、Verify、Deliver、Release、Incident 與 Learning 串成一條責任鏈。Day 9 把 approved learning 帶回下一次 Context；Day 10 接著處理一個尚未解決的問題：approved 不代表永遠有效，Context 也可能因為 source commit、時間、scope 或 learning 狀態改變而過期。

## 暫定標題

Day 10｜Learning Pack 放進 Context 就安全了嗎？用 Freshness Gate 擋住過期規則

## 生活情境

事故已經結案，團隊也核准一條 Learning Pack 規則。兩週後，新的 agent 讀到舊 Context，卻沒有注意 Repository 已換了 source commit、learning 已過期，或這次修改根本不在原本的 scope。它仍然回報「依照已核准規則執行」，但使用的是過時前提。

## 痛點

- `approved` 被誤解成永久有效。
- Context 的 source commit 與目前 checkout 不一致，卻繼續執行。
- Learning Pack 的有效期限、證據與 scope 沒有在執行前重查。
- 同一個 Context 套用到不同服務，造成規則污染。

## 核心方法

建立一個唯讀的 Context Freshness Gate，在 Codex 開始修改前檢查：

1. `context_id` 與本次 request 相同。
2. Context 的 `source_commit` 與目前 Repository commit 相同。
3. Context 尚未超過 `max_age_hours`。
4. 每筆 learning 都是 `approved`／`applied`、有 evidence、未過期且未 retired。
5. 本次 request 的 paths 都落在 learning 的 scope 內。

Gate 只產生可追溯報告，不替人類更新 Context、不自動延長期限，也不把舊資料改寫成新鮮資料。

## 可驗收條件

- Given context_id、source commit、時間與 learning scope 都符合，When 執行 Freshness Gate，Then 回報 `allowed=true`。
- Given current source commit 不同，When 執行 Gate，Then 回報 `allowed=false` 並列出 commit mismatch。
- Given Context 超過 max_age_hours，When 執行 Gate，Then 阻擋，不因 learning 仍是 approved 而放行。
- Given learning 是 retired、已過期或缺少 evidence，When 執行 Gate，Then 阻擋並指出具體 learning_id。
- Given request path 超出 scope 或 context_id 不同，When 執行 Gate，Then 阻擋，避免跨服務污染。
- Given 相同輸入重試兩次，When 執行 Gate，Then 兩次報告相同且輸入不被修改。

## 可執行範例

`day10/example-freshness-gate/` 使用 Python 標準函式庫實作唯讀 gate、JSON fixture 與 `unittest` 測試。測試涵蓋成功、source commit 漂移、Context 過期、learning 失效、證據缺失、跨 Context、scope 越界與 deterministic retry。

## 圖解

- `diagrams/freshness_gate_flow.mmd`：從 Context 讀取到允許／阻擋的流程。
- `diagrams/freshness_states.mmd`：Fresh、Stale、Blocked、Approved learning 的狀態邊界。

## 影片場景

1. 過期 Context 仍被當成最新規則的生活情境。
2. Freshness Gate 的五個檢查點。
3. source commit 漂移與時間過期的阻擋分支。
4. Learning Pack 的 evidence、status、expiry 與 scope。
5. 唯讀、fail-closed、deterministic 的設計。
6. 真實測試輸出與 fixture 結果。
7. 從 Learning Pack 回到 Context 前的責任鏈。
8. 結語：approved 是前提，不是永久通行證。

## 交付 gates

- canonical `article.md` 第一行只有標題，其餘為 Markdown 正文。
- companion example 完整 `python3 -m unittest -v`、`py_compile` 與 fixture CLI 執行成功。
- HTML deck 固定 1920×1080，8 張投影片，speaker notes 與畫面分離。
- Fish Audio per-scene TTS 使用 AutoCut manifest，音訊 duration 以 ffprobe 為準。
- 每張投影片獨立擷取，notes 隱藏，生成 exact-count midpoint contact sheet。
- clean H.264/AAC MP4 固定 25 fps，字幕為獨立 UTF-8 SRT，不燒入畫面。
- FFprobe、full decode、音量、SRT timing、視覺檢查與 copied-artifact re-probe 全部 PASS。
- `上傳資訊.md` 明確記錄 `youtube_status=待上傳`、`ithome_status=草稿已存`、`github_status=待同步`；不含 OAuth、API key 或假想 watch URL。
- iThome 只建立正確系列／Day 10 Ironman draft，保存後回讀，不按發布。
