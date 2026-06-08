import tkinter as tk
from PIL import Image, ImageTk, ImageGrab, ImageEnhance
import win32api
import win32con
import config_manager

class ScreenOverlay:
    def __init__(self, parent, on_select_callback, on_close_callback):
        self.on_select_callback = on_select_callback
        self.on_close_callback = on_close_callback
        
        # 1. Get virtual screen coordinates (supports multi-monitor)
        try:
            self.left = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
            self.top = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)
            self.width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
            self.height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
        except Exception:
            # Fallback to primary monitor
            self.left = 0
            self.top = 0
            self.width = ImageGrab.grab().width
            self.height = ImageGrab.grab().height
            
        # 2. Grab the screenshot of all screens
        # We grab slightly before showing the window so we don't capture our own window
        self.original_image = ImageGrab.grab(
            bbox=(self.left, self.top, self.left + self.width, self.top + self.height),
            all_screens=True
        )
        
        # Create a darkened version of the screenshot
        enhancer = ImageEnhance.Brightness(self.original_image)
        self.darkened_image = enhancer.enhance(0.40)  # Dim the screen to 40% brightness
        
        # 3. Initialize the Toplevel window
        self.root = tk.Toplevel(parent)
        self.root.title("Box to Search Overlay")
        self.root.overrideredirect(True)  # Frameless window
        
        # Position window to cover the entire virtual screen
        self.root.geometry(f"{self.width}x{self.height}+{self.left}+{self.top}")
        self.root.attributes("-topmost", True)
        
        # Set cursor to crosshair
        self.root.config(cursor="cross")
        
        # 4. Create Canvas
        self.canvas = tk.Canvas(
            self.root, 
            width=self.width, 
            height=self.height, 
            bd=0, 
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)
        
        # Initialize background image
        self.bg_photo = ImageTk.PhotoImage(self.darkened_image)
        self.bg_id = self.canvas.create_image(0, 0, image=self.bg_photo, anchor="nw")
        
        # 5. Draw instructional banner at the top center of the screen
        center_x = self.width // 2
        banner_w = 480
        banner_h = 36
        self.canvas.create_rectangle(
            center_x - banner_w // 2, 20,
            center_x + banner_w // 2, 20 + banner_h,
            fill="#121212", outline="#004aad", width=1.5
        )
        self.canvas.create_text(
            center_x, 20 + banner_h // 2,
            text="Box to Search: Drag to select. Right-Click to Exit.",
            fill="white",
            font=("Inter", 12, "bold")
        )
        
        # Selection state
        self.start_x = None
        self.start_y = None
        self.rect_id = None
        self.border_id = None
        
        # Bind events
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)
        
        # Bind Right-Click to both root and canvas to guarantee cancellation
        self.root.bind("<Button-3>", lambda e: self.close())
        self.canvas.bind("<Button-3>", lambda e: self.close())
        
        # Force focus on window and canvas
        self.root.focus_force()
        self.canvas.focus_set()

    def on_button_press(self, event):
        # Save start coordinates
        self.start_x = event.x
        self.start_y = event.y
        
        # Create a neon borders on canvas
        # Google's theme has a beautiful neon cyan/blue/magenta glow.
        # We will draw a stylish selection border.
        self.border_id = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline="#004aad", width=2, dash=(4, 4)
        )

    def on_move_press(self, event):
        cur_x, cur_y = event.x, event.y
        
        # Bound coordinates within screen limits
        cur_x = max(0, min(self.width, cur_x))
        cur_y = max(0, min(self.height, cur_y))
        
        x1, y1 = self.start_x, self.start_y
        x2, y2 = cur_x, cur_y
        
        # Normalize bounds
        min_x, max_x = min(x1, x2), max(x1, x2)
        min_y, max_y = min(y1, y2), max(y1, y2)
        
        # Avoid zero width/height
        if max_x - min_x < 2 or max_y - min_y < 2:
            return
            
        # Update canvas selection border outline
        self.canvas.coords(self.border_id, min_x, min_y, max_x, max_y)
        
        # SPOTLIGHT EFFECT:
        # 1. Take a copy of the darkened image
        temp_img = self.darkened_image.copy()
        
        # 2. Crop the bright area from original_image
        crop_box = (min_x, min_y, max_x, max_y)
        bright_crop = self.original_image.crop(crop_box)
        
        # 3. Paste the bright crop onto the darkened copy
        temp_img.paste(bright_crop, (min_x, min_y))
        
        # 4. Update the background PhotoImage in place
        self.bg_photo = ImageTk.PhotoImage(temp_img)
        self.canvas.itemconfig(self.bg_id, image=self.bg_photo)

    def on_button_release(self, event):
        if self.start_x is None or self.start_y is None:
            return
        x1, y1 = self.start_x, self.start_y
        x2, y2 = event.x, event.y
        
        # Bound coordinates within screen limits
        x2 = max(0, min(self.width, x2))
        y2 = max(0, min(self.height, y2))
        
        min_x, max_x = min(x1, x2), max(x1, x2)
        min_y, max_y = min(y1, y2), max(y1, y2)
        
        # Calculate size
        w = max_x - min_x
        h = max_y - min_y
        
        # Destroy window immediately to restore desktop view
        self.root.destroy()
        
        # If selection is large enough, trigger callback
        if w > 5 and h > 5:
            cropped_image = self.original_image.crop((min_x, min_y, max_x, max_y))
            self.on_select_callback(cropped_image)
        else:
            self.on_close_callback()
            
    def close(self):
        self.root.destroy()
        self.on_close_callback()

if __name__ == "__main__":
    # Test running overlay and saving selected crop
    print("Testing Overlay... Drag to select. Right click to cancel.")
    def handle_crop(img):
        img.save("test_crop.png")
        print("Selection saved as test_crop.png")
        
    root = tk.Tk()
    ScreenOverlay(root, handle_crop, lambda: print("Overlay closed"))
    root.mainloop()
