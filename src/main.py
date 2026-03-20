"""
Gacha Game Monitor - 主程式

Flet 0.80+ 版本適配

執行方式：
    python src/main.py
"""

import flet as ft
import sys
from pathlib import Path

# 將 src 目錄加入 Python 路徑
sys.path.insert(0, str(Path(__file__).parent))

from models import Game, DEFAULT_GAMES
from views import GameCard
from controllers import GameController
from services import SettingsService, NotificationService, TrayService


def main(page: ft.Page) -> None:
    """Flet 應用程式的主函式"""
    
    # ========== 頁面設定 ==========
    page.title = "Gacha Game Monitor 🎮"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    page.window.width = 1000
    page.window.height = 750
    page.window.min_width = 600
    page.window.min_height = 500
    page.bgcolor = ft.Colors.BLUE_GREY_900

    # ========== 初始化服務 ==========
    controller = GameController(data_path="data/games.json")
    games = controller.load_games()
    
    settings = SettingsService(settings_path="data/settings.json")
    notification_service = NotificationService(check_interval=60)
    notification_service.set_games(games)
    
    # ========== 狀態追蹤 ==========
    state = {
        "page_ready": False,
        "tray_service": None,
    }

    # ========== UI 元件 ==========
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
        margin=20,
    )

    status_text = ft.Text("", size=14, color=ft.Colors.GREEN_400)
    game_cards: list[GameCard] = []

    def refresh_cards() -> None:
        """刷新所有卡片的顯示"""
        if not state["page_ready"]:
            return
        try:
            for card in game_cards:
                card.refresh()
            page.update()
        except Exception:
            pass

    # ========== 事件處理 ==========

    def on_launch_game(game: Game) -> None:
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
                ft.Button("儲存", on_click=save_path),
            ],
        )
        page.overlay.append(dialog)
        dialog.open = True
        page.update()

    def show_stamina_dialog(game: Game) -> None:
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
        error_text = ft.Text("", size=12, color=ft.Colors.RED_400)

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
                
                controller.record_login(game, stamina)
                notification_service.reset_notification(game.id)
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
                    ft.Text(f"請輸入目前的 {game.stamina_name} 數值：", size=14),
                    stamina_field,
                    error_text,
                    ft.Text(f"💡 上限：{game.max_stamina}", size=12, color=ft.Colors.WHITE54),
                ],
                tight=True,
                spacing=10,
            ),
            actions=[
                ft.TextButton("取消", on_click=close_dialog),
                ft.Button("儲存", on_click=save_stamina),
            ],
        )
        page.overlay.append(dialog)
        dialog.open = True
        page.update()

    # ========== 建立遊戲卡片 ==========
    def create_cards() -> ft.Row:
        game_cards.clear()
        for game in games:
            card = GameCard(
                game=game,
                on_launch=on_launch_game,
                on_record_stamina=show_stamina_dialog,
            )
            game_cards.append(card)
        return ft.Row(
            controls=game_cards,
            wrap=True,
            spacing=16,
            run_spacing=16,
            alignment=ft.MainAxisAlignment.CENTER,
        )

    cards_container = create_cards()

    # ========== 設定面板 ==========
    def show_settings(e) -> None:
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
        
        notification_switch = ft.Switch(
            value=settings.notifications_enabled,
            active_color=ft.Colors.CYAN_400,
        )
        
        def toggle_notifications(e):
            settings.notifications_enabled = notification_switch.value
        notification_switch.on_change = toggle_notifications
        
        def reset_close_behavior(e):
            settings.close_to_tray = None
            status_text.value = "✅ 已重置，下次關閉視窗時會再次詢問"
            status_text.color = ft.Colors.GREEN_400
            settings_dialog.open = False
            page.update()

        def close_settings(e):
            settings_dialog.open = False
            page.update()
        
        def test_notification(e):
            if notification_service.send_test_notification():
                status_text.value = "✅ 測試通知已發送"
                status_text.color = ft.Colors.GREEN_400
            else:
                status_text.value = "❌ 通知功能不可用"
                status_text.color = ft.Colors.RED_400
            page.update()

        settings_dialog = ft.AlertDialog(
            title=ft.Text("設定"),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("遊戲路徑", weight=ft.FontWeight.BOLD),
                        game_list,
                        ft.Divider(),
                        ft.Text("通知設定", weight=ft.FontWeight.BOLD),
                        ft.Row([
                            ft.Text("體力滿時發送通知"),
                            notification_switch,
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Button("測試通知", icon=ft.Icons.NOTIFICATIONS, on_click=test_notification),
                        ft.Divider(),
                        ft.Text("其他設定", weight=ft.FontWeight.BOLD),
                        ft.TextButton("重置「關閉視窗」行為", on_click=reset_close_behavior),
                    ],
                    scroll=ft.ScrollMode.AUTO,
                ),
                width=500,
                height=450,
            ),
            actions=[ft.TextButton("關閉", on_click=close_settings)],
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

    def refresh_all(e) -> None:
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

    # ========== 視窗關閉處理 ==========
    
    async def show_window_from_tray():
        page.window.visible = True
        page.window.focused = True
        page.update()
    
    async def quit_application():
        notification_service.stop()
        if state["tray_service"]:
            state["tray_service"].stop()
        await page.window.destroy()
    
    def minimize_to_tray():
        page.window.visible = False
        page.update()
        
        if state["tray_service"] is None:
            state["tray_service"] = TrayService(
                on_show=lambda: page.run_task(show_window_from_tray),
                on_quit=lambda: page.run_task(quit_application),
            )
            state["tray_service"].start()
    
    async def show_close_dialog():
        remember_checkbox = ft.Checkbox(label="記住我的選擇", value=True)
        
        async def close_and_quit(e):
            if remember_checkbox.value:
                settings.close_to_tray = False
            close_dialog.open = False
            page.update()
            await quit_application()
        
        def close_and_minimize(e):
            if remember_checkbox.value:
                settings.close_to_tray = True
            close_dialog.open = False
            page.update()
            minimize_to_tray()
        
        def cancel_close(e):
            close_dialog.open = False
            page.update()
        
        close_dialog = ft.AlertDialog(
            title=ft.Text("關閉視窗"),
            content=ft.Column(
                controls=[
                    ft.Text("你想要怎麼處理？"),
                    ft.Container(height=10),
                    remember_checkbox,
                ],
                tight=True,
            ),
            actions=[
                ft.TextButton("取消", on_click=cancel_close),
                ft.Button("最小化到托盤", icon=ft.Icons.MINIMIZE, on_click=close_and_minimize),
                ft.Button(
                    "退出程式",
                    icon=ft.Icons.CLOSE,
                    on_click=close_and_quit,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.RED_700),
                ),
            ],
        )
        page.overlay.append(close_dialog)
        close_dialog.open = True
        page.update()
    
    async def handle_window_event(e):
        if "CLOSE" in str(e.type):
            close_to_tray = settings.close_to_tray
            
            if close_to_tray is None:
                await show_close_dialog()
            elif close_to_tray:
                minimize_to_tray()
            else:
                await quit_application()
    
    page.window.prevent_close = True
    page.window.on_event = handle_window_event

    # ========== 組合頁面 ==========
    page.add(
        ft.Column(
            controls=[
                ft.Row(
                    controls=[ft.Container(expand=True), refresh_button, settings_button],
                ),
                header,
                ft.Container(content=status_text, margin=10),
                ft.Container(content=cards_container, expand=True),
                ft.Container(
                    content=ft.Text(
                        "💡 點擊「記錄體力」輸入當前體力 → 體力滿時會收到通知",
                        size=12,
                        color=ft.Colors.WHITE54,
                    ),
                    margin=10,
                ),
            ],
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
    )
    
    # ========== 啟動服務 ==========
    state["page_ready"] = True
    notification_service.on_check(refresh_cards)
    if settings.notifications_enabled:
        notification_service.start()


if __name__ == "__main__":
    ft.app(main)
