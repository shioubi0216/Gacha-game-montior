"""
HoYoLab Service - HoYoLab API 即時體力查詢

使用 genshin.py 套件查詢星穹鐵道的即時開拓力數值，
省去手動輸入體力的步驟。

需要使用者提供 ltoken_v2 和 ltuid_v2（從瀏覽器 Cookie 取得）
"""

import asyncio
import threading
from typing import Optional, Callable

import genshin


class HoYoLabService:
    """HoYoLab API 服務，使用 genshin.py 查詢星穹鐵道即時體力"""

    def __init__(
        self,
        ltuid: str,
        ltoken: str,
    ):
        """
        Args:
            ltuid: HoYoLab ltuid_v2 值
            ltoken: HoYoLab ltoken_v2 值
        """
        self.ltuid = ltuid
        self.ltoken = ltoken
        self._timer: Optional[threading.Timer] = None
        self._running = False
        self._callback: Optional[Callable[[dict], None]] = None
        self._interval = 600

    def _create_client(self) -> genshin.Client:
        """建立 genshin.py Client"""
        cookies = {"ltuid_v2": self.ltuid, "ltoken_v2": self.ltoken}
        return genshin.Client(
            cookies,
            game=genshin.Game.STARRAIL,
            region=genshin.Region.OVERSEAS,
        )

    def fetch_stamina(self) -> Optional[dict]:
        """
        查詢即時體力（同步包裝）

        Returns:
            成功時回傳 {"current": int, "max": int, "recover_seconds": int}
            失敗時回傳 None
        """
        try:
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(self._async_fetch())
            finally:
                loop.close()
        except Exception as e:
            print(f"HoYoLab 查詢失敗: {type(e).__name__}: {e}")
            return None

    async def _async_fetch(self) -> Optional[dict]:
        """實際的 async 查詢邏輯"""
        client = self._create_client()
        try:
            notes = await client.get_starrail_notes()
            return {
                "current": notes.current_stamina,
                "max": notes.max_stamina,
                "recover_seconds": int(notes.stamina_recover_time.total_seconds()),
            }
        except genshin.errors.InvalidCookies:
            print("HoYoLab 錯誤: Cookie 無效或已過期")
            return None
        except genshin.errors.DataNotPublic:
            print("HoYoLab 錯誤: 即時便箋未公開，請到 HoYoLab 開啟")
            return None
        except genshin.errors.GenshinException as e:
            print(f"HoYoLab API 錯誤: {e}")
            return None

    def start(self, interval: int = 600, callback: Optional[Callable[[dict], None]] = None) -> None:
        """
        啟動定時查詢

        Args:
            interval: 查詢間隔秒數（預設 600 = 10 分鐘）
            callback: 查詢成功時的回呼函式，接收體力資料 dict
        """
        self._interval = interval
        self._callback = callback
        self._running = True
        self._schedule_next()

    def stop(self) -> None:
        """停止定時查詢"""
        self._running = False
        if self._timer:
            self._timer.cancel()
            self._timer = None

    def _schedule_next(self) -> None:
        """排程下一次查詢"""
        if not self._running:
            return
        self._timer = threading.Timer(self._interval, self._poll)
        self._timer.daemon = True
        self._timer.start()

    def _poll(self) -> None:
        """執行一次查詢並排程下一次"""
        if not self._running:
            return

        result = self.fetch_stamina()
        if result and self._callback:
            try:
                self._callback(result)
            except Exception as e:
                print(f"HoYoLab callback 執行失敗: {e}")

        self._schedule_next()
