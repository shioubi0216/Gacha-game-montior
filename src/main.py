"""
Gacha Game Monitor - 主程式

這是應用程式的進入點，負責：
- 初始化 Flet 應用程式
- 設定整體 UI 佈局
- 連接 Controller 和 View

執行方式：
    python src/main.py
"""

import flet as ft
import sys
from pathlib import Path

# 將 src 目錄加入 Python 路徑
# 這樣才能正確 import 我們的模組
sys.path.insert(0, str(Path(__file__).parent))

from models import Game, DEFAULT_GAMES
from views import GameCard
from controllers import GameController


def main(page: ft.Page) -> None:
    """
    Flet 應用程式的主函式

    Args:
        page: Flet 提供的頁面物件
    """
    # ========== 頁面設定 ==========
    page.title = "Gacha Game Monitor 🎮"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    page.window.width = 1000
    page.window.height = 700
    page.window.min_width = 600
    page.window.min_height = 400
    page.bgcolor = ft.Colors.BLUE_GREY_900

    # ========== 初始化 Controller ==========
    controller = GameController(data_path="data/games.json")
    games = controller.load_games()

    # ========== UI 元件 ==========

    # 標題
    header = ft.Container(
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.SPORTS_ESPORTS, size=32, color=ft.Colors.CYAN_400),
                ft.Text(
                    "Gacha Game Monitor",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.WHITE,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        margin=ft.margin.only(bottom=20),
    )

    # 狀態訊息
    status_text = ft.Text(
        "",
        size=14,
        color=ft.Colors.GREEN_400,
    )

    # ========== 事件處理 ==========

    def on_launch_game(game: Game) -> None:
        """處理遊戲啟動"""
        if not game.exe_path:
            status_text.value = f"⚠️ 請先設定 {game.name} 的執行檔路徑"
            status_text.color = ft.Colors.ORANGE_400
        else:
            success = controller.launch_game(game)
            if success:
                status_text.value = f"✅ 已啟動 {game.name}"
                status_text.color = ft.Colors.GREEN_400
            else:
                status_text.value = f"❌ 啟動 {game.name} 失敗"
                status_text.color = ft.Colors.RED_400

        # 刷新所有卡片
        refresh_cards()
        page.update()

    def show_path_dialog(game: Game) -> None:
        """顯示設定路徑的對話框"""
        path_field = ft.TextField(
            label="執行檔路徑",
            hint_text=r"例如: C:\Games\FGO\Fate.exe",
            value=game.exe_path or "",
            width=400,
        )

        def close_dialog(e):
            dialog.open = False
            page.update()

        def save_path(e):
            if path_field.value:
                controller.update_game_path(game.id, path_field.value)
                status_text.value = f"✅ 已更新 {game.name} 的路徑"
                status_text.color = ft.Colors.GREEN_400
            dialog.open = False
            page.update()

        dialog = ft.AlertDialog(
            title=ft.Text(f"設定 {game.name} 執行檔路徑"),
            content=path_field,
            actions=[
                ft.TextButton("取消", on_click=close_dialog),
                ft.ElevatedButton("儲存", on_click=save_path),
            ],
        )

        page.overlay.append(dialog)
        dialog.open = True
        page.update()

    # ========== 建立遊戲卡片 ==========

    game_cards: list[GameCard] = []

    def create_cards() -> ft.Row:
        """建立所有遊戲卡片"""
        game_cards.clear()

        for game in games:
            card = GameCard(
                game=game,
                on_launch=on_launch_game,
            )
            game_cards.append(card)

        # 使用 wrap 讓卡片自動換行
        return ft.Row(
            controls=game_cards,
            wrap=True,
            spacing=16,
            run_spacing=16,
            alignment=ft.MainAxisAlignment.CENTER,
        )

    def refresh_cards() -> None:
        """刷新所有卡片的顯示"""
        for card in game_cards:
            card.refresh()

    cards_container = create_cards()

    # ========== 設定區域 ==========

    def show_settings(e) -> None:
        """顯示設定面板"""
        game_list = ft.Column(
            controls=[
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.GAMES),
                    title=ft.Text(game.name),
                    subtitle=ft.Text(
                        game.exe_path or "尚未設定路徑",
                        color=ft.Colors.WHITE70 if game.exe_path else ft.Colors.ORANGE_400,
                    ),
                    on_click=lambda e, g=game: show_path_dialog(g),
                )
                for game in games
            ],
            scroll=ft.ScrollMode.AUTO,
        )

        def close_settings(e):
            settings_dialog.open = False
            page.update()

        settings_dialog = ft.AlertDialog(
            title=ft.Text("遊戲設定"),
            content=ft.Container(
                content=game_list,
                width=500,
                height=400,
            ),
            actions=[
                ft.TextButton("關閉", on_click=close_settings),
            ],
        )

        page.overlay.append(settings_dialog)
        settings_dialog.open = True
        page.update()

    settings_button = ft.IconButton(
        icon=ft.Icons.SETTINGS,
        icon_color=ft.Colors.WHITE70,
        tooltip="設定",
        on_click=show_settings,
    )

    # ========== 組合頁面 ==========

    page.add(
        ft.Column(
            controls=[
                # 頂部工具列
                ft.Row(
                    controls=[
                        ft.Container(expand=True),  # 彈性空間
                        settings_button,
                    ],
                ),
                header,
                # 狀態訊息
                ft.Container(
                    content=status_text,
                    margin=ft.margin.only(bottom=10),
                ),
                # 遊戲卡片區
                ft.Container(
                    content=cards_container,
                    expand=True,
                ),
                # 底部說明
                ft.Container(
                    content=ft.Text(
                        "💡 點擊設定按鈕 (右上角齒輪) 來設定遊戲執行檔路徑",
                        size=12,
                        color=ft.Colors.WHITE54,
                    ),
                    margin=ft.margin.only(top=10),
                ),
            ],
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
    )


if __name__ == "__main__":
    ft.app(target=main)
