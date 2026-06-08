import os
import json
import sys

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "default_language": "es",  # Spanish
    "hotkey": "<ctrl>+<shift>+x",
    "hotkey_display": "Ctrl+Shift+X",
    "ocr_mode": "online",
    "run_on_startup": False
}

def get_resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller.
    """
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def get_config_path():
    """
    Returns the absolute path to config.json in the executable directory.
    """
    if getattr(sys, 'frozen', False):
        script_dir = os.path.dirname(sys.executable)
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, CONFIG_FILE)

def is_run_on_startup_enabled():
    """
    Checks if the application is registered to run on startup in the Windows Registry.
    """
    if sys.platform != "win32":
        return False
    import winreg
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    app_name = "BoxToSearch"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
        try:
            value, _ = winreg.QueryValueEx(key, app_name)
            enabled = bool(value)
        except FileNotFoundError:
            enabled = False
        winreg.CloseKey(key)
        return enabled
    except Exception as e:
        print(f"Error checking run on startup registry: {e}")
        return False

def set_run_on_startup(enabled):
    """
    Registers or unregisters the application from system startup in the Windows Registry.
    """
    if sys.platform != "win32":
        return
    import winreg
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    app_name = "BoxToSearch"
    try:
        # Use KEY_WRITE to allow creating and deleting values under the key
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
        if enabled:
            if getattr(sys, 'frozen', False):
                app_path = f'"{sys.executable}"'
            else:
                script_dir = os.path.dirname(os.path.abspath(__file__))
                app_py_path = os.path.join(script_dir, "app.py")
                app_path = f'"{sys.executable}" "{app_py_path}"'
            
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, app_path)
            print(f"Added BoxToSearch to startup registry: {app_path}")
        else:
            try:
                winreg.DeleteValue(key, app_name)
                print("Removed BoxToSearch from startup registry.")
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
    except Exception as e:
        print(f"Error setting run on startup registry: {e}")


def load_config():
    """
    Loads configuration from config.json. If it does not exist, creates it with defaults.
    """
    path = get_config_path()
    if not os.path.exists(path):
        config = DEFAULT_CONFIG.copy()
        config["run_on_startup"] = is_run_on_startup_enabled()
        save_config(config)
        return config
        
    try:
        with open(path, "r", encoding="utf-8") as f:
            config = json.load(f)
            # Ensure all default keys exist
            updated = False
            for k, v in DEFAULT_CONFIG.items():
                if k not in config:
                    config[k] = v
                    updated = True
            
            # Sync run_on_startup with actual registry state
            registry_state = is_run_on_startup_enabled()
            if config.get("run_on_startup") != registry_state:
                config["run_on_startup"] = registry_state
                updated = True
                
            if updated:
                save_config(config)
            return config
    except Exception as e:
        print(f"Error reading config: {e}. Reverting to defaults.")
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()


def save_config(config):
    """
    Saves configuration to config.json.
    """
    path = get_config_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error writing config: {e}")

def load_custom_fonts():
    """
    Dynamically loads the application's custom fonts on Windows.
    """
    if sys.platform == "win32":
        try:
            import ctypes
            fonts_dir = get_resource_path(os.path.join("assets", "fonts"))
            font1 = os.path.join(fonts_dir, "ArchivoBlack-Regular.ttf")
            font2 = os.path.join(fonts_dir, "Inter-VariableFont_opsz,wght.ttf")
            
            FR_PRIVATE = 0x10
            gdi32 = ctypes.windll.gdi32
            
            if os.path.exists(font1):
                gdi32.AddFontResourceExW(font1, FR_PRIVATE, 0)
            if os.path.exists(font2):
                gdi32.AddFontResourceExW(font2, FR_PRIVATE, 0)
        except Exception as e:
            print(f"Error loading custom fonts: {e}")

# Load the custom fonts automatically upon module import
load_custom_fonts()
