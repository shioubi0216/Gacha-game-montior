"""
GameCard View - 遊戲卡片 UI 元件

這個模組定義了顯示單一遊戲資訊的卡片元件。

設計原則：
- 元件只負責「顯示」，不處理業務邏輯
- 透過 callback 將事件傳遞給 Controller
- 使用 Flet 的 Flexbox 排版（Row, Column）
"""

import flet as ft
from typing import Callable, Optional
from models.game import Game


class GameCard(ft.Container):
    """
    遊戲卡片元件

    顯示內容：
    - 遊戲名稱
    - 上次登入時間
    - 預估當前體力
    - 啟動遊戲按鈕
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

        self.launch_button = ft.ElevatedButton(
            "啟動遊戲",
            icon=ft.Icons.PLAY_ARROW,
            on_click=self._handle_launch,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.BLUE_700,
                color=ft.Colors.WHITE,
            ),
        )

        # 組合元件 - 只使用穩定的基礎 API
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
                            ],
                            spacing=4,
                        ),
                        padding=ft.padding.only(left=32),
                    ),
                    # 按鈕區
                    ft.Row(
                        controls=[self.launch_button],
                        alignment=ft.MainAxisAlignment.END,
                    ),
                ],
                spacing=8,
            ),
            bgcolor=ft.Colors.WHITE10,
            border=ft.border.all(1, ft.Colors.WHITE24),
            border_radius=12,
            padding=16,
            width=280,
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
            return f"⚡ {self.game.stamina_name}：{current} / {self.game.max_stamina}"
        return f"⚡ {self.game.stamina_name}：-- / {self.game.max_stamina}"

    def _handle_launch(self, e: ft.ControlEvent) -> None:
        """處理啟動按鈕點擊"""
        if self.on_launch:
            self.on_launch(self.game)

    def refresh(self) -> None:
        """刷新顯示內容（當遊戲資料更新後呼叫）"""
        self.last_login_text.value = self._get_login_display()
        self.stamina_text.value = self._get_stamina_display()
        self.update()
