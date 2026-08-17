# Day 26｜Evidence Access Gate

## 本日定位

Day 25 用 Evidence Retention Gate 確認 incident 結案後的 evidence 仍存在、可回讀、期限沒有過期。但「留住」不等於「所有人都能讀」。Day 26 延伸到 retained evidence 的讀取邊界：誰提出請求、為了什麼目的、可以看哪些 evidence 與欄位、有效多久，以及誰對這次讀取做過核准。

## 核心主張

1. `retention_ready` 只代表證據還在，不代表 access 已被授權。
2. `Evidence Access Gate` 只做唯讀判斷，不讀取內容、不發放 token、不呼叫 archive 或 IAM API。
3. identity、role、purpose、field scope、時間、approval 與 audit 必須綁在同一個 digest。
4. `access_eligible` 只代表請求具備交給授權系統或人類 owner 的前提，仍不等於資料已被讀取。

## 驗收條件

- Given access intent 與 observation 的 incident、closeout、run、digest、environment、target 完全一致，requester role／purpose 合法，requested evidence 與 fields 沒有超過 allowlist，期限有效，approval scope／年齡正確，audit record 已綁定同一 digest，When 執行 Gate，Then 輸出 `allowed=true`、`state=access_eligible`、`reasons=[]`。
- Given 任一 identity 漂移，When 執行 Gate，Then 先輸出 `blocked_identity` 與欄位差異，不繼續假設其他條件成立。
- Given role、purpose、evidence name 或 field scope 超出 intent，When 執行 Gate，Then fail-closed 並回報具體 reason code。
- Given requested／expiry 時間缺少、未來或超過 policy window，When 執行 Gate，Then 阻擋 access eligibility。
- Given approval 沒有精確綁定 requester、scope、target、digest，或已過期，When 執行 Gate，Then 阻擋，不把別人的核准搬過來。
- Given audit record 缺少 event id、digest 或 recorded time，When 執行 Gate，Then 阻擋，不讓不可追蹤的讀取通過。
- Given相同輸入重試兩次，When 執行 Gate，Then 結果一致且輸入沒有被修改。

## 交付與 QA

- `article.md`：白話說明 retention 與 access 的差別、流程、reason code 與責任邊界。
- `example-evidence-access-gate/`：Python 標準函式庫 runnable example、fixtures、10 項測試。
- `diagrams/`：access gate flow 與狀態圖 Mermaid 原始檔。
- `NARRATION.md`：10 個 scene，對應 10 張 HTML slides。
- Deck：官方 `claude-code-slides` 0.6.0、`claude-editorial`、HTML scaffold 後填入 Day 26 內容。
- Media：Fish Audio per-scene TTS、逐頁 1920×1080 capture、固定 25 fps clean H.264/AAC MP4、獨立 UTF-8 SRT。
- QA：官方 deck checker、companion tests、fixture CLI、Python／JavaScript syntax checks、FFprobe、full decode、volume、SRT timing、10 張 midpoint contact sheet、final MP4 full-resolution frame、獨立 visual review 與 delivery-root reconciliation。

## 外部邊界

本 Producer 只產製與驗證本機檔案；iThome、YouTube、OAuth、Chrome、CuaDriver、GitHub commit／push／PR 皆留給後續 Release lane。
