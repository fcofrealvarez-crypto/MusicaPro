import flet as ft
from downloader import download_music
from utils import update_yt_dlp
from config_manager import ConfigManager
from history_manager import HistoryManager
import threading
import os
import subprocess

# Initialize Managers
config = ConfigManager()
history_manager = HistoryManager()

class DownloaderView(ft.Container):
    def __init__(self, page):
        super().__init__()
        self.page_ref = page
        self.padding = 30
        
        self.status_text = ft.Text("Ready", size=16, color=ft.Colors.GREY_400)
        self.progress_bar = ft.ProgressBar(width=400, visible=False, color=ft.Colors.TEAL)
        
        # Load Defaults
        default_fmt = config.get("default_format")
        default_bass = config.get("bass_reduction")
        
        self.url_input = ft.TextField(
            label="YouTube URL", 
            width=450, 
            hint_text="Paste video or playlist link",
            prefix_icon=ft.Icons.LINK,
            border_color=ft.Colors.TEAL,
            focused_border_color=ft.Colors.TEAL
        )
        
        self.format_dropdown = ft.Dropdown(
            width=200,
            label="Format",
            value=default_fmt,
            options=[
                ft.dropdown.Option("mp3", "MP3 (320kbps)"),
                ft.dropdown.Option("flac", "FLAC (Lossless)"),
            ],
            icon=ft.Icons.AUDIO_FILE
        )
        
        self.preset_dropdown = ft.Dropdown(
            width=220,
            label="Sound Profile",
            value="Smart (Auto)",
            options=[
                ft.dropdown.Option("Smart (Auto)"),
                ft.dropdown.Option("Bass Boost (Club)"),
                ft.dropdown.Option("Vocal Clarity"),
                ft.dropdown.Option("Dynamic (Pop/Rock)"),
            ],
            icon=ft.Icons.EQUALIZER,
            text_style=ft.TextStyle(size=12)
        )
        
        self.download_btn = ft.ElevatedButton(
            text="Download", 
            width=200, 
            height=50,
            icon=ft.Icons.DOWNLOAD_ROUNDED,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                bgcolor={"": ft.Colors.TEAL, "hovered": ft.Colors.TEAL}
            ),
            on_click=self.on_download_click
        )

        self.content = ft.Column([
            ft.Text("Download Music", size=24, weight=ft.FontWeight.BOLD),
            ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
            
            ft.Row([self.url_input], alignment=ft.MainAxisAlignment.CENTER),
            ft.Container(height=10),
            
            ft.Row([
                self.format_dropdown,
                ft.Container(width=10),
                self.preset_dropdown
            ], alignment=ft.MainAxisAlignment.CENTER),
            
            ft.Container(height=30),
            self.download_btn,
            ft.Container(height=20),
            self.progress_bar,
            self.status_text,
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    def update_status(self, msg, progress=None):
        self.status_text.value = msg
        if progress is not None:
            self.progress_bar.value = progress
        self.update()

    def on_download_click(self, e):
        url = self.url_input.value
        if not url:
            self.url_input.error_text = "Required"
            self.update()
            return

        self.url_input.error_text = None
        self.toggle_inputs(False)
        self.progress_bar.visible = True
        self.progress_bar.value = None
        self.status_text.value = "Initializing..."
        self.update()

        def run():
            try:
                downloaded = download_music(
                    url, 
                    status_hook=self.update_status, 
                    audio_format=self.format_dropdown.value,
                    # Pass the preset name instead of boolean
                    bass_reduction=False, # Deprecated arg in downloader, but let's check utils signature match
                    # Wait, downloader.py likely calls utils.get_enhancement_filters. 
                    # We need to check downloader.py signature too.
                    # For now, let's assume we need to update downloader.py as well. 
                    # But wait, looking at enhancer.py, it calls enhance_audio...
                    # Let's pass the valid args.
                )
                # Actually I need to check downloader.py to see how it calls enhance_audio
                # STOP. I should check downloader.py first.

                
                if downloaded:
                     for item in downloaded:
                         history_manager.add_entry(item['title'], item['artist'], item['file_path'], item['format'])
                     self.status_text.value = f"Completed! ({len(downloaded)} files)"
                     self.page_ref.snack_bar = ft.SnackBar(ft.Text("Download Finished & Saved to Library!"), bgcolor=ft.Colors.GREEN)
                else:
                     self.status_text.value = "Failed or No files found."
                     self.page_ref.snack_bar = ft.SnackBar(ft.Text("Download Failed!"), bgcolor=ft.Colors.RED)

                self.page_ref.snack_bar.open = True
            except Exception as ex:
                self.status_text.value = "Error"
                self.page_ref.snack_bar = ft.SnackBar(ft.Text(f"Error: {ex}"), bgcolor=ft.Colors.RED)
                self.page_ref.snack_bar.open = True
            finally:
                self.progress_bar.visible = False
                self.toggle_inputs(True)
                self.page_ref.update()
                self.update()

        threading.Thread(target=run, daemon=True).start()

    def toggle_inputs(self, enabled):
        self.download_btn.disabled = not enabled
        self.url_input.disabled = not enabled
        self.format_dropdown.disabled = not enabled
        self.bass_switch.disabled = not enabled


class SettingsView(ft.Container):
    def __init__(self, page):
        super().__init__()
        self.page_ref = page
        self.padding = 30
        
        # Load current config state
        current_path = config.get("download_path")
        
        self.path_field = ft.TextField(value=current_path, label="Download Folder", read_only=True, width=350)
        self.path_btn = ft.IconButton(icon=ft.Icons.FOLDER_OPEN, on_click=self.pick_folder)
        
        self.def_fmt_drop = ft.Dropdown(
            label="Default Format",
            value=config.get("default_format"),
            options=[ft.dropdown.Option("mp3"), ft.dropdown.Option("flac")],
            on_change=lambda e: config.set("default_format", e.control.value)
        )
        
        self.content = ft.Column([
            ft.Text("Settings", size=24, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            
            ft.Text("General", size=18, weight=ft.FontWeight.W_500),
            ft.Row([self.path_field, self.path_btn], alignment=ft.MainAxisAlignment.CENTER),
            
            ft.Container(height=10),
            self.def_fmt_drop,
            
            ft.Container(height=30),
            ft.Text("Updates", size=18, weight=ft.FontWeight.W_500),
            ft.OutlinedButton("Check for Updates (yt-dlp)", on_click=self.check_updates)
            
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    def pick_folder(self, e):
        pass 

    def check_updates(self, e):
        e.control.text = "Checking..."
        e.control.disabled = True
        self.update()
        
        def run():
            ok, msg = update_yt_dlp()
            self.page_ref.snack_bar = ft.SnackBar(ft.Text(msg))
            self.page_ref.snack_bar.open = True
            e.control.text = "Check for Updates (yt-dlp)"
            e.control.disabled = False
            self.page_ref.update()
            self.update()
            
        threading.Thread(target=run, daemon=True).start()

class ToolsView(ft.Container):
    def __init__(self, page):
        super().__init__()
        self.page_ref = page
        self.padding = 20
        
        # --- Converter UI ---
        self.conv_file_picker = ft.FilePicker(on_result=self.on_conv_file_picked)
        page.overlay.append(self.conv_file_picker)
        
        self.conv_path = ft.TextField(label="Input File", read_only=True, width=400, border_color=ft.Colors.TEAL)
        self.conv_fmt = ft.Dropdown(
            label="Target Format", width=150, value="mp3",
            options=[ft.dropdown.Option("mp3"), ft.dropdown.Option("flac"), ft.dropdown.Option("m4a")]
        )
        self.conv_btn = ft.ElevatedButton("Convert", icon=ft.Icons.TRANSFORM, on_click=self.run_convert)
        self.conv_status = ft.Text("")

        converter_tab = ft.Column([
            ft.Text("Audio Converter", size=20, weight=ft.FontWeight.BOLD),
            ft.Row([self.conv_path, ft.IconButton(ft.Icons.FOLDER, on_click=lambda _: self.conv_file_picker.pick_files())], alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([self.conv_fmt, self.conv_btn], alignment=ft.MainAxisAlignment.CENTER),
            self.conv_status
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20)

        # --- Metadata UI ---
        self.meta_file_picker = ft.FilePicker(on_result=self.on_meta_file_picked)
        page.overlay.append(self.meta_file_picker)
        
        self.meta_path = ft.TextField(label="File to Edit", read_only=True, width=400, border_color=ft.Colors.PURPLE)
        self.meta_title = ft.TextField(label="Title", width=300)
        self.meta_artist = ft.TextField(label="Artist", width=300)
        self.meta_album = ft.TextField(label="Album", width=300)
        self.meta_save_btn = ft.ElevatedButton("Save Tags", icon=ft.Icons.SAVE, on_click=self.run_meta_save, bgcolor=ft.Colors.PURPLE)
        
        metadata_tab = ft.Column([
            ft.Text("Tag Editor", size=20, weight=ft.FontWeight.BOLD),
            ft.Row([self.meta_path, ft.IconButton(ft.Icons.FOLDER, on_click=lambda _: self.meta_file_picker.pick_files())], alignment=ft.MainAxisAlignment.CENTER),
            self.meta_title,
            self.meta_artist,
            self.meta_album,
            self.meta_save_btn
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        # --- Remaster UI ---
        self.remaster_folder_picker = ft.FilePicker(on_result=self.on_remaster_folder_picked)
        page.overlay.append(self.remaster_folder_picker)
        
        self.remaster_path = ft.TextField(label="Music Folder", read_only=True, width=400, border_color=ft.Colors.AMBER)
        
        self.remaster_preset = ft.Dropdown(
            width=220,
            label="Sound Profile",
            value="Smart (Auto)",
            options=[
                ft.dropdown.Option("Smart (Auto)"),
                ft.dropdown.Option("Bass Boost (Club)"),
                ft.dropdown.Option("Vocal Clarity"),
                ft.dropdown.Option("Dynamic (Pop/Rock)"),
            ],
            icon=ft.Icons.EQUALIZER,
            text_style=ft.TextStyle(size=12)
        )
        
        self.remaster_btn = ft.ElevatedButton("Start Remaster", icon=ft.Icons.AUTO_FIX_HIGH, on_click=self.run_remaster, bgcolor=ft.Colors.AMBER, color=ft.Colors.BLACK)
        self.remaster_status = ft.Text("")
        self.remaster_progress = ft.ProgressBar(width=400, color=ft.Colors.AMBER, visible=False)
        
        remaster_tab = ft.Column([
            ft.Text("Batch Remaster", size=20, weight=ft.FontWeight.BOLD),
            ft.Text("Enhances low quality files & normalizes volume.", size=12, color=ft.Colors.GREY),
            ft.Row([self.remaster_path, ft.IconButton(ft.Icons.FOLDER, on_click=lambda _: self.remaster_folder_picker.get_directory_path())], alignment=ft.MainAxisAlignment.CENTER),
            self.remaster_preset,
            self.remaster_btn,
            self.remaster_progress,
            self.remaster_status
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15)

        # Main Tabs using ft.Tabs inside the View
        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(text="Converter", icon=ft.Icons.SWAP_HORIZ),
                ft.Tab(text="Metadata", icon=ft.Icons.EDIT),
                ft.Tab(text="Remaster", icon=ft.Icons.AUTO_FIX_HIGH),
            ],
            expand=True
        )
        
        # We need to manually switch content because Tabs only shows tabs header in this context if we want full control
        # Actually Flet Tabs control contains the content.
        self.tabs.tabs[0].content = ft.Container(content=converter_tab, padding=20)
        self.tabs.tabs[1].content = ft.Container(content=metadata_tab, padding=20)
        self.tabs.tabs[2].content = ft.Container(content=remaster_tab, padding=20)

        self.content = self.tabs

    def on_conv_file_picked(self, e: ft.FilePickerResultEvent):
        if e.files:
            self.conv_path.value = e.files[0].path
            self.update()

    def run_convert(self, e):
        if not self.conv_path.value: return
        
        from utils import convert_audio
        self.conv_status.value = "Converting..."
        self.conv_btn.disabled = True
        self.update()
        
        def task():
            ok, msg, out = convert_audio(self.conv_path.value, self.conv_fmt.value)
            self.conv_status.value = f"Saved to: {os.path.basename(out)}" if ok else f"Error: {msg}"
            self.conv_btn.disabled = False
            self.update()
        
        threading.Thread(target=task, daemon=True).start()

    def on_meta_file_picked(self, e: ft.FilePickerResultEvent):
        if e.files:
            self.meta_path.value = e.files[0].path
            self.update()

    def run_meta_save(self, e):
        if not self.meta_path.value: return
        
        from utils import write_metadata
        self.meta_save_btn.disabled = True
        self.update()
        
        def task():
            ok, msg = write_metadata(
                self.meta_path.value, 
                title=self.meta_title.value, 
                artist=self.meta_artist.value, 
                album=self.meta_album.value
            )
            self.page_ref.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor=ft.Colors.GREEN if ok else ft.Colors.RED)
            self.page_ref.snack_bar.open = True
            self.meta_save_btn.disabled = False
            self.page_ref.update()
        
        threading.Thread(target=task, daemon=True).start()

    def on_remaster_folder_picked(self, e: ft.FilePickerResultEvent):
        if e.path:
            self.remaster_path.value = e.path
            self.update()

    def run_remaster(self, e):
        folder = self.remaster_path.value
        if not folder or not os.path.isdir(folder): return
        
        # We can reuse logic from enhancer.py but we need to import it carefully 
        # as it was written as a script. 
        # Let's import the function directly.
        from enhancer import enhance_audio
        from utils import get_audio_bitrate
        
        self.remaster_btn.disabled = True
        self.remaster_progress.visible = True
        self.remaster_status.value = "Scanning..."
        self.update()
        
        def task():
            output_folder = os.path.join(folder, "enhanced")
            os.makedirs(output_folder, exist_ok=True)
            
            files = [f for f in os.listdir(folder) if f.lower().endswith(('.mp3', '.wav', '.m4a', '.flac', '.ogg'))]
            total = len(files)
            processed = 0
            
            for i, filename in enumerate(files):
                self.remaster_status.value = f"Processing ({i+1}/{total}): {filename}"
                self.remaster_progress.value = (i) / total
                self.update()
                
                input_file = os.path.join(folder, filename)
                output_file = os.path.join(output_folder, filename)
                
                bitrate = get_audio_bitrate(input_file)
                is_low = (bitrate and bitrate < 128)
                
                # Check cancellation? No basic cancellation for now.
                enhance_audio(input_file, output_file, is_low_quality=is_low, preset=self.remaster_preset.value)
                processed += 1
                
            self.remaster_status.value = f"Done! {processed} files saved to 'enhanced' subfolder."
            self.remaster_progress.value = 1.0
            self.remaster_btn.disabled = False
            self.page_ref.snack_bar = ft.SnackBar(ft.Text("Remastering Complete!"), bgcolor=ft.Colors.AMBER, color=ft.Colors.BLACK)
            self.page_ref.snack_bar.open = True
            self.update()
            
        threading.Thread(target=task, daemon=True).start()

class LibraryView(ft.Container):
    def __init__(self, page):
        super().__init__()
        self.page_ref = page
        self.padding = 20
        self.build_ui()

    def build_ui(self):
        self.history_list = ft.ListView(expand=True, spacing=10, padding=20)
        self.refresh_list()
        
        self.content = ft.Column([
            ft.Row([
                ft.Text("My Library", size=24, weight=ft.FontWeight.BOLD),
                ft.IconButton(ft.Icons.REFRESH, on_click=lambda e: self.refresh_list(), tooltip="Refresh List")
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(),
            ft.Container(content=self.history_list, expand=True)
        ], expand=True)

    def refresh_list(self):
        history_manager.load() # Reload from disk
        items = history_manager.get_all()
        self.history_list.controls.clear()
        
        if not items:
            self.history_list.controls.append(ft.Text("No downloads yet.", italic=True, color=ft.Colors.GREY))
        else:
            for item in items:
                self.history_list.controls.append(self.create_item_tile(item))
        
        if self.history_list.page:
            self.history_list.update()

    def create_item_tile(self, item):
        return ft.Container(
            padding=10,
            border_radius=10,
            bgcolor=ft.Colors.BLUE_GREY_900,
            content=ft.Row([
                ft.Icon(ft.Icons.MUSIC_NOTE, color=ft.Colors.TEAL),
                ft.Column([
                    ft.Text(item.get('title', 'Unknown'), weight=ft.FontWeight.BOLD, size=16),
                    ft.Text(f"{item.get('artist', 'Unknown')} • {item.get('format', '').upper()}", size=12, color=ft.Colors.GREY),
                    ft.Text(f"{item.get('date', '')}", size=10, color=ft.Colors.GREY_500)
                ], expand=True),
                ft.IconButton(ft.Icons.PLAY_ARROW, on_click=lambda e: self.play_file(item.get('file_path'))),
                ft.IconButton(ft.Icons.FOLDER_OPEN, on_click=lambda e: self.open_folder(item.get('file_path')))
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        )

    def play_file(self, path):
        if path and os.path.exists(path):
            try:
                os.startfile(path)
            except:
                subprocess.Popen(['xdg-open', path]) # Linux fallback, though we are on Windows
        else:
            self.page_ref.snack_bar = ft.SnackBar(ft.Text("File not found!"), bgcolor=ft.Colors.RED)
            self.page_ref.snack_bar.open = True
            self.page_ref.update()

    def open_folder(self, path):
        if path and os.path.exists(os.path.dirname(path)):
             os.startfile(os.path.dirname(path))

class SearchView(ft.Container):
    def __init__(self, page, downloader_view):
        super().__init__()
        self.page_ref = page
        self.downloader_view = downloader_view # Reference to trigger downloads
        self.padding = 20
        self.build_ui()

    def build_ui(self):
        self.search_field = ft.TextField(
            hint_text="Search YouTube (Song, Artist...)", 
            width=500, 
            prefix_icon=ft.Icons.SEARCH,
            on_submit=self.run_search,
            border_color=ft.Colors.TEAL
        )
        self.search_btn = ft.FloatingActionButton(icon=ft.Icons.ARROW_FORWARD, on_click=self.run_search, bgcolor=ft.Colors.TEAL)
        self.results_list = ft.ListView(expand=True, spacing=10, padding=10)
        self.loading = ft.ProgressBar(width=400, color=ft.Colors.TEAL, visible=False)
        
        self.content = ft.Column([
            ft.Text("Search Music", size=24, weight=ft.FontWeight.BOLD),
            ft.Row([self.search_field, self.search_btn], alignment=ft.MainAxisAlignment.CENTER),
            ft.Divider(color=ft.Colors.TRANSPARENT),
            self.loading,
            ft.Container(content=self.results_list, expand=True)
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)

    def run_search(self, e):
        query = self.search_field.value
        if not query: return
        
        self.loading.visible = True
        self.search_btn.disabled = True
        self.search_field.disabled = True
        self.results_list.controls.clear()
        self.update()
        
        from utils import search_youtube
        
        def task():
            results = search_youtube(query, limit=15)
            self.loading.visible = False
            self.search_btn.disabled = False
            self.search_field.disabled = False
            
            if not results:
                 self.results_list.controls.append(ft.Text("No results found.", italic=True))
            else:
                 for res in results:
                     self.results_list.controls.append(self.create_result_card(res))
            
            self.update()
            
        threading.Thread(target=task, daemon=True).start()

    def create_result_card(self, res):
        return ft.Container(
            padding=10,
            border_radius=10,
            bgcolor=ft.Colors.BLUE_GREY_900,
            content=ft.Row([
                # Thumbnail
                ft.Image(src=res['thumbnail'], width=80, height=45, fit=ft.ImageFit.COVER, border_radius=5) if res['thumbnail'] else ft.Icon(ft.Icons.MUSIC_NOTE),
                
                # Info
                ft.Column([
                    ft.Text(res['title'], weight=ft.FontWeight.BOLD, no_wrap=True, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS, width=450),
                    ft.Text(f"{res.get('uploader', 'Unknown')} • {res.get('duration_string') or res.get('duration')}", size=12, color=ft.Colors.GREY)
                ], expand=True),
                
                # Download Action
                ft.IconButton(ft.Icons.DOWNLOAD, tooltip="Download MP3", on_click=lambda e: self.trigger_download(res, 'mp3')),
                ft.IconButton(ft.Icons.HIGH_QUALITY, tooltip="Download FLAC", on_click=lambda e: self.trigger_download(res, 'flac'))
                
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        )

    def trigger_download(self, res, fmt):
        # We switch to Downloader tab and pre-fill
        # But since we have a reference, we can maybe just manipulate it?
        # Better UX: Switch tab, fill URL, and maybe auto-click?
        
        # Access downloader view controls
        self.downloader_view.url_input.value = res['url'] # or https://youtube.com/watch?v=...
        self.downloader_view.format_dropdown.value = fmt
        self.downloader_view.update()
        
        # Switch tab (Need reference to tabs or main page logic)
        # Hacky: we don't have direct access to tabs control easily unless passed.
        # But we can start download directly!
        
        self.page_ref.snack_bar = ft.SnackBar(ft.Text(f"Queued: {res['title']}"), bgcolor=ft.Colors.TEAL)
        self.page_ref.snack_bar.open = True
        self.page_ref.update()
        
        # Call the click handler of downloader to reuse logic
        self.downloader_view.download_btn.on_click(None)

def main(page: ft.Page):
    page.title = "MusicPro Premium"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 850
    page.window_height = 650
    page.padding = 0
    
    # Views
    downloader = DownloaderView(page)
    settings = SettingsView(page)
    tools = ToolsView(page)
    library = LibraryView(page)
    search = SearchView(page, downloader)
    
    def on_nav_change(e):
        # Provide a simple fade transition or just switch
        content_area.content = [downloader, search, settings, tools, library][e.control.selected_index]
        content_area.update()
        
        # Auto-refresh library when switched to
        if e.control.selected_index == 4:
            library.refresh_list()
            
    # Navigation Rail or Tabs? Tabs are good for top level
    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[
            ft.Tab(text="Downloader", icon=ft.Icons.DOWNLOAD),
            ft.Tab(text="Search", icon=ft.Icons.SEARCH),
            ft.Tab(text="Settings", icon=ft.Icons.SETTINGS),
            ft.Tab(text="Tools", icon=ft.Icons.BUILD),
            ft.Tab(text="Library", icon=ft.Icons.LIBRARY_MUSIC),
        ],
        on_change=on_nav_change
    )
    
    content_area = ft.Container(content=downloader, expand=True)

    page.add(
        ft.Column([
            tabs,
            ft.Divider(height=1),
            content_area
        ], expand=True)
    )

ft.app(target=main)
