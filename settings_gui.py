import tkinter as tk
import customtkinter as ctk
import config_manager
import translator

# Configure customtkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class ScrollableDropdown(ctk.CTkToplevel):
    def __init__(self, attach_widget, values, command, fg_color="#1e1e1e", button_color="#1e1e1e", button_hover_color="#004aad", text_color="white"):
        super().__init__()
        self.attach_widget = attach_widget
        self.values = values
        self.command = command
        self.fg_color = fg_color
        self.button_color = button_color
        self.button_hover_color = button_hover_color
        self.text_color = text_color
        
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color=fg_color)
        
        # Position relative to attach widget
        self.attach_widget.update_idletasks()
        x = self.attach_widget.winfo_rootx()
        y = self.attach_widget.winfo_rooty() + self.attach_widget.winfo_height()
        w = self.attach_widget.winfo_width()
        
        h = min(200, len(self.values) * 32 + 10)
        self.geometry(f"{w}x{h}+{x}+{y}")
        
        self.frame = ctk.CTkScrollableFrame(
            self, 
            fg_color=fg_color, 
            corner_radius=4,
            scrollbar_button_color=button_color,
            scrollbar_button_hover_color=button_hover_color
        )
        self.frame.pack(fill="both", expand=True, padx=1, pady=1)
        
        for val in self.values:
            btn = ctk.CTkButton(
                self.frame,
                text=val,
                fg_color="transparent",
                hover_color=button_hover_color,
                text_color=text_color,
                anchor="center",
                corner_radius=4,
                height=30,
                font=ctk.CTkFont(family="Inter", size=13),
                command=lambda v=val: self.select_value(v)
            )
            btn.pack(fill="x", pady=1)
            
        self.grab_set()
        self.bind("<Button-1>", self.on_click_anywhere)
        
    def on_click_anywhere(self, event):
        x, y = event.x, event.y
        w = self.winfo_width()
        h = self.winfo_height()
        if x < 0 or x > w or y < 0 or y > h:
            self.destroy()
            
    def select_value(self, val):
        self.command(val)
        self.destroy()

    def focus_set(self):
        if self.winfo_exists():
            try:
                super().focus_set()
            except Exception:
                pass

    def destroy(self):
        if self.winfo_exists():
            try:
                super().destroy()
            except Exception:
                pass

