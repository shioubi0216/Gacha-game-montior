"""
GameCard View - 遊戲卡片 UI 元件

這個模組定義了顯示單一遊戲資訊的卡片元件。

設計原則：
- 元件只負責「顯示」，不處理業務邏輯
- 透過 callback 將事件傳遞給 Controller
- 使用 Flet 的 Flexbox 排版（Row, Column）
"""

import flet as ft
from datetime import datetime, timedelta
from typing import Callable, Optional
from models.game import Game


class GameCard(ft.Container):
    """
    遊戲卡片元件

    顯示內容：
    - 遊戲名稱
    - 上次登入時間
    - 預估當前體力
    - 預計體力全滿時間
    - 啟動遊戲按鈕
    - 記錄體力按鈕
    """

    def __init__(
        self,
        game: Game,
        on_launch: Optional[Callable[[Game], None]] = None,
        on_record_stamina: Optional[Callable[[Game], None]] = None,
    ):
        self.game = game
        self.on_launch = on_launch
        self.on_record_stamina = on_record_stamina

        # 建立 UI 元素
        self.name_text = ft.Text(
            game.name,
            size=18,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.WHITE,
        )

        self.last_login_text = ft.Text(
            self._get_login_display(),
            size=12,
            color=ft.Colors.WHITE70,
        )

        self.stamina_text = ft.Text(
            self._get_stamina_display(),
            size=14,
            color=ft.Colors.CYAN_200,
        )
        
        self.time_until_full_text = ft.Text(
            self._get_time_until_full_display(),
            size=12,
            color=ft.Colors.GREEN_300,
        )

        self.launch_button = ft.ElevatedButton(
            "啟動遊戲",
            icon=ft.Icons.PLAY_ARROW,
            on_click=self._handle_launch,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.BLUE_700,
                color=ft.Colors.WHITE,
            ),
        )
        
        self.record_button = ft.OutlinedButton(
            "記錄體力",
            icon=ft.Icons.EDIT,
            on_click=self._handle_record_stamina,
            style=ft.ButtonStyle(
                color=ft.Colors.CYAN_300,
            ),
        )

        # 組合元件
        super().__init__(
            content=ft.Column(
                controls=[
                    # 標題列
                    ft.Row(
                        controls=[
                            ft.Icon(
                                ft.Icons.GAMES,
                                color=ft.Colors.CYAN_400,
                                size=24,
                            ),
                            self.name_text,
                        ],
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    # 資訊區
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                self.last_login_text,
                                self.stamina_text,
                                self.time_until_full_text,
                            ],
                            spacing=4,
                        ),
                        padding=ft.padding.only(left=32),
                    ),
                    # 按鈕區
                    ft.Row(
                        controls=[
                            self.record_button,
                            self.launch_button,
                        ],
                        alignment=ft.MainAxisAlignment.END,
                        spacing=8,
                    ),
                ],
                spacing=8,
            ),
            bgcolor=ft.Colors.WHITE10,
            border=ft.border.all(1, ft.Colors.WHITE24),
            border_radius=12,
            padding=16,
            width=300,
        )

    def _get_login_display(self) -> str:
        """取得上次登入的顯示文字"""
        time_str = self.game.get_time_since_login()
        if time_str:
            return f"🕐 上次登入：{time_str}"
        return "🕐 尚未登入過"

    def _get_stamina_display(self) -> str:
        """取得體力狀態的顯示文字"""
        current = self.game.get_current_stamina()
        if current is not None:
            # 如果體力已滿，顯示特殊樣式
            if current >= self.game.max_stamina:
                return f"⚡ {self.game.stamina_name}：{self.game.max_stamina} / {self.game.max_stamina} ✅ 已滿！"
            return f"⚡ {self.game.stamina_name}：{current} / {self.game.max_stamina}"
        return f"⚡ {self.game.stamina_name}：-- / {self.game.max_stamina}"
    
    def _get_time_until_full_display(self) -> str:
        """取得預計體力全滿的時間顯示"""
        current = self.game.get_current_stamina()
        
        # 如果沒有記錄過體力
        if current is None:
            return "⏰ 請記錄體力以顯示預估"
        
        # 如果已經滿了
        if current >= self.game.max_stamina:
            return "⏰ 體力已滿，快去玩！"
        
        # 計算還需要多久
        time_left = self.game.get_time_until_full()
        if time_left is None:
            return ""
        
        # 計算預計滿的時間點
        full_time = datetime.now() + time_left
        full_time_str = full_time.strftime("%H:%M")
        
        # 格式化剩餘時間
        total_minutes = int(time_left.total_seconds() / 60)
        hours = total_minutes // 60
        minutes = total_minutes % 60
        
        if hours > 0:
            return f"⏰ 預計 {full_time_str} 滿（{hours}時{minutes}分後）"
        else:
            return f"⏰ 預計 {full_time_str} 滿（{minutes}分鐘後）"

    def _handle_launch(self, e: ft.ControlEvent) -> None:
        """處理啟動按鈕點擊"""
        if self.on_launch:
            self.on_launch(self.game)
    
    def _handle_record_stamina(self, e: ft.ControlEvent) -> None:
        """處理記錄體力按鈕點擊"""
        if self.on_record_stamina:
            self.on_record_stamina(self.game)

    def refresh(self) -> None:
        """刷新顯示內容（當遊戲資料更新後呼叫）"""
        self.last_login_text.value = self._get_login_display()
        self.stamina_text.value = self._get_stamina_display()
        self.time_until_full_text.value = self._get_time_until_full_display()
        
        # 根據體力狀態改變顏色
        current = self.game.get_current_stamina()
        if current is not None and current >= self.game.max_stamina:
            self.stamina_text.color = ft.Colors.GREEN_400
            self.time_until_full_text.color = ft.Colors.ORANGE_400
        else:
            self.stamina_text.color = ft.Colors.CYAN_200
            self.time_until_full_text.color = ft.Colors.GREEN_300
        
        self.update()
