"""
Tray Service - 系統托盤服務

負責管理系統托盤圖示，包括：
- 最小化到托盤
- 右鍵選單
- 點擊恢復視窗
"""

import threading
from typing import Callable, Optional

# pystray 用於系統托盤
try:
    import pystray
    from PIL import Image, ImageDraw
    PYSTRAY_AVAILABLE = True
except ImportError:
    PYSTRAY_AVAILABLE = False
    print("警告: pystray 或 Pillow 未安裝，托盤功能將無法使用")


class TrayService:
    """系統托盤服務"""
    
    def __init__(
        self,
        on_show: Optional[Callable] = None,
        on_quit: Optional[Callable] = None,
    ):
        """
        初始化托盤服務
        
        Args:
            on_show: 點擊「顯示視窗」時的 callback
            on_quit: 點擊「退出」時的 callback
        """
        self.on_show = on_show
        self.on_quit = on_quit
        self._icon: Optional[pystray.Icon] = None
        self._thread: Optional[threading.Thread] = None
    
    def _create_icon_image(self) -> Image.Image:
        """建立托盤圖示（簡單的遊戲控制器圖案）"""
        # 建立 64x64 的圖片
        size = 64
        image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # 繪製一個簡單的遊戲手把形狀
        # 主體 - 圓角矩形（用橢圓模擬）
        draw.ellipse([8, 16, 56, 48], fill='#00BCD4')
        
        # 左搖桿
        draw.ellipse([12, 22, 28, 38], fill='#263238')
        draw.ellipse([15, 25, 25, 35], fill='#37474F')
        
        # 右按鈕
        draw.ellipse([40, 24, 48, 32], fill='#E91E63')
        draw.ellipse([48, 28, 56, 36], fill='#4CAF50')
        
        # 中間按鈕
        draw.rectangle([28, 28, 36, 36], fill='#FFC107')
        
        return image
    
    def start(self) -> None:
        """啟動托盤服務"""
        if not PYSTRAY_AVAILABLE:
            print("托盤功能不可用")
            return
        
        if self._icon is not None:
            return  # 已經在運行
        
        # 建立選單
        menu = pystray.Menu(
            pystray.MenuItem(
                "Gacha Game Monitor",
                None,
                enabled=False,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "顯示視窗",
                self._handle_show,
                default=True,  # 雙擊時的預設動作
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "退出程式",
                self._handle_quit,
            ),
        )
        
        # 建立托盤圖示
        self._icon = pystray.Icon(
            name="GachaGameMonitor",
            icon=self._create_icon_image(),
            title="Gacha Game Monitor",
            menu=menu,
        )
        
        # 在背景執行緒中運行托盤
        self._thread = threading.Thread(target=self._icon.run, daemon=True)
        self._thread.start()
        print("托盤服務已啟動")
    
    def stop(self) -> None:
        """停止托盤服務"""
        if self._icon:
            self._icon.stop()
            self._icon = None
        print("托盤服務已停止")
    
    def _handle_show(self, icon, item) -> None:
        """處理「顯示視窗」選單項"""
        if self.on_show:
            self.on_show()
    
    def _handle_quit(self, icon, item) -> None:
        """處理「退出程式」選單項"""
        self.stop()
        if self.on_quit:
            self.on_quit()
    
    def update_tooltip(self, text: str) -> None:
        """更新托盤圖示的提示文字"""
        if self._icon:
            self._icon.title = text
