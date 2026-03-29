"""
GameController - 遊戲控制器

這個模組負責處理業務邏輯，包括：
- 載入/儲存遊戲資料
- 啟動遊戲執行檔
- 協調 Model 和 View

設計原則：
- Controller 是 Model 和 View 之間的橋樑
- 不直接操作 UI 元素，透過 callback 通知 View 更新
- 使用 asyncio 處理耗時操作，避免阻塞 UI
"""

import json
import os
import subprocess
import asyncio
from pathlib import Path
from typing import List, Optional, Callable
from models.game import Game, DEFAULT_GAMES


class GameController:
    """遊戲管理控制器"""
    
    def __init__(self, data_path: str = "data/games.json"):
        """
        初始化控制器
        
        Args:
            data_path: 遊戲資料的 JSON 檔案路徑
        """
        self.data_path = Path(data_path)
        self.games: List[Game] = []
        self._on_update_callbacks: List[Callable[[], None]] = []
    
    def load_games(self) -> List[Game]:
        """
        載入遊戲資料
        
        如果 JSON 檔案不存在，會建立預設遊戲清單。
        
        Returns:
            遊戲物件列表
        """
        if self.data_path.exists():
            try:
                with open(self.data_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.games = [Game.from_dict(g) for g in data]
            except (json.JSONDecodeError, KeyError) as e:
                print(f"載入遊戲資料失敗: {e}")
                self.games = self._create_default_games()
                self.save_games()
        else:
            self.games = self._create_default_games()
            self.save_games()
        
        return self.games
    
    def _create_default_games(self) -> List[Game]:
        """建立預設遊戲清單"""
        return [Game.from_dict(g) for g in DEFAULT_GAMES]
    
    def save_games(self) -> None:
        """儲存遊戲資料到 JSON 檔案"""
        # 確保目錄存在
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.data_path, "w", encoding="utf-8") as f:
            data = [g.to_dict() for g in self.games]
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def get_game_by_id(self, game_id: str) -> Optional[Game]:
        """根據 ID 取得遊戲"""
        for game in self.games:
            if game.id == game_id:
                return game
        return None
    
    def launch_game(self, game: Game) -> bool:
        """
        啟動遊戲
        
        Args:
            game: 要啟動的遊戲
            
        Returns:
            True 如果成功啟動，False 如果路徑未設定或檔案不存在
        """
        if not game.exe_path:
            print(f"遊戲 {game.name} 尚未設定執行檔路徑")
            return False
        
        exe_path = Path(game.exe_path)
        if not exe_path.exists():
            print(f"找不到執行檔: {exe_path}")
            return False
        
        try:
            if os.name == 'nt':
                # Windows：使用 ShellExecuteW 啟動，自動處理 UAC 提權
                import ctypes
                ctypes.windll.shell32.ShellExecuteW(
                    None, "open", str(exe_path), None, str(exe_path.parent), 1
                )
            else:
                subprocess.Popen(
                    [str(exe_path)],
                    shell=False,
                )
            
            # 記錄登入時間
            game.record_login()
            self.save_games()
            self._notify_update()
            
            return True
        except Exception as e:
            print(f"啟動遊戲失敗: {e}")
            return False
    
    def record_login(self, game: Game, stamina: Optional[int] = None) -> None:
        """
        記錄遊戲登入
        
        Args:
            game: 遊戲物件
            stamina: 當前體力值（可選）
        """
        game.record_login(stamina)
        self.save_games()
        self._notify_update()
    
    def update_game_path(self, game_id: str, exe_path: str) -> bool:
        """
        更新遊戲的執行檔路徑
        
        Args:
            game_id: 遊戲 ID
            exe_path: 新的執行檔路徑
            
        Returns:
            True 如果更新成功
        """
        game = self.get_game_by_id(game_id)
        if game:
            game.exe_path = exe_path
            self.save_games()
            return True
        return False
    
    def on_update(self, callback: Callable[[], None]) -> None:
        """
        註冊資料更新的 callback
        
        當遊戲資料變更時，會呼叫所有註冊的 callback。
        
        Args:
            callback: 無參數的函式
        """
        self._on_update_callbacks.append(callback)
    
    def _notify_update(self) -> None:
        """通知所有 callback 資料已更新"""
        for callback in self._on_update_callbacks:
            try:
                callback()
            except Exception as e:
                print(f"Callback 執行失敗: {e}")
