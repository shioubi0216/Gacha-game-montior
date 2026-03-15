# Gacha Game Monitor 🎮

一個用於管理手遊日常任務與體力追蹤的桌面應用程式。

## 專案簡介

身為一個同時玩多款手遊的玩家，每天需要登入多個遊戲消耗體力、完成日常任務。
這個工具幫助你：
- 追蹤每個遊戲的上次登入時間
- 計算體力恢復進度
- 提醒你哪些遊戲還沒完成日常

## 支援遊戲

- 蔚藍檔案 (Blue Archive)
- 鳴潮 (Wuthering Waves)
- FGO 台服
- 妮姬 台服 (NIKKE)
- 星穹鐵道 (Honkai: Star Rail)

## 技術棧

- **語言**: Python 3.14
- **UI 框架**: Flet (Flutter-based)
- **架構**: MVC (Model-View-Controller)
- **資料儲存**: JSON (本地)

## 專案結構

```
gachagamemonitor/
├── src/
│   ├── main.py              # 程式進入點
│   ├── models/              # 資料模型層
│   │   └── game.py          # 遊戲資料類別
│   ├── views/               # 視圖層
│   │   └── game_card.py     # 遊戲卡片元件
│   ├── controllers/         # 控制層
│   │   └── game_controller.py
│   └── services/            # 服務層
│       └── process_monitor.py  # 進程監控（未來功能）
├── data/
│   └── games.json           # 遊戲資料儲存
├── assets/                  # 靜態資源
├── requirements.txt
└── README.md
```

## 安裝與執行

```bash
# 1. 建立虛擬環境
python -m venv .venv

# 2. 啟動虛擬環境 (Windows)
.\.venv\Scripts\Activate

# 3. 安裝相依套件
pip install -r requirements.txt

# 4. 執行程式
python src/main.py
```

## 開發進度

詳見 [PROGRESS.md](./PROGRESS.md)

## 作者

shiou - 資管系畢業生，目標成為資工人才 💪
