import threading
import os
import tempfile
import webbrowser
import requests
import customtkinter as ctk
from PIL import Image, ImageTk
import win32com.client
import ocr_engine
import translator
import config_manager
from tkinter import filedialog
import tkinter as tk


# Configure customtkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class ScrollableDropdown(ctk.CTkToplevel):
    def __init__(self, attach_widget, values, command, fg_color="#1e1e24", button_color="#1e1e24", button_hover_color="#004aad", text_color="white"):
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

class ResultsWindow:
    def __init__(self, parent, cropped_image):
        self.parent = parent
        self.image = cropped_image
        self.ocr_text = ""
        self.languages = translator.get_languages()
        self.config = config_manager.load_config()
        self.is_speaking = False
        self.speaker = None
        
        # Load custom button icons
        import os
        import sys
        
        def get_resource_path(relative_path):
            try:
                base_path = sys._MEIPASS
            except AttributeError:
                base_path = os.path.dirname(os.path.abspath(__file__))
            return os.path.join(base_path, relative_path)
            
        icon_dir = get_resource_path(os.path.join("assets", "icon"))
        
        try:
            search_pil = Image.open(os.path.join(icon_dir, "image_search_icon.ico"))
            self.search_icon = ctk.CTkImage(light_image=search_pil, dark_image=search_pil, size=(20, 20))
        except Exception:
            self.search_icon = None
            
        try:
            save_pil = Image.open(os.path.join(icon_dir, "save_icon.ico"))
            self.save_icon = ctk.CTkImage(light_image=save_pil, dark_image=save_pil, size=(20, 20))
        except Exception:
            self.save_icon = None
            
        try:
            read_pil = Image.open(os.path.join(icon_dir, "readaloud_icon.ico"))
            self.read_icon = ctk.CTkImage(light_image=read_pil, dark_image=read_pil, size=(20, 20))
        except Exception:
            self.read_icon = None

        try:
            retry_pil = Image.open(os.path.join(icon_dir, "retry_icon.ico"))
            self.retry_icon = ctk.CTkImage(light_image=retry_pil, dark_image=retry_pil, size=(16, 16))
        except Exception:
            self.retry_icon = None

        try:
            copy_pil = Image.open(os.path.join(icon_dir, "copy_icon.ico"))
            self.copy_icon = ctk.CTkImage(light_image=copy_pil, dark_image=copy_pil, size=(16, 16))
        except Exception:
            self.copy_icon = None
            
        # 1. Main Window Setup
        self.root = ctk.CTkToplevel(parent)
        self.root.title("Box to Search")
        self.root.geometry("1100x700")
        self.root.configure(fg_color="#0c0c0c")
        
        # Set window icon
        try:
            icon_path = get_resource_path(os.path.join("assets", "icon", "app_icon.ico"))
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
                # Ensure the icon is applied after window mapping to override customtkinter defaults
                self.root.after(200, lambda: self.root.iconbitmap(icon_path) if self.root.winfo_exists() else None)
            else:
                from PIL import ImageDraw
                icon_img = Image.new("RGBA", (64, 64), color=(0, 0, 0, 0))
                draw = ImageDraw.Draw(icon_img)
                draw.rectangle([8, 8, 56, 56], outline="#00F0FF", width=4)
                draw.line([36, 36, 46, 46], fill="white", width=4)
                draw.ellipse([20, 20, 38, 38], outline="white", width=3)
                self.window_icon = ImageTk.PhotoImage(icon_img)
                self.root.iconphoto(False, self.window_icon)
        except Exception as e:
            print("Failed to set window icon:", e)
            
        # Center the window on the screen
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 1100) // 2
        y = (screen_height - 700) // 2
        self.root.geometry(f"+{x}+{y}")
        
        self.root.attributes("-topmost", True)
        self.root.after(1000, lambda: self.root.attributes("-topmost", False))
        
        # Disable manual drag-resizing but allow maximize on Windows
        if sys.platform == "win32":
            try:
                import ctypes
                self.root.update()
                hwnd = int(self.root.wm_frame(), 0)
                GWL_STYLE = -16
                WS_THICKFRAME = 0x00040000
                SWP_NOMOVE = 0x0002
                SWP_NOSIZE = 0x0001
                SWP_NOZORDER = 0x0004
                SWP_FRAMECHANGED = 0x0020
                
                user32 = ctypes.windll.user32
                style = user32.GetWindowLongW(hwnd, GWL_STYLE)
                new_style = style & ~WS_THICKFRAME
                user32.SetWindowLongW(hwnd, GWL_STYLE, new_style)
                user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED)
            except Exception as e:
                print("Failed to apply Win32 style adjustments:", e)
                
        # Main Grid Layout:
        # Row 0: Top Header bar (burger menu, title)
        # Row 1: Content frame
        # Row 2: Status bar
        self.root.rowconfigure(0, minsize=50)
        self.root.rowconfigure(1, weight=1)
        self.root.rowconfigure(2, minsize=35)
        self.root.columnconfigure(0, weight=1)
        
        # --- HEADER BAR ---
        self.header_bar = ctk.CTkFrame(self.root, height=50, corner_radius=0, fg_color="transparent")
        self.header_bar.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 0))
        
        self.burger_btn = ctk.CTkButton(
            self.header_bar,
            text="☰",
            width=36,
            height=36,
            fg_color="transparent",
            hover_color="#18181b",
            text_color="white",
            font=ctk.CTkFont(size=20),
            command=self.show_burger_menu
        )
        self.burger_btn.pack(side="left")
        
        self.burger_menu = tk.Menu(self.root, tearoff=0, bg="#1e1e24", fg="white", activebackground="#2563eb", activeforeground="white", bd=1)
        self.burger_menu.add_command(label="Settings", command=self.open_settings)

        
        self.header_title = ctk.CTkLabel(
            self.header_bar,
            text="OCR Tool",
            font=ctk.CTkFont(family="ArchivoBlack", size=20, weight="bold"),
            text_color="white"
        )
        self.header_title.pack(side="left", padx=15)
        
        # --- CONTENT FRAME ---
        self.content_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(10, 10))
        self.content_frame.columnconfigure(0, weight=35, minsize=340)
        self.content_frame.columnconfigure(1, weight=65, minsize=500)
        self.content_frame.rowconfigure(0, weight=1)
        
        # --- LEFT COLUMN ("Image" Card) ---
        self.image_card = ctk.CTkFrame(self.content_frame, corner_radius=12, fg_color="#151518", border_width=1, border_color="#222225")
        self.image_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.image_card.columnconfigure(0, weight=1)
        self.image_card.rowconfigure(1, weight=1) # The image preview takes up space
        
        self.image_title_label = ctk.CTkLabel(
            self.image_card,
            text="Image",
            font=ctk.CTkFont(family="ArchivoBlack", size=18, weight="bold"),
            text_color="white"
        )
        self.image_title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        # Image Preview Frame
        self.preview_container = ctk.CTkFrame(self.image_card, corner_radius=8, fg_color="#0e0e11", border_width=1, border_color="#2c2c30")
        self.preview_container.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.preview_container.bind("<Button-1>", lambda e: self.browse_image())
        
        # Action Buttons Container
        self.actions_container = ctk.CTkFrame(self.image_card, fg_color="transparent")
        self.actions_container.grid(row=2, column=0, padx=20, pady=(10, 20), sticky="ew")
        
        self.web_search_btn = ctk.CTkButton(
            self.actions_container,
            text="Search Image on Web",
            image=self.search_icon,
            font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
            height=40,
            corner_radius=8,
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            text_color="white",
            command=self.trigger_web_search
        )
        self.web_search_btn.pack(fill="x", pady=5)
        
        self.save_img_btn = ctk.CTkButton(
            self.actions_container,
            text="Save Image",
            image=self.save_icon,
            font=ctk.CTkFont(family="Inter", size=14),
            height=40,
            corner_radius=8,
            fg_color="#24242b",
            hover_color="#2f2f3a",
            text_color="white",
            command=self.save_image
        )
        self.save_img_btn.pack(fill="x", pady=5)
        
        self.tts_btn = ctk.CTkButton(
            self.actions_container,
            text="Read Extracted Text",
            image=self.read_icon,
            font=ctk.CTkFont(family="Inter", size=14),
            height=40,
            corner_radius=8,
            fg_color="#24242b",
            hover_color="#2f2f3a",
            text_color="white",
            command=self.speak_text
        )
        self.tts_btn.pack(fill="x", pady=5)
        
        # --- RIGHT COLUMN (OCR & Translate) ---
        self.right_column_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.right_column_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        self.right_column_frame.columnconfigure(0, weight=1)
        self.right_column_frame.rowconfigure(0, weight=1) # OCR Card
        self.right_column_frame.rowconfigure(1, weight=1) # Translate Card
        
        # 1. OCR CARD
        self.ocr_card = ctk.CTkFrame(self.right_column_frame, corner_radius=12, fg_color="#151518", border_width=1, border_color="#222225")
        self.ocr_card.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        self.ocr_card.columnconfigure(0, weight=1)
        self.ocr_card.rowconfigure(1, weight=1)
        
        self.ocr_header_frame = ctk.CTkFrame(self.ocr_card, fg_color="transparent")
        self.ocr_header_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        
        self.ocr_title = ctk.CTkLabel(
            self.ocr_header_frame,
            text="Extracted Text",
            font=ctk.CTkFont(family="ArchivoBlack", size=18, weight="bold"),
            text_color="white"
        )
        self.ocr_title.pack(side="left")
        
        self.copy_ocr_btn = ctk.CTkButton(
            self.ocr_header_frame,
            text="Copy",
            image=self.copy_icon,
            width=70,
            height=28,
            corner_radius=6,
            fg_color="transparent",
            hover_color="#24242b",
            text_color="white",
            font=ctk.CTkFont(family="Inter", size=14),
            command=self.copy_ocr_to_clipboard
        )
        self.copy_ocr_btn.pack(side="right", padx=(5, 0))
        
        self.retry_ocr_btn = ctk.CTkButton(
            self.ocr_header_frame,
            text="Retry",
            image=self.retry_icon,
            width=70,
            height=28,
            corner_radius=6,
            fg_color="transparent",
            hover_color="#24242b",
            text_color="white",
            font=ctk.CTkFont(family="Inter", size=14),
            command=self.retry_ocr
        )
        self.retry_ocr_btn.pack(side="right")
        
        self.ocr_textbox = ctk.CTkTextbox(
            self.ocr_card,
            font=ctk.CTkFont(family="Inter", size=14),
            fg_color="#0e0e11",
            text_color="#666",
            border_color="#222225",
            corner_radius=8,
        )
        self.ocr_textbox.insert("1.0", "Extracted text will appear here...")
        self.ocr_textbox.configure(state="disabled")
        self.ocr_textbox.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        
        # 2. TRANSLATE CARD
        self.trans_card = ctk.CTkFrame(self.right_column_frame, corner_radius=12, fg_color="#151518", border_width=1, border_color="#222225")
        self.trans_card.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        self.trans_card.columnconfigure(0, weight=1)
        self.trans_card.rowconfigure(2, weight=1)
        
        self.trans_header_frame = ctk.CTkFrame(self.trans_card, fg_color="transparent")
        self.trans_header_frame.grid(row=0, column=0, padx=20, pady=(20, 5), sticky="ew")
        
        self.trans_title = ctk.CTkLabel(
            self.trans_header_frame,
            text="Translate",
            font=ctk.CTkFont(family="ArchivoBlack", size=18, weight="bold"),
            text_color="white"
        )
        self.trans_title.pack(side="left")
        
        self.copy_trans_btn = ctk.CTkButton(
            self.trans_header_frame,
            text="Copy",
            image=self.copy_icon,
            width=70,
            height=28,
            corner_radius=6,
            fg_color="transparent",
            hover_color="#24242b",
            text_color="white",
            font=ctk.CTkFont(family="Inter", size=14),
            command=self.copy_trans_to_clipboard
        )
        self.copy_trans_btn.pack(side="right", padx=(5, 0))
        
        self.retry_trans_btn = ctk.CTkButton(
            self.trans_header_frame,
            text="Retry",
            image=self.retry_icon,
            width=70,
            height=28,
            corner_radius=6,
            fg_color="transparent",
            hover_color="#24242b",
            text_color="white",
            font=ctk.CTkFont(family="Inter", size=14),
            command=self.trigger_translation
        )
        self.retry_trans_btn.pack(side="right")
        
        # Translation Dropdown Controls
        self.trans_control_frame = ctk.CTkFrame(self.trans_card, fg_color="transparent")
        self.trans_control_frame.grid(row=1, column=0, padx=20, pady=(5, 10), sticky="w")
        
        self.to_label = ctk.CTkLabel(
            self.trans_control_frame,
            text="To",
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            text_color="#aaa"
        )
        self.to_label.pack(side="left", padx=(0, 10))
        
        default_code = self.config.get("default_language", "es")
        default_name = "spanish"
        for name, code in self.languages.items():
            if code == default_code:
                default_name = name
                break
                
        self.lang_dropdown = ctk.CTkButton(
            self.trans_control_frame,
            text=f"{default_name.capitalize()}  ▼",
            width=140,
            height=28,
            corner_radius=6,
            fg_color="#1e1e24",
            hover_color="#2a2a35",
            text_color="white",
            font=ctk.CTkFont(family="Inter", size=12),
            anchor="center",
            command=self.show_language_dropdown
         )
        self.lang_dropdown.pack(side="left")
        
        self.trans_textbox = ctk.CTkTextbox(
            self.trans_card,
            font=ctk.CTkFont(family="Inter", size=14),
            fg_color="#0e0e11",
            text_color="#666",
            border_color="#222225",
            corner_radius=8,
        )
        self.trans_textbox.insert("1.0", "Translated text will appear here...")
        self.trans_textbox.configure(state="disabled")
        self.trans_textbox.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="nsew")
        
        # --- STATUS BAR ---
        self.status_bar = ctk.CTkFrame(self.root, height=35, corner_radius=0, fg_color="#0c0c0c")
        self.status_bar.grid(row=2, column=0, sticky="ew")
        
        self.status_icon = ctk.CTkLabel(
            self.status_bar,
            text="✓",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#10b981"
        )
        self.status_icon.pack(side="left", padx=(20, 5), pady=5)
        
        self.status_label = ctk.CTkLabel(
            self.status_bar,
            text="Initializing...",
            font=ctk.CTkFont(family="Inter", size=12),
            text_color="#aaa"
        )
        self.status_label.pack(side="left", padx=0, pady=5)
        
        # Initialize display
        self.update_image_display()
        
        if self.image:
            threading.Thread(target=self.run_ocr_background, daemon=True).start()
        else:
            self.set_status("Ready")
            
    def update_image_display(self):
        # Clear existing preview widgets
        for widget in self.preview_container.winfo_children():
            widget.destroy()
            
        if self.image:
            self.preview_label = ctk.CTkLabel(self.preview_container, text="")
            self.preview_label.pack(fill="both", expand=True, padx=10, pady=10)
            self.setup_image_preview()
            
            # Allow click-to-browse even when image is loaded
            self.preview_label.bind("<Button-1>", lambda e: self.browse_image())
            self.preview_label.configure(cursor="hand2")
        else:
            # Placeholder layouts
            self.preview_container.rowconfigure((0, 1, 2, 3), weight=1)
            self.preview_container.columnconfigure(0, weight=1)
            
            self.placeholder_icon = ctk.CTkLabel(
                self.preview_container,
                text="🖼",
                font=ctk.CTkFont(size=48),
                text_color="#666"
            )
            self.placeholder_icon.grid(row=0, column=0, pady=(25, 2))
            
            self.placeholder_text = ctk.CTkLabel(
                self.preview_container,
                text="Drag & drop an image here",
                font=ctk.CTkFont(family="Inter", size=14),
                text_color="#888"
            )
            self.placeholder_text.grid(row=1, column=0, pady=2)
            
            self.browse_link = ctk.CTkLabel(
                self.preview_container,
                text="or click to browse",
                font=ctk.CTkFont(family="Inter", size=14, underline=True),
                text_color="#3b82f6",
                cursor="hand2"
            )
            self.browse_link.grid(row=2, column=0, pady=2)
            self.browse_link.bind("<Button-1>", lambda e: self.browse_image())
            self.browse_link.bind("<Enter>", lambda e: self.browse_link.configure(text_color="#60a5fa"))
            self.browse_link.bind("<Leave>", lambda e: self.browse_link.configure(text_color="#3b82f6"))
            
            self.placeholder_supports = ctk.CTkLabel(
                self.preview_container,
                text="Supports: JPG, PNG, WEBP",
                font=ctk.CTkFont(family="Inter", size=11),
                text_color="#555"
            )
            self.placeholder_supports.grid(row=3, column=0, pady=(2, 25))
            
            # Make children clickable to browse
            for widget in (self.placeholder_icon, self.placeholder_text, self.placeholder_supports):
                widget.bind("<Button-1>", lambda e: self.browse_image())
                widget.configure(cursor="hand2")
                
    def browse_image(self):
        file_types = [("Image files", "*.png *.jpg *.jpeg *.webp"), ("All files", "*.*")]
        filename = filedialog.askopenfilename(
            parent=self.root,
            title="Select Image to OCR",
            filetypes=file_types
        )
        if filename:
            try:
                self.image = Image.open(filename).convert("RGBA")
                self.update_image_display()
                threading.Thread(target=self.run_ocr_background, daemon=True).start()
            except Exception as e:
                self.set_status(f"Error loading image: {str(e)}")
                
    def setup_image_preview(self):
        if not self.image:
            return
            
        max_w, max_h = 320, 260
        w, h = self.image.size
        
        factor = min(max_w / w, max_h / h)
        new_w = int(w * factor)
        new_h = int(h * factor)
        
        resized_img = self.image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        self.photo = ctk.CTkImage(light_image=resized_img, dark_image=resized_img, size=(new_w, new_h))
        self.preview_label.configure(image=self.photo, text="")
        
    def set_status(self, text):
        def update_ui():
            self.status_label.configure(text=text)
            low_text = text.lower()
            if "running" in low_text or "translating" in low_text or "uploading" in low_text or "initializing" in low_text:
                self.status_icon.configure(text="●", text_color="#fbbf24") # Yellow / Busy
            elif "error" in low_text or "failed" in low_text or "no internet" in low_text:
                self.status_icon.configure(text="⚠", text_color="#ef4444") # Red / Warning
            else:
                self.status_icon.configure(text="✓", text_color="#10b981") # Green / Success
        self.root.after(0, update_ui)
        
    def reset_placeholders(self):
        self.ocr_textbox.configure(state="normal", text_color="#666")
        self.ocr_textbox.delete("1.0", ctk.END)
        self.ocr_textbox.insert("1.0", "Extracted text will appear here...")
        self.ocr_textbox.configure(state="disabled")
        
        self.trans_textbox.configure(state="normal", text_color="#666")
        self.trans_textbox.delete("1.0", ctk.END)
        self.trans_textbox.insert("1.0", "Translated text will appear here...")
        self.trans_textbox.configure(state="disabled")
        
    def run_ocr_background(self):
        self.root.after(0, self.reset_placeholders)
        self.set_status("Running OCR...")
        self.ocr_text = ocr_engine.extract_text(self.image)
        
        if not self.ocr_text or not self.ocr_text.strip():
            self.ocr_text = "(No text detected)"
            self.set_status("OCR complete. No text found.")
        else:
            word_count = len(self.ocr_text.split())
            self.set_status(f"OCR complete. Found {word_count} words.")
            
        def update_textbox():
            self.ocr_textbox.configure(state="normal", text_color="white")
            self.ocr_textbox.delete("1.0", ctk.END)
            self.ocr_textbox.insert("1.0", self.ocr_text)
            self.ocr_textbox.configure(state="disabled")
            self.trigger_translation()
            
        self.root.after(0, update_textbox)
        
    def trigger_translation(self):
        text_to_translate = self.ocr_textbox.get("1.0", ctk.END).strip()
        if not text_to_translate or text_to_translate == "(No text detected)" or text_to_translate == "Extracted text will appear here...":
            return
            
        dropdown_text = self.lang_dropdown.cget("text")
        selected_lang_name = dropdown_text.replace("  ▼", "").strip().lower()
        target_code = self.languages.get(selected_lang_name, 'en')
        
        self.set_status(f"Translating to {selected_lang_name.capitalize()}...")
        
        def run_translation():
            translated_text = translator.translate(text_to_translate, target_code)
            
            def update_trans_ui():
                self.trans_textbox.configure(state="normal", text_color="white")
                self.trans_textbox.delete("1.0", ctk.END)
                self.trans_textbox.insert("1.0", translated_text)
                self.trans_textbox.configure(state="disabled")
                self.set_status("Translation complete.")
                
            self.root.after(0, update_trans_ui)
            
        threading.Thread(target=run_translation, daemon=True).start()
        
    def show_language_dropdown(self):
        values = [name.capitalize() for name in self.lang_names]
        ScrollableDropdown(
            attach_widget=self.lang_dropdown,
            values=values,
            command=self.on_language_select
        )
        
    def on_language_select(self, val):
        self.lang_dropdown.configure(text=f"{val}  ▼")
        self.trigger_translation()
        
    def retry_ocr(self):
        if not self.image:
            return
        self.config = config_manager.load_config()
        threading.Thread(target=self.run_ocr_background, daemon=True).start()
        
    def copy_ocr_to_clipboard(self):
        text = self.ocr_textbox.get("1.0", ctk.END).strip()
        if text and text != "Extracted text will appear here...":
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.set_status("OCR text copied to clipboard!")
        
    def copy_trans_to_clipboard(self):
        text = self.trans_textbox.get("1.0", ctk.END).strip()
        if text and text != "Translated text will appear here...":
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.set_status("Translation copied to clipboard!")
        
    def speak_text(self):
        if hasattr(self, 'is_speaking') and self.is_speaking:
            if hasattr(self, 'speaker') and self.speaker:
                try:
                    self.speaker.Speak("", 2) # Purge
                except Exception as e:
                    print("Error stopping speech:", e)
            self.is_speaking = False
            self.tts_btn.configure(text="Read Extracted Text", fg_color="#24242b", hover_color="#2f2f3a")
            self.set_status("Speech stopped.")
            return

        text = self.ocr_textbox.get("1.0", ctk.END).strip()
        if not text or text == "(No text detected)" or text == "Extracted text will appear here...":
            return
            
        self.set_status("Speaking text...")
        self.is_speaking = True
        self.tts_btn.configure(text="Stop Reading", fg_color="#ef4444", hover_color="#dc2626")
        
        if not self.speaker:
            try:
                import pythoncom
                pythoncom.CoInitialize()
                self.speaker = win32com.client.Dispatch("SAPI.SpVoice")
            except Exception as e:
                print("Failed to initialize TTS speaker:", e)
                self.set_status("Failed to initialize TTS.")
                self.is_speaking = False
                self.tts_btn.configure(text="Read Extracted Text", fg_color="#24242b", hover_color="#2f2f3a")
                return

        try:
            self.speaker.Speak(text, 1) # Async
            
            def check_speech_status():
                if not self.is_speaking:
                    return
                try:
                    is_done = self.speaker.WaitUntilDone(0)
                    if not is_done:
                        self.root.after(200, check_speech_status)
                    else:
                        self.is_speaking = False
                        self.tts_btn.configure(text="Read Extracted Text", fg_color="#24242b", hover_color="#2f2f3a")
                        self.set_status("Ready")
                except Exception:
                    self.is_speaking = False
                    self.tts_btn.configure(text="Read Extracted Text", fg_color="#24242b", hover_color="#2f2f3a")
                    self.set_status("Ready")
                    
            self.root.after(200, check_speech_status)
        except Exception as e:
            print("TTS Error:", e)
            self.is_speaking = False
            self.tts_btn.configure(text="Read Extracted Text", fg_color="#24242b", hover_color="#2f2f3a")
            self.set_status("TTS Error.")
        
    def save_image(self):
        if not self.image:
            return
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        initial_name = f"box_search_crop_{timestamp}.png"
        file_types = [("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*")]
        filename = filedialog.asksaveasfilename(
            parent=self.root,
            title="Save Cropped Image",
            initialfile=initial_name,
            defaultextension=".png",
            filetypes=file_types
        )
        if filename:
            try:
                self.image.save(filename)
                self.set_status(f"Image saved successfully to {os.path.basename(filename)}")
            except Exception as e:
                self.set_status(f"Error saving image: {str(e)}")
        
    def trigger_web_search(self):
        if not self.image:
            return
        self.web_search_btn.configure(state="disabled")
        self.set_status("Uploading image to tmpfiles.org for Google Lens search...")
        
        def run_search():
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, "lens_search_crop.png")
            self.image.save(temp_path)
            
            url = "https://tmpfiles.org/api/v1/upload"
            try:
                with open(temp_path, "rb") as f:
                    files = {"file": f}
                    response = requests.post(url, files=files)
                
                if response.status_code == 200:
                     result = response.json()
                     raw_url = result["data"]["url"]
                     direct_url = raw_url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
                     lens_url = f"https://lens.google.com/uploadbyurl?url={direct_url}"
                     webbrowser.open(lens_url)
                     self.set_status("Google Lens search opened in default browser!")
                else:
                     self.set_status(f"Upload failed: HTTP {response.status_code}")
            except Exception as e:
                 err_msg = str(e)
                 if "Failed to resolve" in err_msg or "Max retries exceeded" in err_msg or "Connection" in err_msg:
                     self.set_status("No internet connection. Connect to the internet or change OCR Mode to Offline.")
                 else:
                     self.set_status(f"Search error: {err_msg}")
            finally:
                 if os.path.exists(temp_path):
                     try:
                         os.remove(temp_path)
                     except Exception:
                         pass
                 self.root.after(0, lambda: self.web_search_btn.configure(state="normal"))
                
        threading.Thread(target=run_search, daemon=True).start()

    def show_burger_menu(self):
        self.burger_btn.update_idletasks()
        x = self.burger_btn.winfo_rootx()
        y = self.burger_btn.winfo_rooty() + self.burger_btn.winfo_height()
        self.burger_menu.post(x, y)

            
    def open_settings(self):
        from settings_gui import SettingsWindow
        SettingsWindow(self.root, on_save_callback=self.on_settings_saved)
        
    def on_settings_saved(self):
        self.config = config_manager.load_config()
        self.set_status("Settings updated!")
        if hasattr(self.parent, "app") and self.parent.app:
            self.parent.app.reload_settings()

if __name__ == "__main__":
    print("Launching Results GUI test window...")
    root = ctk.CTk()
    # We pass None to test the browse placeholder layout
    ResultsWindow(root, None)
    root.mainloop()
