"""
ProcessMonitor Service - 進程監控服務

監控遊戲進程的狀態：
- 偵測遊戲啟動與關閉
- 透過 callback 通知主程式狀態變更

設計原則：
- 使用 threading（與 NotificationService 一致）
- 透過 callback 機制通知遊戲狀態變更
- 使用 psutil 取得系統進程資訊
"""

import threading
import time
import shlex
from typing import Callable, Dict, List, Optional, Set, Tuple
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

    監控指定的遊戲進程，當進程啟動或結束時觸發 callback。

    Usage:
        monitor = ProcessMonitor()
        monitor.watch("fgo", "C:/Games/FGO/Fate.exe")
        monitor.on_process_exit("fgo", lambda gid: print(f"{gid} 已關閉"))
        monitor.start()
    """

    def __init__(self, check_interval: float = 5.0):
        """
        初始化監控服務

        Args:
            check_interval: 檢查間隔（秒），預設 5 秒
        """
        self.check_interval = check_interval
        # game_id -> (exe_name, cmdline_keywords)
        # cmdline_keywords: 需要額外比對的命令列關鍵字（用於模擬器等場景）
        self._watched_processes: Dict[str, Tuple[str, List[str]]] = {}
        self._running_processes: Set[str] = set()     # 目前運行中的 game_id
        self._exit_callbacks: Dict[str, Callable[[str], None]] = {}
        self._start_callbacks: Dict[str, Callable[[str], None]] = {}
        self._running = False
        self._thread: threading.Thread | None = None

    @staticmethod
    def _parse_exe_path(exe_path: str) -> Tuple[str, List[str]]:
        """
        解析 exe_path，支援帶命令列參數的格式

        範例:
          "C:/Games/FGO/Fate.exe"
            → ("fate.exe", [])
          "E:/MuMuPlayerGlobal/nx_main/MuMuNxMain.exe -p com.xiaomeng.fategrandorder -v 0"
            → ("mumunxmain.exe", ["com.xiaomeng.fategrandorder"])

        Returns:
            (exe_name, cmdline_keywords): exe 名稱與需比對的命令列關鍵字
        """
        # 以 .exe 為分界拆分路徑與參數
        exe_lower = exe_path.lower()
        exe_idx = exe_lower.find(".exe")
        if exe_idx == -1:
            # 沒有 .exe，整段當路徑
            return Path(exe_path).name.lower(), []

        actual_path = exe_path[:exe_idx + 4].strip()
        args_str = exe_path[exe_idx + 4:].strip()

        exe_name = Path(actual_path).name.lower()

        # 從參數中提取有意義的關鍵字（跳過 flag 如 -p, -v, 數字）
        cmdline_keywords = []
        if args_str:
            parts = args_str.split()
            for part in parts:
                # 跳過 flag（-p, -v 等）和純數字
                if part.startswith("-") or part.isdigit():
                    continue
                # 保留有意義的識別符（如 package name）
                cmdline_keywords.append(part.lower())

        return exe_name, cmdline_keywords

    def watch(self, game_id: str, exe_path: str) -> None:
        """
        開始監控一個遊戲進程

        支援兩種格式:
        - 單純路徑: "C:/Games/Game.exe"
        - 帶參數: "E:/Emulator/emu.exe -p com.game.package -v 0"

        Args:
            game_id: 遊戲 ID
            exe_path: 執行檔路徑（可帶命令列參數）
        """
        exe_name, cmdline_keywords = self._parse_exe_path(exe_path)
        self._watched_processes[game_id] = (exe_name, cmdline_keywords)

    def unwatch(self, game_id: str) -> None:
        """停止監控一個遊戲進程"""
        self._watched_processes.pop(game_id, None)
        self._running_processes.discard(game_id)

    def watch_games(self, games: list) -> None:
        """批量註冊要監控的遊戲（跳過 exe_path 為 None 的遊戲）"""
        for game in games:
            if game.exe_path:
                self.watch(game.id, game.exe_path)

    def on_process_exit(self, game_id: str, callback: Callable[[str], None]) -> None:
        """
        註冊進程結束時的 callback

        Args:
            game_id: 遊戲 ID
            callback: 進程結束時呼叫的函式，會傳入 game_id
        """
        self._exit_callbacks[game_id] = callback

    def on_process_start(self, game_id: str, callback: Callable[[str], None]) -> None:
        """
        註冊進程啟動時的 callback

        Args:
            game_id: 遊戲 ID
            callback: 進程啟動時呼叫的函式，會傳入 game_id
        """
        self._start_callbacks[game_id] = callback

    def is_running(self, game_id: str) -> bool:
        """檢查指定遊戲是否正在運行"""
        return game_id in self._running_processes

    def start(self) -> None:
        """啟動背景監控"""
        if not PSUTIL_AVAILABLE:
            print("psutil 未安裝，無法啟動進程監控")
            return

        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        print("進程監控服務已啟動")

    def stop(self) -> None:
        """停止監控"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        print("進程監控服務已停止")

    def _monitor_loop(self) -> None:
        """背景監控迴圈"""
        while self._running:
            try:
                self._check_processes()
            except Exception as e:
                print(f"進程監控時發生錯誤: {e}")

            # 分段睡眠，讓停止更快響應
            for _ in range(int(self.check_interval)):
                if not self._running:
                    break
                time.sleep(1)

    def _is_process_running(self, exe_name: str, cmdline_keywords: List[str]) -> bool:
        """
        檢查特定進程是否正在運行

        Args:
            exe_name: 執行檔名稱（小寫）
            cmdline_keywords: 需額外比對的命令列關鍵字（空列表 = 只比對 exe 名稱）
        """
        for proc in psutil.process_iter(['name']):
            try:
                name = proc.info['name']
                if not name or name.lower() != exe_name:
                    continue

                # exe 名稱匹配
                if not cmdline_keywords:
                    return True

                # 需要額外比對命令列參數（模擬器場景）
                try:
                    cmdline = " ".join(proc.cmdline()).lower()
                    if all(kw in cmdline for kw in cmdline_keywords):
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False

    def _check_processes(self) -> None:
        """檢查所有監控中的進程狀態"""
        if not PSUTIL_AVAILABLE:
            return

        for game_id, (exe_name, cmdline_keywords) in self._watched_processes.items():
            was_running = game_id in self._running_processes
            is_running = self._is_process_running(exe_name, cmdline_keywords)

            if is_running and not was_running:
                # 進程剛啟動
                self._running_processes.add(game_id)
                if game_id in self._start_callbacks:
                    try:
                        self._start_callbacks[game_id](game_id)
                    except Exception as e:
                        print(f"進程啟動 callback 執行失敗: {e}")
            elif was_running and not is_running:
                # 進程剛結束
                self._running_processes.discard(game_id)
                if game_id in self._exit_callbacks:
                    try:
                        self._exit_callbacks[game_id](game_id)
                    except Exception as e:
                        print(f"進程結束 callback 執行失敗: {e}")
