"""
Game Model - 遊戲資料類別

這個模組定義了遊戲的資料結構，包含：
- 遊戲基本資訊（名稱、執行檔路徑、圖示）
- 體力系統設定（最大體力、恢復速率）
- 狀態追蹤（上次登入時間、當時體力）

設計原則：
- 使用 dataclass 簡化類別定義
- 使用 Type Hints 增加程式碼可讀性
- 將資料與邏輯分離（體力計算放在這裡，UI 顯示放在 View）
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
import json


@dataclass
class Game:
    """代表一個手遊的資料模型"""
    
    # 基本資訊
    id: str                          # 唯一識別碼，例如 "fgo", "nikke"
    name: str                        # 顯示名稱，例如 "FGO 台服"
    exe_path: Optional[str] = None   # 執行檔路徑，None 表示尚未設定
    icon_path: Optional[str] = None  # 圖示路徑
    
    # 體力系統設定
    max_stamina: int = 100                    # 最大體力
    stamina_per_minute: float = 0.2           # 每分鐘恢復體力 (預設 5 分鐘回 1 點)
    stamina_name: str = "體力"                # 體力的遊戲內名稱（AP、體力、開拓力等）
    
    # 登入提醒
    login_reminder_hours: Optional[float] = None  # None = 不提醒, 例如 20.0 = 20 小時後提醒

    # API 整合
    api_enabled: bool = False                      # 是否支援 API 即時查詢
    api_last_sync: Optional[datetime] = None       # 上次 API 同步時間

    # 狀態追蹤
    last_login: Optional[datetime] = None     # 上次登入時間
    last_stamina: Optional[int] = None        # 上次登入時的體力值
    
    def get_current_stamina(self) -> Optional[int]:
        """
        根據上次記錄的體力和經過時間，計算當前預估體力值
        
        Returns:
            預估的當前體力值，如果沒有歷史記錄則返回 None
        """
        if self.last_login is None or self.last_stamina is None:
            return None
        
        elapsed_minutes = (datetime.now() - self.last_login).total_seconds() / 60
        recovered = int(elapsed_minutes * self.stamina_per_minute)
        current = min(self.last_stamina + recovered, self.max_stamina)
        
        return current
    
    def get_time_until_full(self) -> Optional[timedelta]:
        """
        計算距離體力全滿還需要多少時間
        
        Returns:
            timedelta 物件，如果已滿或無資料則返回 None
        """
        current = self.get_current_stamina()
        if current is None or current >= self.max_stamina:
            return None
        
        stamina_needed = self.max_stamina - current
        minutes_needed = stamina_needed / self.stamina_per_minute
        
        return timedelta(minutes=minutes_needed)
    
    def get_time_since_login(self) -> Optional[str]:
        """
        取得距離上次登入經過多少時間（人類可讀格式）
        
        Returns:
            例如 "3 小時前"、"剛剛"、"昨天"
        """
        if self.last_login is None:
            return None
        
        elapsed = datetime.now() - self.last_login
        
        if elapsed.total_seconds() < 60:
            return "剛剛"
        elif elapsed.total_seconds() < 3600:
            minutes = int(elapsed.total_seconds() / 60)
            return f"{minutes} 分鐘前"
        elif elapsed.total_seconds() < 86400:
            hours = int(elapsed.total_seconds() / 3600)
            return f"{hours} 小時前"
        else:
            days = int(elapsed.total_seconds() / 86400)
            return f"{days} 天前"
    
    def is_login_overdue(self) -> bool:
        """檢查是否已超過提醒時間未登入"""
        if self.login_reminder_hours is None or self.last_login is None:
            return False
        elapsed_hours = (datetime.now() - self.last_login).total_seconds() / 3600
        return elapsed_hours >= self.login_reminder_hours

    def record_login(self, stamina: Optional[int] = None) -> None:
        """
        記錄一次登入
        
        Args:
            stamina: 當前體力值（可選）
        """
        self.last_login = datetime.now()
        if stamina is not None:
            self.last_stamina = stamina
    
    def to_dict(self) -> dict:
        """轉換為字典格式，用於 JSON 儲存"""
        return {
            "id": self.id,
            "name": self.name,
            "exe_path": self.exe_path,
            "icon_path": self.icon_path,
            "max_stamina": self.max_stamina,
            "stamina_per_minute": self.stamina_per_minute,
            "stamina_name": self.stamina_name,
            "login_reminder_hours": self.login_reminder_hours,
            "api_enabled": self.api_enabled,
            "api_last_sync": self.api_last_sync.isoformat() if self.api_last_sync else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "last_stamina": self.last_stamina,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Game":
        """從字典建立 Game 物件"""
        last_login = None
        if data.get("last_login"):
            last_login = datetime.fromisoformat(data["last_login"])
        
        api_last_sync = None
        if data.get("api_last_sync"):
            api_last_sync = datetime.fromisoformat(data["api_last_sync"])

        return cls(
            id=data["id"],
            name=data["name"],
            exe_path=data.get("exe_path"),
            icon_path=data.get("icon_path"),
            max_stamina=data.get("max_stamina", 100),
            stamina_per_minute=data.get("stamina_per_minute", 0.2),
            stamina_name=data.get("stamina_name", "體力"),
            login_reminder_hours=data.get("login_reminder_hours"),
            api_enabled=data.get("api_enabled", False),
            api_last_sync=api_last_sync,
            last_login=last_login,
            last_stamina=data.get("last_stamina"),
        )


# 預設遊戲設定
# 這些數值來自各遊戲的實際體力系統
DEFAULT_GAMES: list[dict] = [
    {
        "id": "blue_archive",
        "name": "蔚藍檔案",
        "max_stamina": 240,
        "stamina_per_minute": 1/6,  # 6 分鐘回 1 點
        "stamina_name": "AP",
        "login_reminder_hours": 20.0,
    },
    {
        "id": "wuthering_waves",
        "name": "鳴潮",
        "max_stamina": 240,
        "stamina_per_minute": 1/6,  # 6 分鐘回 1 點
        "stamina_name": "結晶波片",
        "login_reminder_hours": 20.0,
    },
    {
        "id": "fgo",
        "name": "FGO 台服",
        "max_stamina": 140,  # 依等級不同，這是大約值
        "stamina_per_minute": 1/5,  # 5 分鐘回 1 點
        "stamina_name": "體力",
        "login_reminder_hours": 20.0,
    },
    {
        "id": "nikke",
        "name": "妮姬",
        "max_stamina": 24,
        "stamina_per_minute": 1/60,  # 6 分鐘回 1 點
        "stamina_name": "基地點數",
        "login_reminder_hours": 20.0,
    },
    {
        "id": "star_rail",
        "name": "星穹鐵道",
        "max_stamina": 300,
        "stamina_per_minute": 1/6,  # 6 分鐘回 1 點
        "stamina_name": "開拓力",
        "login_reminder_hours": 20.0,
        "api_enabled": True,  # 支援 HoYoLab API 即時查詢
    },
    {
        "id": "pgr",
        "name": "戰雙帕彌什",
        "max_stamina": 240,
        "stamina_per_minute": 1/6,  # 6 分鐘回 1 點
        "stamina_name": "體力",
        "login_reminder_hours": 20.0,
    },
]
