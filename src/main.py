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
from services import SettingsService, NotificationService, TrayService, ProcessMonitor, HoYoLabService


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

    process_monitor = ProcessMonitor(check_interval=5.0)

    # ========== 初始化 HoYoLab 服務 ==========
    hoyolab_service: HoYoLabService | None = None

    def _init_hoyolab() -> HoYoLabService | None:
        """根據設定初始化 HoYoLab 服務"""
        if settings.hoyolab_enabled and settings.hoyolab_ltuid and settings.hoyolab_ltoken:
            return HoYoLabService(
                ltuid=settings.hoyolab_ltuid,
                ltoken=settings.hoyolab_ltoken,
            )
        return None

    hoyolab_service = _init_hoyolab()

    # ========== 狀態追蹤 ==========
    state = {
        "page_ready": False,
        "tray_service": None,
        "hoyolab_service": hoyolab_service,
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

    # ========== HoYoLab API 回調 ==========

    def on_hoyolab_update(data: dict) -> None:
        """HoYoLab API 查詢成功時的回調"""
        star_rail = controller.get_game_by_id("star_rail")
        if not star_rail:
            return

        from datetime import datetime
        star_rail.last_stamina = data["current"]
        star_rail.max_stamina = data["max"]
        star_rail.last_login = datetime.now()
        star_rail.api_last_sync = datetime.now()
        controller.save_games()

        if state["page_ready"]:
            try:
                refresh_cards()
                page.update()
            except Exception:
                pass

    def on_sync_stamina(game: Game) -> None:
        """手動觸發 HoYoLab 同步"""
        svc = state.get("hoyolab_service")
        if not svc:
            status_text.value = "⚠️ 請先在設定中配置 HoYoLab API"
            status_text.color = ft.Colors.ORANGE_400
            page.update()
            return

        status_text.value = "🔄 正在從 HoYoLab 同步..."
        status_text.color = ft.Colors.CYAN_400
        page.update()

        import threading
        def _do_sync():
            result = svc.fetch_stamina()
            if result:
                on_hoyolab_update(result)
                status_text.value = f"✅ 已同步星穹鐵道開拓力：{result['current']} / {result['max']}"
                status_text.color = ft.Colors.GREEN_400
            else:
                status_text.value = "❌ HoYoLab 同步失敗，請檢查 Cookie 是否過期"
                status_text.color = ft.Colors.RED_400
            try:
                page.update()
            except Exception:
                pass

        threading.Thread(target=_do_sync, daemon=True).start()

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
                # 同步更新進程監控
                process_monitor.watch(game.id, path_field.value)
                process_monitor.on_process_exit(game.id, _make_exit_callback(game.id))
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

    # ========== 進程監控：遊戲關閉時自動彈窗 ==========

    def show_game_closed_prompt(game_id: str) -> None:
        """遊戲關閉後自動彈出體力記錄提示"""
        game = next((g for g in games if g.id == game_id), None)
        if not game:
            return

        # 先自動記錄登入時間
        from datetime import datetime
        game.last_login = datetime.now()
        controller.save_games()

        stamina_field = ft.TextField(
            label=f"目前的 {game.stamina_name}",
            hint_text=f"0 ~ {game.max_stamina}",
            width=200,
            keyboard_type=ft.KeyboardType.NUMBER,
            autofocus=True,
        )
        error_text = ft.Text("", size=12, color=ft.Colors.RED_400)

        def close_dialog(e):
            dialog.open = False
            refresh_cards()
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
                status_text.value = f"✅ 已自動記錄 {game.name} 的 {game.stamina_name}：{stamina}"
                status_text.color = ft.Colors.GREEN_400
                dialog.open = False
                refresh_cards()
                page.update()
            except ValueError:
                error_text.value = "請輸入有效的數字"
                page.update()

        dialog = ft.AlertDialog(
            title=ft.Text(f"你剛關閉了 {game.name}"),
            content=ft.Column(
                controls=[
                    ft.Text(f"要記錄目前的 {game.stamina_name} 嗎？", size=14),
                    stamina_field,
                    error_text,
                    ft.Text("💡 跳過也會記錄登入時間", size=12, color=ft.Colors.WHITE54),
                ],
                tight=True,
                spacing=10,
            ),
            actions=[
                ft.TextButton("跳過", on_click=close_dialog),
                ft.Button("儲存", on_click=save_stamina),
            ],
        )
        page.overlay.append(dialog)
        dialog.open = True
        page.update()

    async def on_game_exited(game_id: str):
        """背景執行緒偵測到遊戲關閉時，透過 run_task 在 UI 執行緒彈出對話框"""
        # 若視窗隱藏中，先恢復顯示
        if not page.window.visible:
            page.window.visible = True
            page.window.focused = True
            page.update()
        show_game_closed_prompt(game_id)

    def _make_exit_callback(gid: str):
        """建立進程結束 callback（確保傳給 run_task 的是 coroutine function）"""
        async def _handler():
            await on_game_exited(gid)
        return lambda game_id: page.run_task(_handler)

    # ========== 建立遊戲卡片 ==========
    def create_cards() -> ft.Row:
        game_cards.clear()
        for game in games:
            card = GameCard(
                game=game,
                on_launch=on_launch_game,
                on_record_stamina=show_stamina_dialog,
                on_sync_stamina=on_sync_stamina,
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

    # ========== HoYoLab 服務管理 ==========

    def _restart_hoyolab_service() -> None:
        """重新啟動或停止 HoYoLab 服務"""
        # 停止舊的
        old_svc = state.get("hoyolab_service")
        if old_svc:
            old_svc.stop()
            state["hoyolab_service"] = None

        # 啟動新的
        if settings.hoyolab_enabled and settings.hoyolab_ltuid and settings.hoyolab_ltoken:
            svc = HoYoLabService(
                ltuid=settings.hoyolab_ltuid,
                ltoken=settings.hoyolab_ltoken,
            )
            state["hoyolab_service"] = svc
            # 立即查詢一次再啟動定時
            import threading
            def _initial_fetch():
                result = svc.fetch_stamina()
                if result:
                    on_hoyolab_update(result)
            threading.Thread(target=_initial_fetch, daemon=True).start()
            svc.start(interval=settings.hoyolab_interval, callback=on_hoyolab_update)

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

        # ---- HoYoLab 設定區塊 ----
        hoyolab_switch = ft.Switch(
            value=settings.hoyolab_enabled,
            active_color=ft.Colors.CYAN_400,
        )
        hoyolab_ltuid_field = ft.TextField(
            label="ltuid_v2",
            hint_text="從 HoYoLab Cookie 取得的 ltuid_v2 值",
            value=settings.hoyolab_ltuid or "",
            width=460,
        )
        hoyolab_ltoken_field = ft.TextField(
            label="ltoken_v2",
            hint_text="從 HoYoLab Cookie 取得的 ltoken_v2 值",
            value=settings.hoyolab_ltoken or "",
            width=460,
            password=True,
            can_reveal_password=True,
        )
        hoyolab_status_text = ft.Text("", size=12)

        def toggle_hoyolab(e):
            settings.hoyolab_enabled = hoyolab_switch.value
            _restart_hoyolab_service()

        hoyolab_switch.on_change = toggle_hoyolab

        def save_hoyolab_settings(e):
            ltuid_val = hoyolab_ltuid_field.value.strip()
            ltoken_val = hoyolab_ltoken_field.value.strip()

            if not ltuid_val or not ltoken_val:
                hoyolab_status_text.value = "⚠️ ltuid_v2 和 ltoken_v2 都必須填寫"
                hoyolab_status_text.color = ft.Colors.ORANGE_400
                page.update()
                return

            settings.hoyolab_ltuid = ltuid_val
            settings.hoyolab_ltoken = ltoken_val
            settings.hoyolab_enabled = True
            hoyolab_switch.value = True
            _restart_hoyolab_service()

            hoyolab_status_text.value = "✅ 已儲存 HoYoLab 設定"
            hoyolab_status_text.color = ft.Colors.GREEN_400
            page.update()

        def test_hoyolab(e):
            ltuid_val = hoyolab_ltuid_field.value.strip()
            ltoken_val = hoyolab_ltoken_field.value.strip()

            if not ltuid_val or not ltoken_val:
                hoyolab_status_text.value = "⚠️ 請先填寫 ltuid_v2 和 ltoken_v2"
                hoyolab_status_text.color = ft.Colors.ORANGE_400
                page.update()
                return

            hoyolab_status_text.value = "🔄 測試連線中..."
            hoyolab_status_text.color = ft.Colors.CYAN_400
            page.update()

            import threading
            def _do_test():
                test_svc = HoYoLabService(
                    ltuid=ltuid_val,
                    ltoken=ltoken_val,
                )
                result = test_svc.fetch_stamina()
                if result:
                    hoyolab_status_text.value = f"✅ 連線成功！開拓力：{result['current']} / {result['max']}"
                    hoyolab_status_text.color = ft.Colors.GREEN_400
                else:
                    hoyolab_status_text.value = "❌ 連線失敗，請檢查 ltuid_v2 和 ltoken_v2"
                    hoyolab_status_text.color = ft.Colors.RED_400
                try:
                    page.update()
                except Exception:
                    pass

            threading.Thread(target=_do_test, daemon=True).start()

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
                        ft.Text("HoYoLab API（星穹鐵道）", weight=ft.FontWeight.BOLD),
                        ft.Row([
                            ft.Text("啟用即時體力查詢"),
                            hoyolab_switch,
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        hoyolab_ltuid_field,
                        hoyolab_ltoken_field,
                        ft.Row([
                            ft.Button("測試連線", icon=ft.Icons.WIFI, on_click=test_hoyolab),
                            ft.Button("儲存", icon=ft.Icons.SAVE, on_click=save_hoyolab_settings),
                        ], spacing=8),
                        hoyolab_status_text,
                        ft.Text(
                            "💡 HoYoLab 登入後，從瀏覽器 DevTools → Application → Cookies 取得",
                            size=11,
                            color=ft.Colors.WHITE54,
                        ),
                        ft.Divider(),
                        ft.Text("其他設定", weight=ft.FontWeight.BOLD),
                        ft.TextButton("重置「關閉視窗」行為", on_click=reset_close_behavior),
                    ],
                    scroll=ft.ScrollMode.AUTO,
                ),
                width=500,
                height=500,
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
        process_monitor.stop()
        if state.get("hoyolab_service"):
            state["hoyolab_service"].stop()
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

    # 啟動進程監控
    if settings.process_monitor_enabled:
        process_monitor.watch_games(games)
        for game in games:
            if game.exe_path:
                process_monitor.on_process_exit(game.id, _make_exit_callback(game.id))
        process_monitor.start()

    # 啟動 HoYoLab 服務
    if state.get("hoyolab_service"):
        state["hoyolab_service"].start(
            interval=settings.hoyolab_interval,
            callback=on_hoyolab_update,
        )
        # 啟動時立即查詢一次
        import threading
        def _initial_hoyolab_fetch():
            svc = state.get("hoyolab_service")
            if svc:
                result = svc.fetch_stamina()
                if result:
                    on_hoyolab_update(result)
        threading.Thread(target=_initial_hoyolab_fetch, daemon=True).start()


if __name__ == "__main__":
    ft.app(main)