class SettingsWindow:
    def __init__(self, parent, on_save_callback=None):
        self.on_save_callback = on_save_callback
        self.config = config_manager.load_config()
        self.languages = translator.get_languages()
        
        # Recording state
        self.is_recording = False
        self.recorded_hotkey = self.config.get("hotkey", "<ctrl>+<shift>+x")
        self.recorded_display = self.config.get("hotkey_display", "Ctrl+Shift+X")
        
        # 1. Window Setup
        self.root = ctk.CTkToplevel(parent)
        self.root.title("Box to Search - Settings")
        self.root.geometry("450x540")
        self.root.resizable(False, False)
        self.root.configure(fg_color="#0c0c0c")
        
        # Set window icon (blue box icon)
        try:
            import os
            icon_path = config_manager.get_resource_path(os.path.join("assets", "icon", "app_icon.ico"))
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
            else:
                from PIL import Image, ImageDraw, ImageTk
                icon_img = Image.new("RGBA", (64, 64), color=(0, 0, 0, 0))
                draw = ImageDraw.Draw(icon_img)
                draw.rectangle([8, 8, 56, 56], outline="#00F0FF", width=4)
                draw.line([36, 36, 46, 46], fill="white", width=4)
                draw.ellipse([20, 20, 38, 38], outline="white", width=3)
                
                self.window_icon = ImageTk.PhotoImage(icon_img)
                self.root.iconphoto(False, self.window_icon)
        except Exception as e:
            print("Failed to set settings window icon:", e)
        
        # Center the window
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 450) // 2
        y = (screen_height - 540) // 2
        self.root.geometry(f"+{x}+{y}")
        
        self.root.attributes("-topmost", True)
        self.root.after(1000, lambda: self.root.attributes("-topmost", False))
        
        # 2. UI Layout
        # Title Label
        self.title_label = ctk.CTkLabel(
            self.root, 
            text="Settings", 
            font=ctk.CTkFont(family="Inter", size=20, weight="bold"),
            text_color="white"
        )
        self.title_label.pack(pady=(20, 15))
        
        # Form Container
        self.form_frame = ctk.CTkFrame(self.root, corner_radius=12, fg_color="#121212")
        self.form_frame.pack(fill="both", expand=True, padx=24, pady=(0, 20))
        self.form_frame.columnconfigure(0, weight=40)
        self.form_frame.columnconfigure(1, weight=60)
        
        # --- Default Language ---
        self.lang_label = ctk.CTkLabel(
            self.form_frame, 
            text="Default Language:", 
            font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
            text_color="white"
        )
        self.lang_label.grid(row=0, column=0, padx=20, pady=16, sticky="w")
        
        self.lang_names = sorted(list(self.languages.keys()))
        default_code = self.config.get("default_language", "es")
        default_name = "spanish"
        for name, code in self.languages.items():
            if code == default_code:
                default_name = name
                break
                
        # Dropdown selection button acting as a menu trigger
        self.lang_dropdown = ctk.CTkButton(
            self.form_frame,
            text=f"{default_name.capitalize()}  ▼",
            width=200,
            height=34,
            corner_radius=6,
            fg_color="#1e1e1e",
            hover_color="#2a2a2a",
            text_color="white",
            font=ctk.CTkFont(family="Inter", size=13),
            anchor="center",
            command=self.show_language_dropdown
        )
        self.lang_dropdown.grid(row=0, column=1, padx=20, pady=16, sticky="e")
        
        # --- Shortcut Hotkey ---
        self.hotkey_label = ctk.CTkLabel(
            self.form_frame, 
            text="Shortcut Hotkey:", 
            font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
            text_color="white"
        )
        self.hotkey_label.grid(row=1, column=0, padx=20, pady=16, sticky="w")
        
        self.record_btn = ctk.CTkButton(
            self.form_frame,
            text=self.recorded_display,
            width=200,
            height=34,
            corner_radius=6,
            fg_color="#1e1e1e",
            hover_color="#2a2a2a",
            text_color="white",
            font=ctk.CTkFont(family="Inter", size=13),
            command=self.start_recording
        )
        self.record_btn.grid(row=1, column=1, padx=20, pady=16, sticky="e")
        
        # --- OCR Mode Selection ---
        self.ocr_mode_label = ctk.CTkLabel(
            self.form_frame,
            text="OCR Mode:",
            font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
            text_color="white"
        )
        self.ocr_mode_label.grid(row=2, column=0, padx=20, pady=16, sticky="w")
        
        current_mode = self.config.get("ocr_mode", "online").capitalize()
        self.ocr_mode_btn = ctk.CTkSegmentedButton(
            self.form_frame,
            values=["Offline", "Online"],
            width=200,
            height=32,
            fg_color="#1e1e1e",
            selected_color="#004aad",
            selected_hover_color="#0056c6",
            unselected_color="#1e1e1e",
            unselected_hover_color="#2a2a2a",
            text_color="white",
            font=ctk.CTkFont(family="Inter", size=13)
        )
        self.ocr_mode_btn.set(current_mode)
        self.ocr_mode_btn.grid(row=2, column=1, padx=20, pady=16, sticky="e")
        
        # --- Run on Startup Checkbox ---
        self.startup_var = ctk.BooleanVar(value=self.config.get("run_on_startup", False))
        self.startup_cb = ctk.CTkCheckBox(
            self.form_frame,
            text="Start on System Boot",
            variable=self.startup_var,
            font=ctk.CTkFont(family="Inter", size=13),
            fg_color="#004aad",
            hover_color="#0056c6",
            text_color="white",
            checkmark_color="white"
        )
        self.startup_cb.grid(row=3, column=0, columnspan=2, padx=20, pady=(4, 10), sticky="w")
        
        # --- OCR Mode Note ---
        self.ocr_note_label = ctk.CTkLabel(
            self.form_frame,
            text=(
                "Offline Mode: Requires local Windows language packs; struggles with stylized or low-contrast text.\n\n"
                "Online Mode: Requires active internet connection; higher latency; uploads screenshot data to OCR.space API."
            ),
            font=ctk.CTkFont(family="Inter", size=12),
            text_color="#a0a0a0",
            justify="left",
            wraplength=368
        )
        self.ocr_note_label.grid(row=4, column=0, columnspan=2, padx=20, pady=(4, 12), sticky="w")
        
        # --- Status / Instruction Label ---
        self.status_label = ctk.CTkLabel(
            self.form_frame,
            text="Global shortcut activates screen overlay.",
            font=ctk.CTkFont(family="Inter", size=11),
            text_color="white"
        )
        self.status_label.grid(row=5, column=0, columnspan=2, pady=(8, 16))
        
        # --- Buttons Footer ---
        self.footer_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.footer_frame.pack(fill="x", padx=24, pady=(0, 24))
        
        self.cancel_btn = ctk.CTkButton(
            self.footer_frame,
            text="Cancel",
            width=110,
            height=38,
            corner_radius=8,
            fg_color="#1e1e1e",
            hover_color="#2a2a2a",
            text_color="white",
            font=ctk.CTkFont(family="Inter", size=13),
            command=self.close
        )
        self.cancel_btn.pack(side="left")
        
        self.save_btn = ctk.CTkButton(
            self.footer_frame,
            text="Save Settings",
            width=130,
            height=38,
            corner_radius=8,
            fg_color="#004aad",
            hover_color="#0056c6",
            text_color="white",
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            command=self.save_settings
        )
        self.save_btn.pack(side="right")
        
        # Window closing handler
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        
        # Bind key events for recording
        self.root.bind("<KeyPress>", self.on_key_press)
        
    def start_recording(self):
        self.is_recording = True
        self.record_btn.configure(
            text="Press keys... (ESC to clear)", 
            fg_color="#004aad", 
            hover_color="#0056c6"
        )
        self.status_label.configure(
            text="Press modifiers (Ctrl, Alt, Shift) + key. ESC to cancel.",
            text_color="white"
        )
        
    def on_key_press(self, event):
        if not self.is_recording:
            return
            
        keysym = event.keysym
        
        # Handle cancel
        if keysym == "Escape":
            self.is_recording = False
            self.record_btn.configure(text=self.recorded_display, fg_color="#1e1e1e", hover_color="#2a2a2a")
            self.status_label.configure(text="Recording cancelled.", text_color="white")
            return
            
        # Check if the keysym itself is a modifier
        is_mod = keysym in (
            "Control_L", "Control_R", 
            "Shift_L", "Shift_R", 
            "Alt_L", "Alt_R", 
            "Win_L", "Win_R", "Super_L", "Super_R"
        )
        
        # Check active modifiers from the event state bitmask
        ctrl = bool(event.state & 0x0004) or "Control" in keysym
        shift = bool(event.state & 0x0001) or "Shift" in keysym
        alt = bool(event.state & 0x20000) or "Alt" in keysym
        win = bool(event.state & 0x0040) or "Win" in keysym or "Super" in keysym
        
        # If it is a modifier key, we update the placeholder text and wait for the target key
        if is_mod:
            parts = []
            if ctrl: parts.append("Ctrl")
            if alt: parts.append("Alt")
            if shift: parts.append("Shift")
            if win: parts.append("Win")
            self.record_btn.configure(text="+".join(parts) + " + ...")
            return
            
        # If it's a target key, we construct the final shortcut
        has_modifiers = ctrl or alt or shift or win
        if not has_modifiers:
            self.status_label.configure(
                text="Error: Shortcut must include a modifier (Ctrl, Alt, Shift, Win).",
                text_color="#EF4444"
            )
            return
            
        # Map target key names
        key_name = keysym.lower()
        if key_name == "space":
            key_name = "space"
        elif len(key_name) > 1 and not key_name.startswith("f"):
            # Tkinter returns names like "plus", "minus", "comma". We just take character if possible, or fallback.
            # Standard alphanumerics are len == 1, function keys start with 'f' (e.g. 'f1', 'f12').
            # We filter out other complex key names for stability.
            self.status_label.configure(
                text=f"Error: Key '{keysym}' not recommended for global shortcut.",
                text_color="#EF4444"
            )
            return
            
        # Construct strings
        pynput_parts = []
        display_parts = []
        
        if ctrl:
            pynput_parts.append("<ctrl>")
            display_parts.append("Ctrl")
        if alt:
            pynput_parts.append("<alt>")
            display_parts.append("Alt")
        if shift:
            pynput_parts.append("<shift>")
            display_parts.append("Shift")
        if win:
            pynput_parts.append("<cmd>")
            display_parts.append("Win")
            
        pynput_parts.append(key_name)
        display_parts.append(keysym.upper())
        
        self.recorded_hotkey = "+".join(pynput_parts)
        self.recorded_display = "+".join(display_parts)
        
        # Stop recording
        self.is_recording = False
        self.record_btn.configure(text=self.recorded_display, fg_color="#1e1e1e", hover_color="#2a2a2a")
        self.status_label.configure(text="Hotkey recorded! Click 'Save Settings' to apply.", text_color="white")

    def save_settings(self):
        dropdown_text = self.lang_dropdown.cget("text")
        selected_lang_name = dropdown_text.replace("  ▼", "").strip().lower()
        lang_code = self.languages.get(selected_lang_name, "es")
        
        selected_ocr_mode = self.ocr_mode_btn.get().lower()
        run_on_startup = self.startup_var.get()
        
        new_config = {
            "default_language": lang_code,
            "hotkey": self.recorded_hotkey,
            "hotkey_display": self.recorded_display,
            "ocr_mode": selected_ocr_mode,
            "run_on_startup": run_on_startup
        }
        
        config_manager.save_config(new_config)
        config_manager.set_run_on_startup(run_on_startup)
        
        if self.on_save_callback:
            self.on_save_callback()
            
        self.close()
        
    def show_language_dropdown(self):
        values = [name.capitalize() for name in self.lang_names]
        ScrollableDropdown(
            attach_widget=self.lang_dropdown,
            values=values,
            command=self.on_language_select
        )
        
    def on_language_select(self, val):
        self.lang_dropdown.configure(text=f"{val}  ▼")
        
    def close(self):
        self.root.destroy()

if __name__ == "__main__":
    def on_save():
        print("Settings saved callback triggered!")
    root = ctk.CTk()
    SettingsWindow(root, on_save)
    root.mainloop()
