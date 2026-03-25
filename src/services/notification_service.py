"""
Notification Service - 系統通知服務

負責發送 Windows 系統通知，包括：
- 體力滿時通知
- 背景檢查體力狀態
"""

import threading
import time
from typing import Callable, List, Set
from datetime import datetime
from datetime import datetime

# plyer 用於跨平台通知
try:
    from plyer import notification
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False
    print("警告: plyer 未安裝，通知功能將無法使用")


class NotificationService:
    """系統通知服務"""
    
    def __init__(self, check_interval: int = 60):
        """
        初始化通知服務
        
        Args:
            check_interval: 檢查間隔（秒），預設 60 秒
        """
        self.check_interval = check_interval
        self._running = False
        self._thread: threading.Thread | None = None
        self._games = []
        self._notified_games: Set[str] = set()  # 已經通知過的遊戲（避免重複通知）
        self._on_check_callback: Callable | None = None
    
    def set_games(self, games: list) -> None:
        """設定要監控的遊戲列表"""
        self._games = games
    
    def on_check(self, callback: Callable) -> None:
        """設定每次檢查時的 callback（用於更新 UI）"""
        self._on_check_callback = callback
    
    def start(self) -> None:
        """啟動背景檢查"""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._check_loop, daemon=True)
        self._thread.start()
        print("通知服務已啟動")
    
    def stop(self) -> None:
        """停止背景檢查"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        print("通知服務已停止")
    
    def _check_loop(self) -> None:
        """背景檢查迴圈"""
        while self._running:
            try:
                self._check_stamina()
                self._check_login_reminders()
                if self._on_check_callback:
                    self._on_check_callback()
            except Exception as e:
                print(f"檢查體力時發生錯誤: {e}")
            
            # 分段睡眠，讓停止更快響應
            for _ in range(self.check_interval):
                if not self._running:
                    break
                time.sleep(1)
    
    def _check_stamina(self) -> None:
        """檢查所有遊戲的體力狀態"""
        for game in self._games:
            current = game.get_current_stamina()
            
            if current is None:
                continue
            
            # 體力已滿
            if current >= game.max_stamina:
                # 避免重複通知
                if game.id not in self._notified_games:
                    self._send_notification(game)
                    self._notified_games.add(game.id)
            else:
                # 體力不滿時，移除已通知標記（下次滿時會再通知）
                self._notified_games.discard(game.id)
    
    def _send_notification(self, game) -> None:
        """發送系統通知"""
        if not PLYER_AVAILABLE:
            print(f"[模擬通知] {game.name} 的 {game.stamina_name} 已滿！")
            return
        
        try:
            notification.notify(
                title=f"🎮 {game.name}",
                message=f"{game.stamina_name} 已滿！快去消耗體力吧～",
                app_name="Gacha Game Monitor",
                timeout=10,
            )
            print(f"已發送通知: {game.name} 體力已滿")
        except Exception as e:
            print(f"發送通知失敗: {e}")
    
    def _check_login_reminders(self) -> None:
        """檢查是否有遊戲太久沒登入"""
        for game in self._games:
            if game.is_login_overdue():
                reminder_key = f"login_{game.id}"
                if reminder_key not in self._notified_games:
                    self._send_login_reminder(game)
                    self._notified_games.add(reminder_key)
            else:
                self._notified_games.discard(f"login_{game.id}")

    def _send_login_reminder(self, game) -> None:
        """發送登入提醒通知"""
        if not PLYER_AVAILABLE:
            print(f"[模擬通知] {game.name} 太久沒登入了！")
            return

        hours = 0
        if game.last_login:
            hours = int((datetime.now() - game.last_login).total_seconds() / 3600)
        try:
            notification.notify(
                title=f"🎮 {game.name} 登入提醒",
                message=f"已經 {hours} 小時沒有開啟 {game.name} 了！",
                app_name="Gacha Game Monitor",
                timeout=10,
            )
            print(f"已發送登入提醒: {game.name}")
        except Exception as e:
            print(f"發送登入提醒失敗: {e}")

    def reset_notification(self, game_id: str) -> None:
        """重置特定遊戲的通知狀態（記錄新體力後呼叫）"""
        self._notified_games.discard(game_id)
    
    def send_test_notification(self) -> bool:
        """發送測試通知"""
        if not PLYER_AVAILABLE:
            return False
        
        try:
            notification.notify(
                title="🎮 Gacha Game Monitor",
                message="通知功能運作正常！",
                app_name="Gacha Game Monitor",
                timeout=5,
            )
            return True
        except Exception:
            return False
