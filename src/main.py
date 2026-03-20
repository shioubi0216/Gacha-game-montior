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
    page.window.height = 750
    page.window.min_width = 600
    page.window.min_height = 500
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

    # ========== 遊戲卡片列表（需要在事件處理之前宣告）==========
    game_cards: list[GameCard] = []

    def refresh_cards() -> None:
        """刷新所有卡片的顯示"""
        for card in game_cards:
            card.refresh()

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

    def show_stamina_dialog(game: Game) -> None:
        """顯示記錄體力的對話框"""
        
        # 取得目前預估體力作為預設值
        current_estimate = game.get_current_stamina()
        default_value = str(current_estimate) if current_estimate else ""
        
        stamina_field = ft.TextField(
            label=f"當前 {game.stamina_name}",
            hint_text=f"0 ~ {game.max_stamina}",
            value=default_value,
            width=200,
            keyboard_type=ft.KeyboardType.NUMBER,
            autofocus=True,
        )
        
        error_text = ft.Text(
            "",
            size=12,
            color=ft.Colors.RED_400,
        )

        def close_dialog(e):
            dialog.open = False
            page.update()

        def save_stamina(e):
            try:
                stamina = int(stamina_field.value)
                if stamina < 0 or stamina > game.max_stamina:
                    error_text.value = f"請輸入 0 ~ {game.max_stamina} 之間的數字"
                    page.update()
                    return
                
                # 記錄體力
                controller.record_login(game, stamina)
                status_text.value = f"✅ 已記錄 {game.name} 的 {game.stamina_name}：{stamina}"
                status_text.color = ft.Colors.GREEN_400
                
                dialog.open = False
                refresh_cards()
                page.update()
                
            except ValueError:
                error_text.value = "請輸入有效的數字"
                page.update()

        dialog = ft.AlertDialog(
            title=ft.Text(f"記錄 {game.name} 的 {game.stamina_name}"),
            content=ft.Column(
                controls=[
                    ft.Text(
                        f"請輸入你目前在遊戲中看到的 {game.stamina_name} 數值：",
                        size=14,
                    ),
                    stamina_field,
                    error_text,
                    ft.Text(
                        f"💡 體力上限：{game.max_stamina}",
                        size=12,
                        color=ft.Colors.WHITE54,
                    ),
                ],
                tight=True,
                spacing=10,
            ),
            actions=[
                ft.TextButton("取消", on_click=close_dialog),
                ft.ElevatedButton("儲存", on_click=save_stamina),
            ],
        )

        page.overlay.append(dialog)
        dialog.open = True
        page.update()

    # ========== 建立遊戲卡片 ==========

    def create_cards() -> ft.Row:
        """建立所有遊戲卡片"""
        game_cards.clear()

        for game in games:
            card = GameCard(
                game=game,
                on_launch=on_launch_game,
                on_record_stamina=show_stamina_dialog,
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
    
    # ========== 刷新按鈕 ==========
    
    def refresh_all(e) -> None:
        """手動刷新所有卡片"""
        refresh_cards()
        status_text.value = "🔄 已刷新"
        status_text.color = ft.Colors.CYAN_400
        page.update()
    
    refresh_button = ft.IconButton(
        icon=ft.Icons.REFRESH,
        icon_color=ft.Colors.WHITE70,
        tooltip="刷新",
        on_click=refresh_all,
    )

    # ========== 組合頁面 ==========

    page.add(
        ft.Column(
            controls=[
                # 頂部工具列
                ft.Row(
                    controls=[
                        ft.Container(expand=True),  # 彈性空間
                        refresh_button,
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
                        "💡 點擊「記錄體力」輸入當前體力 → 點擊「啟動遊戲」打開遊戲",
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
