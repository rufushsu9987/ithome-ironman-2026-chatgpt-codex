# Day 30 Speaker Notes：Delivery Contract

## Scene 1 — 30 天最後一關不是按發布

30 天走到最後，需求、程式、測試、deck、影片和字幕可能都已經完成。但「檔案都在」不等於「可以安全交付」。今天用 Delivery Contract，把同一輪 run 的證據、交付物和責任交接綁在一起。

## Scene 2 — delivery ready 不等於 published

Delivery Contract Gate 是唯讀 readiness check。它只回答這一包能不能交給下一個責任邊界，不發布文章、不上傳影片，也不替 release owner 做公開決策。Ready 和 Published 必須是兩個不同狀態。

## Scene 3 — 六個局部綠燈還不夠

Context、Plan、Execute、Verify、Review、Deliver 六段都要存在，而且要屬於同一份 contract identity。若只是把六個 true 串起來，可能把另一輪 run 的測試、文章或影片拼成假的成功。

## Scene 4 — 先固定 Delivery Contract identity

本日要求 series、Day、contract、run、source digest、evidence digest、policy、owner 和 target 都對得上。任何欄位漂移都先回報 blocked identity，不拿別輪的綠燈補洞。

## Scene 5 — 順序也是契約

固定順序是 context、plan、execute、verify、review、deliver。每個 stage 都有自己的成功狀態、相同 digest 和 audit event。順序錯了，表示責任鏈沒有真的完成，即使每個 key 都存在也不能放行。

## Scene 6 — 有檔案不等於有 QA evidence

Artifact inventory 不只記檔名。每個必要交付物都要有 verified 狀態、同一份 digest、非零 bytes 和可回讀的相對路徑。影片、字幕、deck 和 media QA 不能只靠檔名叫 final 來證明。

## Scene 7 — 本機 ready 不能冒充 public

Producer 的責任停在本機 artifacts verified。外部發布要交給 release lane，經過自己的授權、idempotency 和公開 read-back。Observation 裡保留 release_lane 這個邊界，就是避免自動化把檔案存在誤報成世界已改變。

## Scene 8 — Runnable example 只回報 reason code

Python 範例只讀 intent 和 observation，不連線、不發布、不修改輸入。它會檢查六段 stage、artifact inventory、release boundary 和 handoff，成功時回傳 delivery_ready，失敗時回傳可以修正的 reason code。

## Scene 9 — 三個角色要分開

Producer 產出證據，Reviewer 回讀 QA，Release owner 才負責外部變更。delivery_ready 是可以交接，不是 published。把責任分開，才能知道哪一段失敗、哪一段需要重新驗證。

## Scene 10 — 把 30 天收成閉環

最後記住三件事：ready 不等於 published；所有證據要屬於同一份 contract identity；外部結果一定要靠授權與公開 read-back 證明。AI 工程的完成，不是按下最多按鈕，而是留下下一個人能安全接手的證據。
