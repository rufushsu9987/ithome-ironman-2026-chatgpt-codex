# Day 15｜Reproducibility Gate

## 本日定位

Day 14 的 Traceability Gate 已經把 intent、acceptance、change、artifact 與 release approval 串成責任鏈。本日再往前追問一個很實際的問題：明天要不要能夠重跑，不能只靠「當時曾經通過」的描述。Reproducibility Gate 將 source commit、輸入摘要、環境識別、toolchain、dependency lock 與輸出 artifact 綁在同一筆 run 上，避免結果看似完整，卻無法重現。

## 文章主線

1. 從「昨天成功、今天重跑失敗」的情境開始。
2. 說明可追溯（traceable）與可重現（reproducible）的差別。
3. 固定 Change Intent 的 source、input 與 environment identity。
4. 驗證 run 的 toolchain、dependency lock 與輸出 artifact。
5. 以唯讀、deterministic、fail-closed 的 Python Gate 示範 reason code。
6. 說明 Gate 不會替人類補環境、改 digest 或宣告發布。
7. 把 Day 10–15 串成從前提有效性到重現證據的責任鏈。

## Runnable example

`example-reproducibility-gate/` 使用 Python 標準函式庫完成：

- intent 與 run 的 context、source commit、input digest 比對。
- toolchain 與 dependency lock 的精確比對。
- expected outputs 是否存在、ready，且反向帶有相同 identity。
- missing、mismatch、not-ready 與 unknown output 的 deterministic reason code。
- 相同輸入重試時報告一致，而且不修改輸入物件。

## Given／When／Then

- Given intent 與 run 的 source、input、environment、toolchain、lock 都一致，And 每個 expected output 都 ready 且帶回相同 identity，When 執行 Gate，Then `allowed=true`、`state=reproducible`。
- Given run 使用另一個 source commit，When 執行 Gate，Then 回報 `source_commit_mismatch`。
- Given輸入摘要不同，When執行 Gate，Then回報 `input_digest_mismatch`，不接受「檔名一樣」作為證據。
- Given toolchain 或 dependency lock 不同，When 執行 Gate，Then 回報對應 mismatch reason。
- Given expected output 缺少或尚未 ready，When 執行 Gate，Then fail-closed 並指出缺口。
- Given相同 intent 與 run 重試兩次，When執行 Gate，Then兩次 JSON 報告一致且輸入未被修改。

## Deck／影片交付 contract

- 官方來源：`claude-code-slides-source/bin/codex-slides.mjs`（Producer 本機以固定絕對路徑執行）。
- 官方版本：`0.6.0`；format：`html`；template：`claude-editorial`。
- Canonical deck：10 張 16:9、1920×1080 HTML slides；每頁有自己的 `data-layout` 與 speaker notes。
- Visual source：canonical HTML deck；每頁獨立 capture，notes 隱藏，禁止以單一長 Playwright recording 作為 release source。
- TTS：Fish Audio per-scene MP3，duration 以 `ffprobe` 實測，manifest 必須記錄 `tts.used=true`。
- Video：clean H.264/AAC、1920×1080、固定 25 fps；字幕為獨立 UTF-8 SRT，不燒入畫面。
- QA：官方 deck checker、Node/Python syntax、companion tests、fixture CLI、每頁 capture dimensions／active／notes、FFprobe、full decode、volume、SRT timing、exact-count midpoint contact sheet、final-MP4 full-resolution frame、strict Media QA。
- 外部邊界：YouTube、iThome、GitHub 均維持待 Release lane；本輪不執行外部寫入。

## 產物與檢查清單

- [x] `article.md`、`PLAN.md`、example、fixtures、兩份 Mermaid 圖完成。
- [x] companion tests、`py_compile`、fixture CLI 真實執行成功。
- [x] canonical deck 由官方 CLI scaffold 衍生，metadata／manifest／QA provenance 一致。
- [x] 官方 checker exit 0、errors 空、warnings 空。
- [x] 10 組 Fish TTS 非空且每組 duration > 0，combined audio 非靜音。
- [x] 10 張 HTML capture 都是 1920×1080、active=1、notes 不可見。
- [x] final MP4 通過 25 fps、H.264/AAC、full decode、volume、SRT timing。
- [x] contact sheet 有 10 個 midpoint，另有 final MP4 full-resolution frame，且已做視覺檢查。
- [x] `Media QA`、`上傳資訊.md` 與 checkpoint 只記錄本機 artifact；不含 secret、credential、假造外部 URL。
