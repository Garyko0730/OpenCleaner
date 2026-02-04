import flet as ft
import os
import plistlib
from pathlib import Path
import threading
import time
import subprocess
from datetime import datetime
from send2trash import send2trash

# --- 核心邏輯 ---

SEARCH_PATHS = [
    Path.home() / "Library/Application Support",
    Path.home() / "Library/Caches",
    Path.home() / "Library/Preferences",
    Path.home() / "Library/Saved Application State",
    Path.home() / "Library/Containers",
    Path.home() / "Library/Logs",
    Path.home() / "Library/Cookies",
    Path.home() / "Library/WebKit",
]

CACHE_DIR = Path("src/main/assets/icons")

class AppItem:
    def __init__(self, name, path):
        self.name = name
        self.path = path
        self.bundle_id = None
        self.leftovers = []
        self.total_size = 0
        self.icon_src = ""
        self.last_used = None
        self.last_used_str = "Unknown"

def get_bundle_info(app_path):
    """讀取 Bundle ID 和 圖標文件名"""
    info_plist = Path(app_path) / "Contents/Info.plist"
    if not info_plist.exists(): return None, None
    try:
        with open(info_plist, 'rb') as f:
            plist = plistlib.load(f)
            return plist.get("CFBundleIdentifier"), plist.get("CFBundleIconFile")
    except: return None, None

