# 開發進度追蹤 📋

> 這個檔案用來追蹤專案開發進度，同時作為 AI 協作時的記憶輔助。
> 每次 commit 後更新此檔案。

---

## 🧠 專案概要（給未來的自己/AI）

**專案目標**：一個桌面應用程式，用於追蹤多款手遊的體力恢復狀態和上次登入時間。

**技術棧**：
- Python 3.14 + Flet 0.80+ (Flutter-based UI)
- MVC 架構（Model-View-Controller）
- 資料儲存：JSON（`data/games.json`, `data/settings.json`）
- 系統托盤：pystray + Pillow
- 系統通知：plyer

**目前狀態**：Phase 2 完成！體力記錄、系統托盤、通知功能已實作。

---

## 🎮 遊戲數據（已確認正確）

| 遊戲 | 體力名稱 | 上限 | 恢復速度 |
|------|----------|------|----------|
| 蔚藍檔案 | AP | 240 | 6 分鐘/1 點 |
| 鳴潮 | 結晶波片 | 240 | 6 分鐘/1 點 |
| FGO 台服 | AP | 140 | 5 分鐘/1 點 |
| 妮姬 台服 | 體力 | 24 | 60 分鐘/1 點 |
| 星穹鐵道 | 開拓力 | 300 | 6 分鐘/1 點 |

---

## 🎯 開發里程碑

### Phase 1: MVP - 桌面啟動器 ✅ 完成
- [x] 環境建置 (Python, venv, Flet)
- [x] 專案結構建立 (MVC 架構)
- [x] 建立 Game Model 類別
- [x] 建立 GameCard 元件
- [x] 實作遊戲啟動功能
- [x] 實作上次登入時間記錄
- [x] JSON 資料持久化
- [x] 修正遊戲體力數據
- [x] 推送到 GitHub

### Phase 2: 體力計算器 + 通知系統 ✅ 完成
- [x] 新增「記錄體力」按鈕與輸入對話框
- [x] 顯示預估當前體力（根據時間自動計算）
- [x] 顯示預計體力全滿時間
- [x] 體力滿時發送 Windows 系統通知
- [x] 背景執行緒持續檢查體力
- [x] 系統托盤功能（最小化到托盤）
- [x] 托盤右鍵選單（顯示視窗 / 退出程式）
- [x] 關閉視窗行為選擇（記住用戶偏好）
- [x] 用戶設定持久化（settings.json）
- [x] Flet 0.80+ API 適配

### Phase 3: 自動化與進階功能（待開發）
- [ ] 自動偵測遊戲 Process（開啟/關閉）
- [ ] 自動偵測已安裝遊戲路徑
- [ ] 星穹鐵道 HoYoLab API 串接（可選）
- [ ] 視窗置底模式（桌面小工具）

### Phase 4: 發布（待開發）
- [ ] 打包成 .exe（PyInstaller）
- [ ] 製作安裝程式或免安裝版
- [ ] 撰寫完整 README 和使用說明

---

## 📁 專案結構

```
gachagamemonitor/
├── src/
│   ├── main.py                     # 程式進入點
│   ├── models/
│   │   └── game.py                 # 遊戲資料類別
│   ├── views/
│   │   └── game_card.py            # 遊戲卡片 UI 元件
│   ├── controllers/
│   │   └── game_controller.py      # 業務邏輯控制器
│   └── services/
│       ├── settings_service.py     # 用戶設定管理
│       ├── notification_service.py # 系統通知服務
│       ├── tray_service.py         # 系統托盤服務
│       └── process_monitor.py      # 進程監控（Phase 3）
├── data/
│   ├── games.json                  # 遊戲資料
│   └── settings.json               # 用戶設定
├── assets/
├── requirements.txt
├── PROGRESS.md
└── README.md
```

---

## 📝 開發日誌

### 2025-01-31 (Day 1)

**Session 1 - 環境建置與 MVP**
- [x] 安裝 VS Code、Python 3.14.2
- [x] 建立虛擬環境、安裝 Flet
- [x] 建立 MVC 專案結構
- [x] 完成 MVP 介面（5 個遊戲卡片）
- [x] 實作遊戲啟動與路徑設定功能
- [x] 初始化 Git，推送到 GitHub

**Session 2 - 體力記錄功能**
- [x] 修正遊戲體力數據（蔚藍240、星穹300、妮姬24/60min）
- [x] 新增「記錄體力」按鈕
- [x] 實作體力輸入對話框
- [x] 實作體力自動計算與預估滿時間

**Session 3 - 系統托盤與通知（踩坑最多的一段）**
- [x] 安裝 pystray、Pillow、plyer
- [x] 實作 SettingsService（用戶設定持久化）
- [x] 實作 NotificationService（背景體力檢查 + 系統通知）
- [x] 實作 TrayService（系統托盤 + 右鍵選單）
- [x] 實作關閉視窗行為選擇對話框
- [x] 解決 Flet 0.80+ API 變更問題（詳見下方踩坑紀錄）

