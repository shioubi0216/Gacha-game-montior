# GachaGameMonitor — Claude Code 專案說明書

## 專案簡介
追蹤多款手遊體力回復與每日登入狀態的 Windows 桌面工具。
目標使用者：同時玩多款手遊的玩家，需要掌握各遊戲體力狀態。

## 技術棧
- **Python 3.14**（虛擬環境：`.venv/`）
- **Flet 0.80+**（Flutter-based UI，有 breaking API 變更，注意相容性）
- **pystray + Pillow**：系統托盤
- **plyer**：Windows 通知
- **psutil**：行程監控（偵測遊戲啟動/關閉）
- 架構：**MVC**，資料持久化用 **JSON**

## ⚠️ Flet 0.80+ 重要注意事項
- 使用 `ft.Button` 而非舊版 `ElevatedButton`
- window close event 用 `e.type` 判斷，不是 `e.data`
- `destroy()` 必須是 async function
- pystray callback 跨執行緒更新 UI 需用 `page.run_task()`
- 詳細踩坑紀錄見 `PROGRESS.md`

## 目錄結構
```
src/
├── main.py                         # 入口，串接所有層
├── models/game.py                  # 資料模型 + 體力計算
├── controllers/game_controller.py  # 商業邏輯、JSON 讀寫
├── views/game_card.py              # Flet UI 卡片（固定 height=190）
└── services/
    ├── notification_service.py     # Windows 通知（plyer）
    ├── settings_service.py         # 設定持久化
    ├── tray_service.py             # 系統托盤（pystray）
    └── process_monitor.py          # 進程監控（threading + psutil）
data/
├── games.json    # 使用者資料（gitignore，勿覆蓋）
└── settings.json
```

## 追蹤的遊戲（6款）
| ID | 名稱 | 體力名 | 上限 | 回復速率 |
|----|------|--------|------|----------|
| blue_archive | 蔚藍檔案 | AP | 240 | 1/6 min |
| wuthering_waves | 鳴潮 | 結晶波片 | 240 | 1/6 min |
| fgo | FGO 台服 | 體力 | 140 | 1/5 min |
| nikke | 妮姬 | 基地點數 | 24 | 1/60 min |
| star_rail | 星穹鐵道 | 開拓力 | 300 | 1/6 min |
| pgr | 戰雙帕彌什 | 體力 | 240 | 1/6 min |

## 開發慣例
- 語言：**繁體中文**（UI 文字、commit message、註解皆用繁中）
- `data/games.json` 已 gitignore，修改前先確認使用者資料
- 新增遊戲：同時更新 `models/game.py` 的 `DEFAULT_GAMES` 與 `data/games.json`
- UI 卡片固定高度 190px，文字設 `no_wrap=True` + `ELLIPSIS` 防止撐高

## 開發慣例（進程監控）
- ProcessMonitor 用 threading（與 NotificationService 一致），不用 async
- 遊戲關閉時透過 `page.run_task()` 橋接到 UI 執行緒彈出對話框
- Lambda closure 用 `gid=game.id` 避免迴圈變數捕獲問題
- `exe_path` 未設定的遊戲不會被監控，手動按鈕仍可用
- 登入提醒預設 20 小時，每款遊戲可獨立設定 `login_reminder_hours`
- `page.run_task()` 要傳 **coroutine function**，不是 coroutine object（用 `_make_exit_callback` 工廠函式）
- 模擬器遊戲：exe_path 支援帶參數格式（如 `MuMuNxDevice.exe -p com.package.name`）
- MuMu Player 偵測用 `MuMuNxDevice.exe`（非 `MuMuNxMain.exe`），關閉模擬器視窗才觸發

## 開發進度
- ✅ Phase 1：MVP 啟動器
- ✅ Phase 2：體力追蹤、系統托盤、Windows 通知、Flet 0.80+ 相容
- ✅ Phase 3：進程監控、關閉遊戲自動彈窗記錄體力、登入提醒通知、過期卡片紅框
- 🔮 Phase 4：PyInstaller 打包成 .exe

## 未來優化方向（按優先度）

### 高價值（建議優先）
- **HoYoLab API 整合**：星穹鐵道即時體力查詢（endpoint: `bbs-api-os.hoyolab.com/game_record/hkrpg/api/note`），需使用者提供 cookie/token
- **PyInstaller 打包 .exe**：讓朋友不裝 Python 也能用
- **自訂遊戲支持**：UI 讓使用者自行新增遊戲（名稱、體力上限、回復速率）

### 中等價值
- Discord Webhook 通知（推送到頻道）
- SQLite 取代 JSON（歷史紀錄功能時遷移）
- 桌面 Widget 模式（always-on-top 精簡視窗）
- 自動偵測已安裝遊戲路徑

### 探索性
- 多語言介面（i18n）
- 體力消耗歷史圖表
- 每日登入行事曆視覺化
