# OpenCleaner 🧹
**macOS App Uninstaller (Pro Max) | macOS 應用卸載神器**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/platform-macOS-lightgrey.svg)]()
[![Built with Flet](https://img.shields.io/badge/Built%20with-Flet-blue)](https://flet.dev)

[English](#english) | [中文說明](#中文說明)

---

<a name="english"></a>
##  English

**OpenCleaner** is a free, open-source, and modern app uninstaller for macOS. It helps you remove applications along with their hidden leftover files (caches, preferences, support files) to free up disk space.

### ✨ Features
- **Modern UI**: Dark mode, real app icons, and smooth animations (powered by Flet).
- **Deep Scan**: Finds leftovers in `~/Library` (Caches, Preferences, Application Support).
- **Safe Delete**: Moves files to **Trash** instead of permanent deletion (no regrets!).
- **Smart Filters**: Quickly find **Large (>1GB)** or **Unused (>30 days)** apps.
- **Batch Mode**: Select and delete multiple apps at once.
- **Privacy First**: Runs entirely locally. No internet required.

### 📥 Download
Download the latest `.dmg` installer from the **[Releases Page](../../releases)**.

### ⚡ Quick Start (Source Code)
If you prefer running from source:

1. **Clone the repo**
   ```bash
   git clone https://github.com/Garyko0730/OpenCleaner.git
   cd OpenCleaner
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run**
   ```bash
   python3 src/main/app.py
   ```

---

<a name="中文說明"></a>
##  中文說明

**OpenCleaner** 是一款免費、開源且界面現代的 macOS 應用卸載工具。它可以幫你徹底刪除應用程序及其隱藏的殘留文件（緩存、配置、支持文件），釋放寶貴的磁盤空間。

### ✨ 核心功能
- **現代界面**: 完美支持暗黑模式，顯示真實應用圖標，操作流暢。
- **深度掃描**: 自動挖掘 `~/Library` 下的關聯垃圾文件（如緩存、偏好設置）。
- **安全刪除**: 所有文件僅 **移動到廢紙簍**，防止誤刪，隨時可還原。
- **智能過濾**: 一鍵篩選 **大型應用 (>1GB)** 或 **長期未用 (>30天)** 的應用。
- **批量卸載**: 支持多選模式，一次性清理多個應用。
- **隱私安全**: 代碼完全開源，本地運行，不聯網。

### 📥 下載安裝
請前往 **[Releases 頁面](../../releases)** 下載最新的 `.dmg` 安裝包。

### ⚡ 源碼運行
如果你是開發者，也可以直接運行源代碼：

1. **克隆倉庫**
   ```bash
   git clone https://github.com/Garyko0730/OpenCleaner.git
   cd OpenCleaner
   ```

2. **安裝依賴**
   ```bash
   pip install -r requirements.txt
   ```

3. **啟動**
   ```bash
   python3 src/main/app.py
   ```

---

## 🤝 Credits
**Co-created by [Gary Ko](https://github.com/Garyko0730) & Jarvis 🤖**  
*Built with ❤️ using OpenClaw Vibe Coding.*
