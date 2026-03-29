"""
Settings Service - 用戶設定管理

處理用戶偏好設定的讀取和儲存，包括：
- 關閉視窗時的行為（最小化到托盤 / 直接關閉）
- 是否啟用通知
- 其他用戶偏好
"""

import json
from pathlib import Path
from typing import Any


class SettingsService:
    """用戶設定服務"""
    
    DEFAULT_SETTINGS = {
        "close_to_tray": None,  # None = 尚未詢問, True = 最小化, False = 關閉
        "notifications_enabled": True,
        "check_interval_seconds": 60,  # 檢查體力的間隔
        "process_monitor_enabled": True,  # 是否啟用進程監控
        "login_reminder_enabled": True,  # 是否啟用登入提醒
        # HoYoLab API 設定
        "hoyolab_enabled": False,
        "hoyolab_ltuid": None,   # ltuid_v2 值
        "hoyolab_ltoken": None,  # ltoken_v2 值
        "hoyolab_interval": 600,  # 查詢間隔秒數（預設 10 分鐘）
    }
    
    def __init__(self, settings_path: str = "data/settings.json"):
        self.settings_path = Path(settings_path)
        self.settings = self._load_settings()
    
    def _load_settings(self) -> dict:
        """載入設定檔"""
        if self.settings_path.exists():
            try:
                with open(self.settings_path, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    # 合併預設值（處理新增的設定項）
                    return {**self.DEFAULT_SETTINGS, **saved}
            except (json.JSONDecodeError, IOError):
                return self.DEFAULT_SETTINGS.copy()
        return self.DEFAULT_SETTINGS.copy()
    
    def _save_settings(self) -> None:
        """儲存設定檔"""
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.settings_path, "w", encoding="utf-8") as f:
            json.dump(self.settings, f, ensure_ascii=False, indent=2)
    
    def get(self, key: str, default: Any = None) -> Any:
        """取得設定值"""
        return self.settings.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """設定並儲存"""
        self.settings[key] = value
        self._save_settings()
    
    @property
    def close_to_tray(self) -> bool | None:
        """關閉視窗時是否最小化到托盤"""
        return self.settings.get("close_to_tray")
    
    @close_to_tray.setter
    def close_to_tray(self, value: bool) -> None:
        self.set("close_to_tray", value)
    
    @property
    def notifications_enabled(self) -> bool:
        """是否啟用通知"""
        return self.settings.get("notifications_enabled", True)
    
    @notifications_enabled.setter
    def notifications_enabled(self, value: bool) -> None:
        self.set("notifications_enabled", value)

    @property
    def process_monitor_enabled(self) -> bool:
        """是否啟用進程監控"""
        return self.settings.get("process_monitor_enabled", True)

    @process_monitor_enabled.setter
    def process_monitor_enabled(self, value: bool) -> None:
        self.set("process_monitor_enabled", value)

    @property
    def login_reminder_enabled(self) -> bool:
        """是否啟用登入提醒"""
        return self.settings.get("login_reminder_enabled", True)

    @login_reminder_enabled.setter
    def login_reminder_enabled(self, value: bool) -> None:
        self.set("login_reminder_enabled", value)

    # ===== HoYoLab API 設定 =====

    @property
    def hoyolab_enabled(self) -> bool:
        return self.settings.get("hoyolab_enabled", False)

    @hoyolab_enabled.setter
    def hoyolab_enabled(self, value: bool) -> None:
        self.set("hoyolab_enabled", value)

    @property
    def hoyolab_ltuid(self) -> str | None:
        return self.settings.get("hoyolab_ltuid")

    @hoyolab_ltuid.setter
    def hoyolab_ltuid(self, value: str | None) -> None:
        self.set("hoyolab_ltuid", value)

    @property
    def hoyolab_ltoken(self) -> str | None:
        return self.settings.get("hoyolab_ltoken")

    @hoyolab_ltoken.setter
    def hoyolab_ltoken(self, value: str | None) -> None:
        self.set("hoyolab_ltoken", value)

    @property
    def hoyolab_interval(self) -> int:
        return self.settings.get("hoyolab_interval", 600)

    @hoyolab_interval.setter
    def hoyolab_interval(self, value: int) -> None:
        self.set("hoyolab_interval", value)
