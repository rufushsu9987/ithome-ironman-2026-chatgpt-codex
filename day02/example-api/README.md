# Day 2：訂單 CSV 匯出範例

這個可執行範例將文章中的驗收規格落成 Python 程式，不依賴第三方套件。

## 已實作的規格

| 驗收條件 | 程式行為 |
| --- | --- |
| 非租戶管理員建立匯出 | 回傳 403，不建立工作並留下拒絕稽核事件 |
| 跨租戶操作 | 回傳 403，不加入工作佇列 |
| 日期超過 31 天 | 回傳 422 並指出 `date_range` |
| 合法請求 | 回傳 202 與 `job_id`，將工作加入佇列 |
| 相同 `request_id` 重送 | 回傳相同 `job_id`，不重複建立工作 |
| Worker 執行工作 | 僅讀取指定租戶與日期區間的訂單 |
| 匯出完成 | 寫入物件儲存並產生 600 秒下載網址 |
| 建立、拒絕與完成 | 寫入結構化稽核事件 |

## 執行測試

```bash
cd day02/example-api
python3 -m unittest -v
```

本範例刻意使用記憶體內 Repository、Queue 與 Object Storage，讓驗收規則可以快速執行。實務專案可將這些介面替換為 PostgreSQL、SQS／Service Bus、S3／Blob Storage，而不改變核心驗收行為。
