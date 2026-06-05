import tkinter as tk
import random
import math
import numpy as np
from mod_api import BaseMod

# Required manifest dictionary export for ChaoHub ModLoader
CHAO_MOD_MANIFEST = {
    "name": "GREEN MATRIX",
    "author": "Systems Architect",
    "version": "1.0.0",
    "type": "NEW_MODULE",
    "entry_point": "GreenMatrixMod"
}

class GreenMatrixMod(tk.Frame, BaseMod):
    """
    A runtime dynamic ChaoHub plugin.
    - Implements Vector A: Instantiates a custom neon digital rain tab frame.
    - Implements Vector B: Injects render-pipe color/static modifiers to GlitchManager.
    """
    def __init__(self, parent=None, app_instance=None):
        self.app_instance = app_instance
        self.running = True
        self.color_mode = "GREEN"
        self.global_projection = True
        
        self.columns = []
        self.font_size = 14
        self.drawn_chars = {}
        self.animation_job = None

        if parent is not None:
            super().__init__(parent, bg="#000000")
            # Build and style layout components (Vector A)
            self.setup_ui()
        else:
            # Standalone/load-time instance
            pass

    def initialize(self, app_instance):
        """
        Invoked automatically at application startup.
        Saves proxy instance reference and hooks into the visual engine.
        """
        self.app_instance = app_instance
        if hasattr(app_instance, "glitch_manager") and app_instance.glitch_manager:
            app_instance.glitch_manager.register_visual_modifier(self.visual_glitch_callback)

    def teardown(self):
        """
        Safely unsubscribes callbacks and cancels pending animation threads.
        """
        self.running = False
        self.stop_matrix()
        if self.app_instance and hasattr(self.app_instance, "glitch_manager") and self.app_instance.glitch_manager:
            self.app_instance.glitch_manager.unregister_visual_modifier(self.visual_glitch_callback)

    def setup_ui(self):
        """Builds control selectors and digital rain viewport canvas."""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0) # Controls
        self.rowconfigure(1, weight=1) # Viewport

        # Neon controls panel
        self.controls_frame = tk.Frame(self, bg="#0b0b0b", highlightthickness=1, highlightbackground="#00ff00")
        self.controls_frame.grid(row=0, column=0, fill="x", padx=10, pady=5)

        tk.Label(
            self.controls_frame, 
            text="MATRIX MATRIX CONTROLLER v1.0", 
            fg="#00ff00", 
            bg="#0b0b0b", 
            font=("Courier", 11, "bold")
        ).pack(side="left", padx=10, pady=5)

        # Toggle Button
        self.toggle_btn = tk.Button(
            self.controls_frame, 
            text="[ HALT STREAM ]", 
            command=self.toggle_stream,
            bg="#000000", 
            fg="#00ff00", 
            activebackground="#00ff00", 
            activeforeground="#000000",
            font=("Courier", 9, "bold"), 
            bd=1
        ).pack(side="left", padx=5)

        # Color Selector Menu
        tk.Label(
            self.controls_frame, 
            text="COLOR:", 
            fg="#00ffff", 
            bg="#0b0b0b", 
            font=("Courier", 9, "bold")
        ).pack(side="left", padx=(10, 2))

        self.color_var = tk.StringVar(value="GREEN")
        self.color_menu = tk.OptionMenu(
            self.controls_frame, 
            self.color_var, 
            "GREEN", "MAGENTA", "CYAN", "RAINBOW", 
            command=self.change_color_mode
        )
        self.color_menu.config(
            bg="#000000", 
            fg="#00ff00", 
            activebackground="#00ff00", 
            activeforeground="#000000", 
            font=("Courier", 9, "bold"), 
            bd=1
        )
        self.color_menu["menu"].config(
            bg="#000000", 
            fg="#00ff00", 
            activebackground="#00ff00", 
            activeforeground="#000000", 
            font=("Courier", 9, "bold")
        )
        self.color_menu.pack(side="left", padx=5)

        # Speed scale
        tk.Label(
            self.controls_frame, 
            text="CASCADE DELAY:", 
            fg="#ffff00", 
            bg="#0b0b0b", 
            font=("Courier", 9, "bold")
        ).pack(side="left", padx=(10, 2))

        self.speed_scale = tk.Scale(
            self.controls_frame, 
            from_=15, 
            to=120, 
            orient="horizontal", 
            bg="#0b0b0b", 
            fg="#00ff00",
            troughcolor="#222222", 
            highlightthickness=0, 
            showvalue=False, 
            length=100
        )
        self.speed_scale.set(35)
        self.speed_scale.pack(side="left", padx=5)

        # Global Theme Projection Checkbutton
        self.proj_var = tk.BooleanVar(value=True)
        self.proj_check = tk.Checkbutton(
            self.controls_frame, 
            text="PROMPT GLOBAL THEME", 
            variable=self.proj_var,
            command=self.toggle_projection,
            bg="#0b0b0b", 
            fg="#00ffff", 
            activebackground="#0b0b0b", 
            activeforeground="#00ffff",
            selectcolor="#000000",
            font=("Courier", 9, "bold"), 
            bd=0, 
            highlightthickness=0
        )
        self.proj_check.pack(side="left", padx=15)

        # Dynamic Rain Viewport Canvas
        self.canvas = tk.Canvas(self, bg="#000000", highlightthickness=1, highlightbackground="#00ff00")
        self.canvas.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        # Alerts overlay text for Glitch Events
        self.alert_text_id = self.canvas.create_text(
            400, 30, 
            text="", 
            fill="#ff0000", 
            font=("Courier", 12, "bold"), 
            state="hidden"
        )

        self.canvas.bind("<Configure>", self.recalibrate_columns)
        self.recalibrate_columns()
        self.start_matrix()

    def toggle_stream(self):
        self.running = not self.running
        if self.running:
            self.start_matrix()
        else:
            self.stop_matrix()

    def change_color_mode(self, val):
        self.color_mode = val
        if val != "GREEN":
            try:
                if self.app_instance:
                    self.app_instance.achievement_manager.grant_achievement("matrix_welcome")
            except Exception as e:
                print(f"Error unlocking matrix_welcome: {e}")

    def toggle_projection(self):
        self.global_projection = self.proj_var.get()

    def recalibrate_columns(self, event=None):
        w = self.canvas.winfo_width()
        if w <= 1:
            w = 800
        num_cols = w // self.font_size
        
        if len(self.columns) != num_cols:
            self.columns = []
            for _ in range(num_cols):
                y_pos = random.randint(-40, 0)
                speed = random.randint(2, 6)
                self.columns.append({
                    "y": y_pos,
                    "speed": speed,
                    "last_row": -1
                })

    def start_matrix(self):
        self.stop_matrix()
        self.update_matrix()

    def stop_matrix(self):
        if self.animation_job:
            try:
                self.after_cancel(self.animation_job)
            except Exception:
                pass
            self.animation_job = None

    def update_matrix(self):
        if not self.running:
            return
        
        try:
            width = self.canvas.winfo_width()
            height = self.canvas.winfo_height()
            if width <= 1: width = 800
            if height <= 1: height = 400
            
            rows = height // self.font_size
            
            # Detect Core System Glitch Activity (Matrix Lore Multiplier)
            glitch_manager = getattr(self.app_instance, "glitch_manager", None)
            glitch_active = getattr(glitch_manager, "global_glitch_active", False) if glitch_manager else False

            # Age and fade old characters
            to_delete = []
            for char_id, info in list(self.drawn_chars.items()):
                info["age"] += 1
                age = info["age"]
                
                if age > 14:
                    to_delete.append(char_id)
                else:
                    # Strobe and shift color values
                    if glitch_active:
                        # Lore Multiplier: flashing alert red static during global exploits
                        color = "#ff0000" if age % 2 == 0 else "#880000"
                    else:
                        if self.color_mode == "GREEN":
                            color = f"#{0:02x}{max(0, 255 - age * 18):02x}{0:02x}"
                        elif self.color_mode == "MAGENTA":
                            color = f"#{max(0, 255 - age * 18):02x}{0:02x}{max(0, 255 - age * 18):02x}"
                        elif self.color_mode == "CYAN":
                            color = f"#{0:02x}{max(0, 255 - age * 18):02x}{max(0, 255 - age * 18):02x}"
                        else: # Rainbow
                            r = int(127 + 127 * math.sin(age * 0.4))
                            g = int(127 + 127 * math.sin(age * 0.4 + 2))
                            b = int(127 + 127 * math.sin(age * 0.4 + 4))
                            color = f"#{r:02x}{g:02x}{b:02x}"
                    self.canvas.itemconfig(char_id, fill=color)
            
            for char_id in to_delete:
                self.canvas.delete(char_id)
                self.drawn_chars.pop(char_id, None)

            # Define character pools
            # Standard katakana/ascii mix vs purely binary glitch streams
            if glitch_active:
                char_pool = "01"
            else:
                char_pool = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ" + "".join(chr(i) for i in range(0xFF66, 0xFF9F))

            # Position alert overlay
            if glitch_active:
                self.canvas.coords(self.alert_text_id, width // 2, 40)
                self.canvas.itemconfig(
                    self.alert_text_id, 
                    text="!!! SYSTEM OVERFLOW EXPLOIT DETECTED - MATRIX RE-ROUTING !!!", 
                    state="normal"
                )
            else:
                self.canvas.itemconfig(self.alert_text_id, state="hidden")

            # Draw cascading heads
            for col_idx, col in enumerate(self.columns):
                # Lore Multiplier: speed up cascading rain by 3x during system glitches
                step_scalar = 0.85 if glitch_active else 0.25
                col["y"] += col["speed"] * step_scalar
                current_row = int(col["y"])
                
                if current_row >= 0 and current_row < rows:
                    if col["last_row"] != current_row:
                        col["last_row"] = current_row
                        
                        char = random.choice(char_pool)
                        x = col_idx * self.font_size + self.font_size // 2
                        y = current_row * self.font_size + self.font_size // 2
                        
                        # Head highlight settings
                        if glitch_active:
                            head_color = "#ffffff" if random.random() < 0.4 else "#ff0000"
                        else:
                            head_color = "#ffffff" if random.random() < 0.2 else "#00ff00"
                            
                        char_id = self.canvas.create_text(
                            x, y, 
                            text=char, 
                            fill=head_color, 
                            font=("Courier", self.font_size, "bold")
                        )
                        self.drawn_chars[char_id] = {"age": 0}
                        
                if current_row >= rows + 6:
                    col["y"] = random.randint(-15, 0)
                    col["last_row"] = -1
            
            # Lore Multiplier: override delay to 10ms (maximum processing rate) during glitch event
            delay = 10 if glitch_active else self.speed_scale.get()
            self.animation_job = self.after(delay, self.update_matrix)
        except Exception:
            pass

    def visual_glitch_callback(self, arr):
        """
        Vector B callback injected directly into GlitchManager's render path.
        Distorts display pixel buffers toward green matrix aesthetics.
        """
        if not self.global_projection:
            return arr

        if arr is not None and len(arr.shape) == 3:
            h, w, c = arr.shape
            
            # Color grade snapshot: suppress red and blue, boost green
            arr[:, :, 0] = (arr[:, :, 0] * 0.15).astype(np.uint8) # Dim Red channel
            arr[:, :, 2] = (arr[:, :, 2] * 0.25).astype(np.uint8) # Dim Blue channel
            arr[:, :, 1] = np.clip(arr[:, :, 1] * 1.3, 0, 255).astype(np.uint8) # Amplify Green
            
            # Check if global exploit flash is active
            glitch_manager = getattr(self.app_instance, "glitch_manager", None)
            glitch_active = getattr(glitch_manager, "global_glitch_active", False) if glitch_manager else False

            if glitch_active:
                # Add horizontal green glitch blocks
                for _ in range(4):
                    slice_h = random.randint(5, 15)
                    slice_y = random.randint(0, max(1, h - slice_h))
                    slice_w = random.randint(100, min(300, w))
                    slice_x = random.randint(0, max(1, w - slice_w))
                    
                    # Fill with solid green static noise block
                    arr[slice_y:slice_y+slice_h, slice_x:slice_x+slice_w, 1] = np.random.randint(200, 256, (slice_h, slice_w), dtype=np.uint8)
                    arr[slice_y:slice_y+slice_h, slice_x:slice_x+slice_w, 0] = 0
                    arr[slice_y:slice_y+slice_h, slice_x:slice_x+slice_w, 2] = 0
            return arr
        return arr
