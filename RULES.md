# RULES.md - OpenCleaner

> **項目名稱**: OpenCleaner
> **最後更新**: 2026-02-04
> **描述**: macOS App Uninstaller (Pro Max)

這份文件是本項目的「憲法」。Agent 在執行任何任務前，必須優先閱讀並遵守此文件。

## 🚨 核心鐵律 (CRITICAL RULES)

> **⚠️ Agent 必須在每次任務開始時確認：**
> "✅ 我已閱讀 RULES.md，並將嚴格遵守技術債預防措施。"

### ❌ 絕對禁止 (Prohibitions)
- **禁止** 在根目錄創建代碼文件 → 必須放在 `src/` 對應模塊下。
- **禁止** 創建 `main_v2.py`, `utils_new.py` 這種命名 → 必須重構原文件。
- **禁止** 憑空寫代碼 → 必須先搜索 (`grep/find`) 是否有現成代碼可復用。
- **禁止** 硬編碼 (Hardcoding) 敏感信息 (API Keys) → 使用 `.env`。

### ✅ 強制執行 (Mandatory)
- **Git 備份**: 每次 Commit 後，**必須** 自動執行 `git push origin main` (或由 Hook 觸發)。
- **子代理 (Sub-agents)**: 遇到複雜任務 (>3步) 或長時間運行的任務，**必須** 派發子代理執行。
- **單一數據源**: 每個功能點只能有一個權威實現 (Single Source of Truth)。

## 📁 項目結構 (Structure)

本項目遵循 **Vibe Coding 標準結構**：

```
[PROJECT_ROOT]/
├── RULES.md               # 本文件 (項目憲法)
├── README.md              # 項目說明
├── .gitignore             # Git 忽略配置
├── src/                   # 源代碼 (核心邏輯)
│   ├── main/              # 主程序入口
│   └── utils/             # 工具函數
├── tests/                 # 測試代碼
├── docs/                  # 文檔
└── output/                # 運行輸出 (日誌/數據)
```

## 🛠️ 開發工作流 (Workflow)

### 1. 啟動任務
*   閱讀 `RULES.md`。
*   檢查當前 `git status`。

### 2. 編寫代碼 (Vibe Mode)
*   **Search**: 使用 `grep` 查找相關代碼。
*   **Plan**: 在腦海中構建修改計劃。
*   **Edit**: 執行精確修改。

### 3. 交付成果
*   運行測試 (如果有的話)。
*   `git commit -m "feat: 描述改動"`
*   `git push` (確保雲端備份)。

---
**Code with Flow, Build with Soul.** 🎸
