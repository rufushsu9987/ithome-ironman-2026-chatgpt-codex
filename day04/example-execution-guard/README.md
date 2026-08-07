# Day 4 Execution Guard

這個標準函式庫範例把「agent 可以怎麼執行」寫成可驗證的 Execution Contract，並在 Codex 或其他執行代理開始修改前 fail closed。

範例本身不會啟動 Codex，也不會修改工作目錄；它只檢查：

- Context ID、版本與 approved source commit 是否一致。
- task 是否在自己的 `.worktrees/<task-id>`，而不是直接寫入主工作目錄。
- 修改路徑是否落在白名單，且沒有碰到唯讀／敏感路徑。
- 驗證命令是否避免網路、發布、強制刪除與高風險 Git 操作。
- timeout、停在 drift、network disabled、人工 Review 等停止條件是否明確。

## 執行

```bash
python3 -m unittest -v
python3 execution_guard.py policy.json plan.json
```

預期輸出包含：

```text
EXECUTION_OK context=orders-export version=3 tasks=1
TASK_OK id=export-api worktree=.worktrees/export-api paths=2 timeout=600s network=disabled
VERIFY_COMMAND python3 -m unittest -v tests/export/test_api.py
STOP_CONDITIONS context_drift,path_violation,timeout,verification_failure
```

這是教學用的最小 gate，不是完整的 sandbox、容器或作業系統權限系統。正式環境仍應搭配 CI、分支保護、容器／OS 層級權限、秘密管理與人工 Review。
