# 開發進度追蹤 📋

> 這個檔案用來追蹤專案開發進度，取代複雜的任務管理工具。
> 每次開發前先看這裡，結束後更新狀態。

---

## 🎯 專案里程碑

### Phase 1: MVP - 桌面啟動器 (目標：1-2 週)
- [x] 環境建置 (Python, venv, Flet)
- [x] 專案結構建立 (MVC 架構)
- [ ] 建立 Game Model 類別
- [ ] 建立 GameCard 元件
- [ ] 實作遊戲啟動功能
- [ ] 實作上次登入時間記錄
- [ ] JSON 資料持久化

### Phase 2: 體力計算器 (目標：第 3 週)
- [ ] 新增體力輸入介面
- [ ] 實作各遊戲體力恢復公式
- [ ] 顯示預計體力全滿時間
- [ ] 體力滿時通知功能

### Phase 3: 自動化與進階功能 (目標：第 4-5 週)
- [ ] 自動偵測遊戲 Process 關閉
- [ ] 星穹鐵道 HoYoLab API 串接
- [ ] 視窗置底 (桌面小工具模式)

---

## 📝 開發日誌

### 2025-01-31 (Day 1)
**完成事項：**
- [x] 安裝 VS Code 與 Python 3.14.2
- [x] 建立虛擬環境
- [x] 安裝 Flet
- [x] 建立專案結構

**學習筆記：**
- 虛擬環境 (venv) 的用途：隔離專案的套件，避免不同專案的相依性衝突
- MVC 架構：Model 處理資料、View 處理顯示、Controller 處理邏輯

**明日目標：**
- [ ] 完成 Game Model 類別
- [ ] 測試第一個 Flet 視窗

---

## 🐛 已知問題 / 待解決

| 問題 | 狀態 | 備註 |
|------|------|------|
| (暫無) | - | - |

---

## 💡 想法暫存區

- 未來可以加入 Discord Webhook 通知
- 考慮用 SQLite 取代 JSON（當資料變複雜時）
- 可以做成 System Tray 常駐程式

---

## 📚 學習資源

- [Flet 官方文件](https://flet.dev/docs/)
- [Python asyncio 教學](https://docs.python.org/3/library/asyncio.html)
- [psutil 文件](https://psutil.readthedocs.io/) (用於 Process 監控)