---

## 🐛 踩坑紀錄 & 解決方案

### 坑 1: Flet 版本 API 不相容

**問題**：使用了舊版 Flet 的 API，導致各種 AttributeError

**錯誤訊息**：
```
AttributeError: module 'flet.controls.alignment' has no attribute 'top_left'
AttributeError: module 'flet' has no attribute 'animation'
```

**解決方案**：

| 舊 API | 新 API (Flet 0.80+) |
|--------|---------------------|
| `ft.alignment.top_left` | 移除，不用漸層背景 |
| `ft.animation.Animation()` | 移除動畫效果 |
| `ft.Colors.with_opacity(0.3, color)` | `ft.Colors.WHITE10` |
| `ft.margin.only(bottom=20)` | `margin=20` 或 `ft.Margin(...)` |
| `ft.padding.only(left=32)` | `ft.Padding(left=32, top=0, right=0, bottom=0)` |
| `ft.ElevatedButton` | `ft.Button` |
| `ft.app(target=main)` | `ft.app(main)` |

---

### 坑 2: 視窗關閉事件 `e.data` 是 None

**問題**：點擊視窗 X 按鈕，`page.window.on_event` 的 `e.data` 是 `None`

**除錯方式**：建立 `test_close.py` 測試檔，印出所有事件屬性

**發現**：Flet 0.80+ 改用 `e.type` 而非 `e.data`

**解決方案**：
```python
async def handle_window_event(e):
    if "CLOSE" in str(e.type):  # 用 e.type 檢查
        # 處理關閉邏輯
```

---

### 坑 3: `page.window.destroy()` 是 async 函數

**問題**：呼叫 `destroy()` 沒反應

**錯誤訊息**：
```
RuntimeWarning: coroutine 'Window.destroy' was never awaited
```

**解決方案**：
```python
# 錯誤
page.window.destroy()

# 正確
await page.window.destroy()
```

所有呼叫 `destroy()` 的函數都要改成 `async def`。

---

### 坑 4: pystray callback 在不同執行緒

**問題**：從托盤點「顯示視窗」，視窗沒有出現

**原因**：pystray 的 callback 是在背景執行緒執行的，直接呼叫 `page.update()` 不會生效

**解決方案**：使用 `page.run_task()` 讓 Flet 在正確的執行緒中執行

```python
# 錯誤
TrayService(
    on_show=show_window_from_tray,  # 直接傳函數
)

# 正確
TrayService(
    on_show=lambda: page.run_task(show_window_from_tray),  # 用 run_task 包裝
)
```

同時 `show_window_from_tray` 要改成 `async def`。

---

### 坑 5: DeprecationWarning 警告

**問題**：執行時出現一堆黃色警告

**說明**：這些只是「棄用警告」，不影響功能，但表示未來版本會移除這些 API

**處理方式**：
- `app() is deprecated` → 可以改用 `ft.run(main)`，但目前 `ft.app(main)` 還能用
- `ElevatedButton is deprecated` → 改用 `ft.Button`

---

## 💡 學到的重要觀念

### Debug 技巧
1. **善用 print()**：在關鍵位置加入 `print(f"[DEBUG] ...")` 來追蹤程式流程
2. **印出物件屬性**：`print(dir(e))` 可以看到物件有哪些屬性可用
3. **建立測試檔案**：遇到問題時，建立最小化的測試檔案來隔離問題

### 多執行緒 UI 更新
- 背景執行緒不能直接更新 UI
- 需要用框架提供的方法（如 `page.run_task()`）回到主執行緒

### API 版本相容性
- 使用新版本框架時，先查閱官方文件確認 API 變更
- 遇到 AttributeError 先懷疑是版本問題

---

## 💡 想法暫存區

- 未來可以加入 Discord Webhook 通知
- 考慮用 SQLite 取代 JSON（當資料變複雜時）
- 可以做成 System Tray 常駐程式 ✅ 已完成
- 支援自訂遊戲（讓用戶新增不在預設清單的遊戲）
- 支援多語言介面

---

## 📚 學習資源

- [Flet 官方文件](https://flet.dev/docs/)
- [Flet 0.80 更新日誌](https://flet.dev/blog/) - 查看 API 變更
- [Python asyncio 教學](https://docs.python.org/3/library/asyncio.html)
- [psutil 文件](https://psutil.readthedocs.io/) (用於 Process 監控)
- [PyInstaller 打包教學](https://pyinstaller.org/)
- [pystray 文件](https://pystray.readthedocs.io/)
- [plyer 文件](https://plyer.readthedocs.io/)

---

## 🔗 相關連結

- GitHub Repo: https://github.com/shioubi0216/Gacha-game-montior