def extract_icon(app_path, icon_name, app_name):
    """使用 sips 將 .icns 轉為 .png"""
    if not icon_name: return None
    
    if not icon_name.endswith(".icns"): icon_name += ".icns"
    icns_path = Path(app_path) / "Contents/Resources" / icon_name
    
    if not icns_path.exists(): return None
    
    output_png = CACHE_DIR / f"{app_name}.png"
    if output_png.exists(): return str(output_png) # 已緩存
    
    try:
        # 使用 macOS 自帶的 sips 工具轉換
        subprocess.run(
            ["sips", "-s", "format", "png", str(icns_path), "--out", str(output_png), "--resampleHeightWidth", "64", "64"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return str(output_png)
    except:
        return None

def get_last_used_date(path):
    """使用 mdls 獲取最後打開時間"""
    try:
        result = subprocess.check_output(["mdls", "-name", "kMDItemLastUsedDate", "-raw", str(path)]).decode("utf-8").strip()
        if result == "(null)": return None
        # 格式: 2025-01-20 08:30:00 +0000
        dt = datetime.strptime(result.split(" +")[0], "%Y-%m-%d %H:%M:%S")
        return dt
    except:
        return None

def check_disk_permission():
    """檢查是否有完全磁盤訪問權限"""
    try:
        # 嘗試列出受保護目錄
        os.listdir(Path.home() / "Library/Safari")
        return True
    except (PermissionError, FileNotFoundError):
        return False

def find_leftovers(bundle_id, app_name):
    if not bundle_id: return []
    found_files = []
    keywords = {bundle_id.lower()}
    parts = bundle_id.split('.')
    if len(parts) >= 3:
        keywords.add(f"{parts[1]}.{parts[2]}".lower())
    clean_name = app_name.replace(" ", "").lower()
    
    for base_dir in SEARCH_PATHS:
        if not base_dir.exists(): continue
        try:
            for item in base_dir.iterdir():
                try:
                    name_lower = item.name.lower()
                    is_match = False
                    for k in keywords:
                        if k in name_lower: is_match = True; break
                    if not is_match and clean_name in name_lower: is_match = True
                    if is_match: found_files.append(item)
                except: pass
        except PermissionError: pass
    return found_files

def get_size(path):
    total = 0
    try:
        if path.is_file(): total = path.stat().st_size
        elif path.is_dir():
            for p in path.rglob('*'):
                if p.is_file(): total += p.stat().st_size
    except: pass
    return total

def format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024: return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"

# --- GUI 主程序 ---

def main(page: ft.Page):
    page.title = "OpenCleaner Pro Max"
    page.theme_mode = ft.ThemeMode.DARK
    page.window.width = 1100
    page.window.height = 760
    page.padding = 0
    
    # 風格定義
    BG_COLOR = "#111827"
    SIDEBAR_COLOR = "#1F2937"
    ACCENT_COLOR = "#3B82F6"
    TEXT_COLOR = "#F3F4F6"
    SUB_TEXT_COLOR = "#9CA3AF"
    
    # 狀態
    selected_app = None
    all_apps_data = []
    
    # --- 權限檢查 Banner ---
    perm_banner = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=ft.Colors.ORANGE_400),
            ft.Text("Full Disk Access Required for deep cleaning.", color=ft.Colors.ORANGE_100, size=12),
            ft.TextButton("How to fix?", style=ft.ButtonStyle(color=ft.Colors.ORANGE_400)) # 簡化，實際可鏈接教程
        ], alignment=ft.MainAxisAlignment.CENTER),
        bgcolor=ft.Colors.ORANGE_900,
        padding=5,
        visible=not check_disk_permission()
    )

    # --- 左側列表 ---
    search_box = ft.TextField(
        hint_text="Search...",
        prefix_icon=ft.Icons.SEARCH,
        border_radius=8,
        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
        border_width=0,
        text_size=13,
        content_padding=10,
        height=35,
        on_change=lambda e: apply_filters()
    )
    
    # 先定義 batch_switch
    def toggle_batch_mode(e):
        batch_bar.visible = e.control.value
        page.update()
        apply_filters()
        
    batch_switch = ft.Switch(label="Batch Mode", on_change=toggle_batch_mode, active_color=ACCENT_COLOR)

    # 過濾芯片 (移動到 batch_switch 定義之後)
    filter_group = ft.Row([
        ft.Chip(label=ft.Text("All"), selected=True, on_select=lambda e: toggle_filter(e, "all")),
        ft.Chip(label=ft.Text("Large (>1GB)"), on_select=lambda e: toggle_filter(e, "large")),
        ft.Chip(label=ft.Text("Unused (>30d)"), on_select=lambda e: toggle_filter(e, "unused")),
        batch_switch
    ], scroll=ft.ScrollMode.HIDDEN)
    
    current_filter = "all"

    def toggle_filter(e, filter_type):
        nonlocal current_filter
        # 簡單的互斥邏輯
        for c in filter_group.controls:
            c.selected = False
        e.control.selected = True
        current_filter = filter_type
        e.control.update()
        apply_filters()

    # --- 批量操作欄 (新) ---
    batch_bar = ft.Container(
        content=ft.Row([
            ft.Text("Batch Mode", weight=ft.FontWeight.BOLD),
            ft.TextButton("Select All", on_click=lambda e: select_all_batch(True)),
            ft.TextButton("Select None", on_click=lambda e: select_all_batch(False)),
            ft.Container(expand=True),
            ft.ElevatedButton("Delete Selected", bgcolor=ft.Colors.RED, color=ft.Colors.WHITE, on_click=lambda e: batch_delete(e))
        ]),
        padding=10,
        bgcolor=ft.Colors.BLUE_GREY_900,
        visible=False
    )
    
    app_list_view = ft.ListView(expand=True, spacing=2, padding=10)
    # ... (原有代碼 - 刪除重複的定義)
    
    def select_all_batch(select):
        for tile in app_list_view.controls:
            if hasattr(tile, 'trailing') and isinstance(tile.trailing, ft.Checkbox):
                tile.trailing.value = select
        page.update()
        
    def batch_delete(e):
        selected_apps = []
        for tile in app_list_view.controls:
             if hasattr(tile, 'trailing') and isinstance(tile.trailing, ft.Checkbox) and tile.trailing.value:
                 selected_apps.append(tile.data)
        
        if not selected_apps:
            page.show_snack_bar(ft.SnackBar(ft.Text("No apps selected!")))
            return
            
        # 批量刪除邏輯
        count = 0
        for app in selected_apps:
            try:
                send2trash(str(app.path))
                count += 1
            except: pass
        
        page.show_snack_bar(ft.SnackBar(ft.Text(f"Batch deleted {count} apps."), bgcolor=ft.Colors.GREEN))
        # 重新加載
        for app in selected_apps:
            if app in all_apps_data: all_apps_data.remove(app)
        apply_filters()

    # 修改列表渲染邏輯以支持批量
    # ... (需修改 apply_filters 中的 tile 創建代碼)
    detail_icon = ft.Image(src="", width=80, height=80, fit="contain", error_content=ft.Icon(ft.Icons.APPS, size=80, color=ACCENT_COLOR))
    detail_name = ft.Text("", size=28, weight=ft.FontWeight.BOLD, color=TEXT_COLOR)
    detail_meta = ft.Text("", size=12, color=SUB_TEXT_COLOR, font_family="monospace")
    detail_size = ft.Text("", size=16, color=ACCENT_COLOR, weight=ft.FontWeight.W_500)
    
    # 餅圖組件
    # Flet 0.80+ PieChart API 變更，暫時使用自定義繪製或文本替代以確保穩定性
    # 這裡我們用一個簡單的進度條和文本來可視化，直到適配新版圖表 API
    chart_info_text = ft.Text("Calculating space usage...", visible=False)
    usage_bar_app = ft.ProgressBar(value=0, color=ft.Colors.BLUE, bgcolor=ft.Colors.TRANSPARENT, expand=True)
    usage_bar_junk = ft.ProgressBar(value=0, color=ft.Colors.RED, bgcolor=ft.Colors.TRANSPARENT, expand=True)
    
    chart_container = ft.Container(
        content=ft.Column([
            chart_info_text,
            ft.Row([ft.Text("App:", size=10, width=40), usage_bar_app]),
            ft.Row([ft.Text("Junk:", size=10, width=40), usage_bar_junk]),
        ]),
        padding=10,
        visible=False,
        bgcolor=ft.Colors.WHITE10,
        border_radius=10
    )
    
    files_list = ft.ListView(expand=True, spacing=5, padding=10)
    
    uninstall_btn = ft.ElevatedButton(
        "Move to Trash",
        icon=ft.Icons.DELETE_OUTLINE,
        color=ft.Colors.WHITE,
        bgcolor=ft.Colors.RED_600,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), padding=15),
        visible=False,
        on_click=lambda e: uninstall_click(e)
    )

    # --- 邏輯方法 ---

    def apply_filters():
        query = search_box.value.lower() if search_box.value else ""
        app_list_view.controls.clear()
        
        filtered = []
        for app in all_apps_data:
            if query and query not in app.name.lower(): continue
            if current_filter == "large" and app.total_size < 1024 * 1024 * 1024: continue
            if current_filter == "unused" and app.last_used and (datetime.now() - app.last_used).days < 30: continue
            filtered.append(app)
            
        for app in filtered:
            leading_icon = ft.Icon(ft.Icons.APPS, color=ft.Colors.BLUE_GREY_400)
            if app.icon_src:
                leading_icon = ft.Image(src=app.icon_src, width=32, height=32, border_radius=5)
            
            # 批量模式：右側加複選框
            trailing_widget = None
            if batch_switch.value:
                trailing_widget = ft.Checkbox()
            else:
                trailing_widget = ft.Icon(ft.Icons.CHEVRON_RIGHT, size=16, color=ft.Colors.GREY_700)

            tile = ft.ListTile(
                leading=leading_icon,
                title=ft.Text(app.name, color=TEXT_COLOR, weight=ft.FontWeight.W_500),
                subtitle=ft.Text(f"{format_size(app.total_size)} • {app.last_used_str}", size=11, color=SUB_TEXT_COLOR),
                data=app,
                trailing=trailing_widget,
                on_click=on_app_select,
                shape=ft.RoundedRectangleBorder(radius=8),
                hover_color=ft.Colors.WHITE_10,
            )
            app_list_view.controls.append(tile)
        page.update()

    def load_apps_background():
        apps_dir = Path("/Applications")
        
        # 階段1: 快速掃描文件列表
        raw_apps = []
        for item in apps_dir.iterdir():
            if item.suffix == ".app":
                raw_apps.append(item)
        
        # 階段2: 逐個解析 (這一步比較慢，所以邊解析邊更新UI是個好主意，但這裡為了簡單，先批量解析一部分)
        # 優化：我們只在後台線程做解析，然後一次性更新列表，或者分批更新
        
        for app_path in raw_apps:
            app = AppItem(app_path.stem, app_path)
            
            # 獲取基礎信息
            app.bundle_id, icon_file = get_bundle_info(app_path)
            
            # 提取圖標
            if icon_file:
                app.icon_src = extract_icon(app_path, icon_file, app.name)
            
            # 獲取大小 (僅主程序，快速)
            app.total_size = get_size(app_path)
            
            # 獲取最後使用時間
            last_used = get_last_used_date(app_path)
            if last_used:
                app.last_used = last_used
                days = (datetime.now() - last_used).days
                if days == 0: app.last_used_str = "Today"
                else: app.last_used_str = f"{days}d ago"
            
            all_apps_data.append(app)
            
            # 每處理5個刷新一次UI，讓用戶感覺快
            if len(all_apps_data) % 5 == 0:
                apply_filters()
        
        # 排序：按名稱
        all_apps_data.sort(key=lambda x: x.name.lower())
        apply_filters()

    def on_app_select(e):
        nonlocal selected_app
        selected_app = e.control.data
        
        # UI 更新
        detail_name.value = selected_app.name
        detail_meta.value = f"{selected_app.path}\nLast Used: {selected_app.last_used_str}"
        detail_size.value = "Scanning leftovers..."
        
        if selected_app.icon_src:
            detail_icon.src = selected_app.icon_src
        else:
            detail_icon.src = "" # 觸發 error_content 顯示默認圖標
            
        uninstall_btn.visible = False
        files_list.controls.clear()
        files_list.controls.append(ft.ProgressBar(color=ACCENT_COLOR))
        page.update()
        
        threading.Thread(target=scan_leftovers_thread, args=(selected_app,), daemon=True).start()

    def scan_leftovers_thread(app):
        # 深入掃描
        leftovers = find_leftovers(app.bundle_id, app.name)
        app.leftovers = leftovers
        
        junk_size = sum(get_size(f) for f in leftovers)
        total_size = app.total_size + junk_size # app.total_size 已經是主程序大小
        
        # 更新圖表 (簡單版)
        chart_container.visible = True
        chart_info_text.visible = True
        if total_size > 0:
            app_ratio = app.total_size / total_size
            junk_ratio = junk_size / total_size
            usage_bar_app.value = app_ratio
            usage_bar_junk.value = junk_ratio
            chart_info_text.value = f"Space Distribution: App {int(app_ratio*100)}% | Junk {int(junk_ratio*100)}%"
        
        # 構建列表
        controls = []
        controls.append(ft.Text("APPLICATION", size=12, color=SUB_TEXT_COLOR, weight=ft.FontWeight.BOLD))
        controls.append(create_file_tile(app.path, app.total_size, is_main=True))
        
        if leftovers:
            controls.append(ft.Divider(color=ft.Colors.GREY_800))
            controls.append(ft.Row([
                ft.Text("SERVICE FILES", size=12, color=SUB_TEXT_COLOR, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=ft.Text(f"{len(leftovers)} items", size=10, color=ft.Colors.WHITE, bgcolor=ACCENT_COLOR, weight=ft.FontWeight.BOLD),
                    padding=ft.padding.symmetric(horizontal=6, vertical=2),
                    border_radius=10,
                    bgcolor=ACCENT_COLOR
                )
            ], spacing=5))
            
            for f in leftovers:
                controls.append(create_file_tile(f, get_size(f)))
        else:
            controls.append(ft.Text("No leftovers found.", color=ft.Colors.GREY_600, italic=True))

        detail_size.value = f"Total: {format_size(total_size)}"
        files_list.controls.clear()
        files_list.controls.extend(controls)
        uninstall_btn.visible = True
        uninstall_btn.text = f"Uninstall ({format_size(total_size)})"
        page.update()

    def create_file_tile(path, size, is_main=False):
        icon = ft.Icons.WEB_ASSET if is_main else ft.Icons.INSERT_DRIVE_FILE
        if not is_main and path.is_dir(): icon = ft.Icons.FOLDER
        color = ACCENT_COLOR if is_main else ft.Colors.GREY_500
        
        return ft.ListTile(
            leading=ft.Icon(icon, color=color, size=20),
            title=ft.Text(path.name, size=13, color=TEXT_COLOR),
            subtitle=ft.Text(str(path), size=10, color=ft.Colors.GREY_600, no_wrap=True),
            trailing=ft.Text(format_size(size), size=12, color=SUB_TEXT_COLOR),
            dense=True, content_padding=5
        )

    def uninstall_click(e):
        if not selected_app: return
        
        def confirm_delete(e):
            page.close_dialog()
            # 執行刪除
            deleted_count = 0
            # 刪主程序
            try:
                send2trash(str(selected_app.path))
                deleted_count += 1
            except Exception as ex:
                print(f"Error: {ex}")
            
            # 刪殘留
            for f in selected_app.leftovers:
                try:
                    send2trash(str(f))
                    deleted_count += 1
                except: pass
            
            page.show_snack_bar(ft.SnackBar(ft.Text(f"Moved {deleted_count} items to Trash."), bgcolor=ft.Colors.GREEN))
            
            # 刷新列表 (移除已刪除的)
            if selected_app in all_apps_data:
                all_apps_data.remove(selected_app)
            apply_filters()
            
            # 清空詳情
            detail_name.value = ""
            files_list.controls.clear()
            uninstall_btn.visible = False
            page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Uninstall App"),
            content=ft.Text(f"Move '{selected_app.name}' and all service files to Trash?"),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: page.close_dialog()),
                ft.TextButton("Trash It", on_click=confirm_delete, style=ft.ButtonStyle(color=ft.Colors.RED)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.dialog = dlg
        dlg.open = True
        page.update()

    # --- 布局結構 ---
    
    sidebar = ft.Container(
        content=ft.Column([
            ft.Container(search_box, padding=10),
            ft.Container(filter_group, padding=ft.padding.only(left=10, right=10, bottom=5)),
            batch_bar, # 插入批量操作欄
            ft.Divider(height=1, color=ft.Colors.GREY_800),
            app_list_view
        ], spacing=0),
        width=280,
        bgcolor=SIDEBAR_COLOR,
    )

    detail_panel = ft.Container(
        content=ft.Column([
            # Header
            ft.Container(
                content=ft.Row([
                    ft.Container(detail_icon, padding=5, bgcolor=ft.Colors.WHITE10, border_radius=15),
                    ft.Column([
                        detail_name,
                        detail_meta,
                        ft.Container(height=5),
                        detail_size
                    ], spacing=2, expand=True)
                ]),
                padding=20,
                bgcolor=ft.Colors.WHITE10
            ),
            # Charts
            chart_container,
            # Files
            files_list,
            # Footer
            ft.Container(
                content=ft.Row([
                    ft.Text("Safe Delete via Trash 🗑️", size=12, color=ft.Colors.GREY_600),
                    uninstall_btn
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=20,
                bgcolor=SIDEBAR_COLOR
            )
        ], spacing=0),
        expand=True,
        bgcolor=BG_COLOR
    )

    main_col = ft.Column([
        perm_banner,
        ft.Row([sidebar, ft.VerticalDivider(width=1, color=ft.Colors.BLACK), detail_panel], expand=True, spacing=0)
    ], expand=True, spacing=0)

    page.add(main_col)
    
    # 啟動後台掃描
    threading.Thread(target=load_apps_background, daemon=True).start()

ft.app(target=main)
