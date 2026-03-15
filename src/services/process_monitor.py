"""
ProcessMonitor Service - 進程監控服務

這個模組負責監控遊戲進程的狀態，包括：
- 偵測遊戲是否正在運行
- 偵測遊戲何時關閉

這是 Phase 3 的進階功能，目前只有介面定義。

設計原則：
- 使用 psutil 庫來獲取系統進程資訊
- 使用背景執行緒避免阻塞 UI
- 透過 callback 機制通知遊戲狀態變更

TODO: Phase 3 實作
"""

import asyncio
from typing import Callable, Dict, Optional, Set
from pathlib import Path

# psutil 是可選的相依套件
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("警告: psutil 未安裝，進程監控功能將無法使用")


class ProcessMonitor:
    """
    進程監控服務
    
    監控指定的遊戲進程，當進程結束時觸發 callback。
    
    Usage:
        monitor = ProcessMonitor()
        monitor.on_process_exit("fgo", lambda: print("FGO 已關閉"))
        monitor.watch("fgo", "C:/Games/FGO/Fate.exe")
        await monitor.start()
    """
    
    def __init__(self, check_interval: float = 5.0):
        """
        初始化監控服務
        
        Args:
            check_interval: 檢查間隔（秒），預設 5 秒
        """
        self.check_interval = check_interval
        self._watched_processes: Dict[str, str] = {}  # game_id -> exe_name
        self._running_processes: Set[str] = set()     # 目前運行中的 game_id
        self._exit_callbacks: Dict[str, Callable[[], None]] = {}
        self._running = False
    
    def watch(self, game_id: str, exe_path: str) -> None:
        """
        開始監控一個遊戲進程
        
        Args:
            game_id: 遊戲 ID
            exe_path: 執行檔的完整路徑
        """
        exe_name = Path(exe_path).name.lower()
        self._watched_processes[game_id] = exe_name
    
    def unwatch(self, game_id: str) -> None:
        """停止監控一個遊戲進程"""
        self._watched_processes.pop(game_id, None)
        self._running_processes.discard(game_id)
    
    def on_process_exit(self, game_id: str, callback: Callable[[], None]) -> None:
        """
        註冊進程結束時的 callback
        
        Args:
            game_id: 遊戲 ID
            callback: 進程結束時呼叫的函式
        """
        self._exit_callbacks[game_id] = callback
    
    def is_running(self, game_id: str) -> bool:
        """檢查指定遊戲是否正在運行"""
        return game_id in self._running_processes
    
    async def start(self) -> None:
        """開始監控（非同步）"""
        if not PSUTIL_AVAILABLE:
            print("psutil 未安裝，無法啟動進程監控")
            return
        
        self._running = True
        while self._running:
            await self._check_processes()
            await asyncio.sleep(self.check_interval)
    
    def stop(self) -> None:
        """停止監控"""
        self._running = False
    
    async def _check_processes(self) -> None:
        """檢查所有監控中的進程狀態"""
        if not PSUTIL_AVAILABLE:
            return
        
        # 取得目前所有運行中的進程名稱
        running_exe_names = set()
        for proc in psutil.process_iter(['name']):
            try:
                name = proc.info['name']
                if name:
                    running_exe_names.add(name.lower())
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # 檢查每個監控中的遊戲
        for game_id, exe_name in self._watched_processes.items():
            was_running = game_id in self._running_processes
            is_running = exe_name in running_exe_names
            
            if is_running:
                self._running_processes.add(game_id)
            elif was_running and not is_running:
                # 進程剛結束
                self._running_processes.discard(game_id)
                if game_id in self._exit_callbacks:
                    try:
                        self._exit_callbacks[game_id]()
                    except Exception as e:
                        print(f"進程結束 callback 執行失敗: {e}")
