import threading
import time
import sys
import os
from PIL import Image, ImageDraw
import pystray
from pynput import keyboard

# Import our custom modules
from overlay import ScreenOverlay
from results_gui import ResultsWindow
import config_manager
import customtkinter as ctk

class BoxToSearchApp:
    def __init__(self):
        self.overlay_active = False
        self.tray_icon = None
        self.hotkey_listener = None
        
        # Load configuration
        self.config = config_manager.load_config()
        self.hotkey_str = self.config.get("hotkey", "<ctrl>+<shift>+x")
        self.hotkey_display = self.config.get("hotkey_display", "Ctrl+Shift+X")
        
        # Initialize a hidden root window to serve as parent for all Tkinter/CustomTkinter windows
        self.root = ctk.CTk()
        self.root.app = self
        self.root.withdraw()
        
        # Set window icon (app_icon.ico)
        try:
            icon_path = config_manager.get_resource_path(os.path.join("assets", "icon", "app_icon.ico"))
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
            else:
                from PIL import ImageTk
                icon_img = self.create_tray_image()
                self.window_icon = ImageTk.PhotoImage(icon_img)
                self.root.iconphoto(False, self.window_icon)
        except Exception as e:
            print("Failed to set root window icon:", e)
        
        # Keep track of active results windows so we can close them on exit
        self.results_windows = []
        
    def create_tray_image(self):
        """
        Loads the app_icon.ico image for the tray.
        """
        icon_path = config_manager.get_resource_path(os.path.join("assets", "icon", "app_icon.ico"))
        if os.path.exists(icon_path):
            try:
                return Image.open(icon_path)
            except Exception as e:
                print("Failed to load app icon image:", e)
                
        # Fallback to drawn icon
        img = Image.new("RGBA", (64, 64), color=(0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rectangle([8, 8, 56, 56], outline="#00F0FF", width=4)
        draw.line([36, 36, 46, 46], fill="white", width=4)
        draw.ellipse([20, 20, 38, 38], outline="white", width=3)
        return img

    def launch_capture(self):
        """
        Launches the screen capture overlay if not already active.
        """
        if self.overlay_active:
            return
            
        self.overlay_active = True
        
        # Schedule on the main thread after a short delay
        def run_overlay():
            time.sleep(0.20)
            self.root.after(0, self._launch_overlay_main_thread)
            
        threading.Thread(target=run_overlay, daemon=True).start()

    def _launch_overlay_main_thread(self):
        try:
            ScreenOverlay(self.root, self.on_image_selected, self.on_overlay_close)
        except Exception as e:
            print(f"Error launching overlay: {e}")
            self.overlay_active = False

    def on_overlay_close(self):
        """
        Callback when the overlay closes/cancels without selection.
        """
        self.overlay_active = False

    def on_image_selected(self, cropped_image):
        """
        Callback when the user completes their screen selection.
        """
        self.overlay_active = False
        
        # Schedule results window creation on the main thread
        def run_results():
            results_win = ResultsWindow(self.root, cropped_image)
            self.results_windows.append(results_win)
            
        self.root.after(0, run_results)

    def show_help(self):
        """
        Shows helper notification about the global hotkey.
        """
        if self.tray_icon:
            self.tray_icon.notify(
                f"Press {self.hotkey_display} from any screen to activate Box to Search.\n"
                "Drag mouse to select area. Right-Click to cancel.",
                "How to Use"
            )

    def show_settings(self):
        """
        Opens the settings window on the main thread.
        """
        self.root.after(0, self._show_settings_main_thread)

    def _show_settings_main_thread(self):
        from settings_gui import SettingsWindow
        SettingsWindow(self.root, on_save_callback=self.reload_settings)

    def reload_settings(self):
        """
        Reloads the configuration from file and updates the hotkey binding on the fly.
        """
        self.config = config_manager.load_config()
        new_hotkey_str = self.config.get("hotkey", "<ctrl>+<shift>+x")
        new_hotkey_display = self.config.get("hotkey_display", "Ctrl+Shift+X")
        
        if new_hotkey_str == self.hotkey_str:
            return # No change in hotkey
            
        print(f"Updating global shortcut from {self.hotkey_display} to {new_hotkey_display}...")
        self.hotkey_str = new_hotkey_str
        self.hotkey_display = new_hotkey_display
        
        # Stop old listener
        if self.hotkey_listener:
            try:
                self.hotkey_listener.stop()
            except Exception:
                pass
                
        # Start new listener
        self.setup_hotkey()
        
        # Update tray title to reflect new hotkey
        if self.tray_icon:
            self.tray_icon.title = f"Box to Search ({self.hotkey_display})"
            self.tray_icon.notify(
                f"Shortcut updated to {self.hotkey_display}!",
                "Box to Search Windows"
            )

    def exit_app(self):
        """
        Cleans up and exits the application.
        """
        print("Shutting down Box to Search...")
        
        # Stop global hotkey listener
        if self.hotkey_listener:
            self.hotkey_listener.stop()
            
        # Stop tray icon
        if self.tray_icon:
            self.tray_icon.stop()
            
        # Force terminate remaining threads/windows
        os._exit(0)

    def setup_hotkey(self):
        """
        Registers the global keyboard hotkey listener in a background thread.
        """
        hotkey_dict = {
            self.hotkey_str: self.launch_capture
        }
        
        try:
            self.hotkey_listener = keyboard.GlobalHotKeys(hotkey_dict)
            self.hotkey_listener.start()
            print(f"Global hotkeys initialized. Listening for {self.hotkey_display}...")
        except Exception as e:
            print(f"Error registering hotkey {self.hotkey_str}: {e}")

    def run(self):
        """
        Initializes and runs the application.
        """
        # 1. Start hotkey listener
        self.setup_hotkey()
        
        # 2. Build tray menu
        menu = pystray.Menu(
            pystray.MenuItem("Capture Screen", lambda: self.launch_capture(), default=True),
            pystray.MenuItem("Settings", lambda: self.show_settings()),
            pystray.MenuItem("How to Use", lambda: self.show_help()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", lambda: self.exit_app())
        )
        
        # 3. Create tray icon
        self.tray_icon = pystray.Icon(
            "box_to_search_win",
            self.create_tray_image(),
            f"Box to Search ({self.hotkey_display})",
            menu
        )
        
        # 4. Show initial toast notification
        def notify_startup():
            time.sleep(1.0)
            self.tray_icon.notify(
                f"Box to Search is running in the system tray.\nPress {self.hotkey_display} to capture!",
                "Box to Search Windows"
            )
            
        threading.Thread(target=notify_startup, daemon=True).start()
        
        # 5. Start tray icon execution loop in a background thread
        threading.Thread(target=self.tray_icon.run, daemon=True).start()
        
        # 6. Start the main Tkinter event loop on the main thread (blocks main thread)
        self.root.mainloop()

if __name__ == "__main__":
    # Ensure working directory is the script directory (or executable directory if frozen)
    if getattr(sys, 'frozen', False):
        script_dir = os.path.dirname(sys.executable)
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    app = BoxToSearchApp()
    app.run()
