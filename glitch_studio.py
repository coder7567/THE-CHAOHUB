import os
import datetime
import random
import time
import math
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk, ImageDraw
import numpy as np

# Styled retro audio click / beep fallback hooks
def play_ui_sound(name):
    try:
        from creative_suite import play_sound_effect
        play_sound_effect(name)
    except Exception:
        pass

def generate_procedural_test_card(width=400, height=400):
    """
    Generates a premium retro-futurist cyber TV calibration grid screen using PIL canvas drawing.
    Serves as the high-fidelity aesthetic fallback if no user image is loaded on startup.
    """
    img = Image.new("RGB", (width, height), "#000000")
    draw = ImageDraw.Draw(img)
    
    # 1. Background grid overlay
    grid_size = 20
    for x in range(0, width, grid_size):
        draw.line([x, 0, x, height], fill="#111111", width=1)
    for y in range(0, height, grid_size):
        draw.line([0, y, width, y], fill="#111111", width=1)
        
    # 2. Render vertical neon calibration color bars
    colors = ["#ffff00", "#00ffff", "#00ff00", "#ff00ff", "#ff0000", "#0000ff"]
    bar_w = width // len(colors)
    for i, color in enumerate(colors):
        draw.rectangle([i * bar_w, 20, (i + 1) * bar_w, int(height * 0.65)], fill=color)
        
    # 3. Horizontal grayscale calibration scale
    grad_y = int(height * 0.65)
    grad_h = 30
    grad_colors = ["#111111", "#333333", "#555555", "#777777", "#999999", "#bbbbbb", "#dddddd", "#ffffff"]
    g_bar_w = width // len(grad_colors)
    for i, color in enumerate(grad_colors):
        draw.rectangle([i * g_bar_w, grad_y, (i + 1) * g_bar_w, grad_y + grad_h], fill=color)
        
    # 4. Diagonal safety warning stripes at the bottom
    stripe_y = grad_y + grad_h + 10
    stripe_w = 15
    for x in range(-stripe_w, width + stripe_w, stripe_w * 2):
        draw.polygon([
            (x, height),
            (x + stripe_w, height),
            (x + stripe_w + 15, stripe_y),
            (x + 15, stripe_y)
        ], fill="#ffff00")
        
    # 5. Calibration crosshair and rings
    cx, cy = width // 2, height // 2
    r1 = min(width, height) // 4
    draw.ellipse([cx - r1, cy - r1, cx + r1, cy + r1], outline="#ffffff", width=2)
    draw.ellipse([cx - r1 - 10, cy - r1 - 10, cx + r1 + 10, cy + r1 + 10], outline="#00ffff", width=1)
    draw.line([cx - r1 - 20, cy, cx + r1 + 20, cy], fill="#ff00ff", width=1)
    draw.line([cx, cy - r1 - 20, cx, cy + r1 + 20], fill="#ff00ff", width=1)
    
    # 6. Center label container
    draw.rectangle([cx - 125, cy - 30, cx + 125, cy + 35], fill="#000000", outline="#00ff00", width=2)
    
    text_lines = [
        "CHAO_HUB GLITCH CORE",
        "STATUS: NO ARTIFACT",
        "AWAITING DATA STREAM"
    ]
    
    y_offset = cy - 22
    for line in text_lines:
        txt_w = len(line) * 6
        draw.text((cx - txt_w // 2, y_offset), line, fill="#00ff00")
        y_offset += 16
        
    return img

class GlitchArtStudioPanel(tk.Frame):
    """
    Module G Tab 3: Complete object-oriented Glitch Art Studio Panel.
    Enables low-level data corruption, real-time matrix manipulations,
    and lossless compiled png exporting.
    """
    def __init__(self, parent, glitch_manager=None):
        super().__init__(parent, bg="#000000")
        self.glitch_manager = glitch_manager
        
        # Cyberpunk terminal styling palettes
        self.BG_DARK = "#000000"
        self.BG_PANEL = "#0b0b0b"
        self.FG_GREEN = "#00ff00"
        self.FG_CYAN = "#00ffff"
        self.FG_MAGENTA = "#ff00ff"
        self.FG_YELLOW = "#ffff00"
        self.ALERT_RED = "#ff0000"
        
        # Image Cache Storage
        self.master_image = None          # Clean, untouched master PIL Image
        self.preview_master = None         # Centered, aspect-fit preview PIL Image
        self.preview_master_arr = None     # NumPy array of the preview master for fast calculations
        self.canvas_image_ref = None       # Tkinter photoimage anchor to protect from garbage collection
        
        # Real-time Slider Value Bindings
        self.tear_intensity_var = tk.DoubleVar(value=0.0)
        self.aberration_offset_var = tk.DoubleVar(value=0.0)
        self.sort_threshold_var = tk.DoubleVar(value=255.0)  # Default: 255 (disabled)
        
        self.build_ui()
        self.load_default_test_card()
        
        # Hook glitch manager support if running inside the ChaoHub framework
        if self.glitch_manager:
            self.glitch_manager.register_widget(self.canvas, magnitude=0.15)
            self.glitch_manager.register_widget(self.btn_ingest, magnitude=0.20)
            self.glitch_manager.register_widget(self.btn_export, magnitude=0.25)
            self.glitch_manager.register_widget(self.scale_tear, magnitude=0.15)
            self.glitch_manager.register_widget(self.scale_aberration, magnitude=0.15)
            self.glitch_manager.register_widget(self.scale_sort, magnitude=0.15)
            self.glitch_manager.register_widget(self.status_label, magnitude=0.15)

    def build_ui(self):
        # Frame Layout Splitting
        # Left Panel: Viewport Canvas and Action Buttons
        self.left_frame = tk.Frame(self, bg=self.BG_DARK)
        self.left_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        canvas_header = tk.Frame(self.left_frame, bg=self.BG_DARK)
        canvas_header.pack(fill="x", pady=(0, 5))
        tk.Label(canvas_header, text="GLITCH VIEWPORT // ARTIFACT PREVIEW", fg=self.FG_CYAN, bg=self.BG_DARK, font=("Courier", 11, "bold")).pack(side="left")
        
        # 400x400 Centered Canvas
        self.canvas = tk.Canvas(self.left_frame, width=400, height=400, bg=self.BG_DARK,
                                highlightthickness=1, highlightbackground=self.FG_MAGENTA)
        self.canvas.pack(anchor="center", pady=5)
        
        # Action Buttons frame
        self.buttons_frame = tk.Frame(self.left_frame, bg=self.BG_DARK)
        self.buttons_frame.pack(fill="x", pady=5)
        
        self.btn_ingest = tk.Button(self.buttons_frame, text="[ INGEST ARTIFACT ]", command=self.ingest_artifact,
                                    bg=self.BG_DARK, fg=self.FG_GREEN, activebackground=self.FG_GREEN, activeforeground=self.BG_DARK,
                                    font=("Courier", 10, "bold"), bd=1, relief="flat", highlightbackground=self.FG_GREEN)
        self.btn_ingest.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.btn_export = tk.Button(self.buttons_frame, text="[ EXPORT CORRUPTED DATA ]", command=self.export_glitch,
                                    bg=self.BG_DARK, fg=self.FG_MAGENTA, activebackground=self.FG_MAGENTA, activeforeground=self.BG_DARK,
                                    font=("Courier", 10, "bold"), bd=1, relief="flat", highlightbackground=self.FG_MAGENTA)
        self.btn_export.pack(side="right", fill="x", expand=True, padx=(5, 0))
        
        # Right Panel: Sliders & Diagnostics Monitor Logger
        self.control_rack = tk.Frame(self, bg=self.BG_PANEL, highlightthickness=1, highlightbackground="#222222", width=340)
        self.control_rack.pack(side="right", fill="both", expand=False, padx=10, pady=10)
        self.control_rack.pack_propagate(False)
        
        title_lbl = tk.Label(self.control_rack, text="GLITCH MATRIX CORE", fg=self.FG_MAGENTA, bg=self.BG_PANEL, font=("Courier", 12, "bold"))
        title_lbl.pack(pady=15, padx=10)
        
        # 1. Slider Parameters Section
        sliders_title = tk.Label(self.control_rack, text="HARDWARE PARAMETERS:", fg=self.FG_YELLOW, bg=self.BG_PANEL, font=("Courier", 10, "bold"))
        sliders_title.pack(anchor="w", padx=15, pady=(5, 5))
        
        self.scale_tear = tk.Scale(self.control_rack, from_=0, to=100, orient="horizontal",
                                   variable=self.tear_intensity_var, command=self.on_parameter_change,
                                   label="TEAR INTENSITY", bg=self.BG_PANEL, fg=self.FG_GREEN,
                                   troughcolor=self.BG_DARK, highlightthickness=0, font=("Courier", 8, "bold"),
                                   activebackground=self.FG_GREEN, resolution=1)
        self.scale_tear.pack(fill="x", padx=15, pady=4)
        
        self.scale_aberration = tk.Scale(self.control_rack, from_=0, to=30, orient="horizontal",
                                         variable=self.aberration_offset_var, command=self.on_parameter_change,
                                         label="ABERRATION OFFSET", bg=self.BG_PANEL, fg=self.FG_CYAN,
                                         troughcolor=self.BG_DARK, highlightthickness=0, font=("Courier", 8, "bold"),
                                         activebackground=self.FG_CYAN, resolution=1)
        self.scale_aberration.pack(fill="x", padx=15, pady=4)
        
        self.scale_sort = tk.Scale(self.control_rack, from_=0, to=255, orient="horizontal",
                                   variable=self.sort_threshold_var, command=self.on_parameter_change,
                                   label="SORT THRESHOLD", bg=self.BG_PANEL, fg=self.FG_YELLOW,
                                   troughcolor=self.BG_DARK, highlightthickness=0, font=("Courier", 8, "bold"),
                                   activebackground=self.FG_YELLOW, resolution=1)
        self.scale_sort.pack(fill="x", padx=15, pady=4)
        
        # 2. Terminal Logger Diagnostic Output
        logger_title = tk.Label(self.control_rack, text="LOG SYSTEM MONITOR:", fg=self.FG_YELLOW, bg=self.BG_PANEL, font=("Courier", 10, "bold"))
        logger_title.pack(anchor="w", padx=15, pady=(12, 4))
        
        self.log_terminal = tk.Text(self.control_rack, height=7, bg="#000000", fg=self.FG_GREEN,
                                    font=("Courier", 8), bd=1, relief="solid", highlightthickness=1, highlightbackground="#333333",
                                    state="disabled")
        self.log_terminal.pack(fill="x", padx=15, pady=2)
        
        # Bottom status display line
        self.status_label = tk.Label(self.control_rack, text="[ STATUS: CORE ACTIVE // STANDBY ]", fg=self.FG_GREEN, bg=self.BG_PANEL, font=("Courier", 9, "bold"))
        self.status_label.pack(side="bottom", fill="x", pady=15)

    # -------------------------------------------------------------
    # FILE INGESTION & DEFAULT STATE GENERATION
    # -------------------------------------------------------------
    def load_default_test_card(self):
        """Loads the procedural cyber grid to the active preview cache on launch."""
        test_card = generate_procedural_test_card(400, 400)
        self.preview_master = test_card
        self.preview_master_arr = np.array(test_card)
        self.log_message("SYSTEM INITIALIZED // RETRO CALIBRATION GRID ARTIFACT INGESTED")
        self.apply_glitch_effects()

    def ingest_artifact(self):
        """Launches native open file dialogue and loads raster images (.png, .jpg, .jpeg) safely."""
        play_ui_sound("click")
        filepath = filedialog.askopenfilename(
            parent=self.winfo_toplevel(),
            title="INGEST ARTIFACT STREAM",
            filetypes=[
                ("Raster Images", "*.png;*.jpg;*.jpeg"),
                ("PNG Image", "*.png"),
                ("JPEG Image", "*.jpg;*.jpeg"),
                ("All Files", "*.*")
            ]
        )
        
        if not filepath:
            self.log_message("INGESTION STREAM ABORTED BY OPERATOR", self.ALERT_RED)
            return
            
        try:
            filename = os.path.basename(filepath)
            self.log_message(f"INGESTING: {filename.upper()}...")
            self.update_idletasks()
            
            # Load full-resolution image
            loaded_img = Image.open(filepath)
            loaded_img.load()
            
            self.master_image = loaded_img
            
            # Scale dynamically to fit centered 400x400 viewport keeping aspect ratio
            max_w, max_h = 400, 400
            w, h = loaded_img.size
            ratio = min(max_w / w, max_h / h)
            new_w = int(w * ratio)
            new_h = int(h * ratio)
            
            self.preview_master = loaded_img.resize((new_w, new_h), Image.Resampling.LANCZOS).convert("RGB")
            self.preview_master_arr = np.array(self.preview_master)
            
            self.log_message(f"INGESTION SUCCESSFUL // SHAPE: {w}x{h} -> PREVIEW: {new_w}x{new_h}", self.FG_GREEN)
            
            # Reset sliders for fresh edits
            self.tear_intensity_var.set(0.0)
            self.aberration_offset_var.set(0.0)
            self.sort_threshold_var.set(255.0)
            
            # Apply base rendering
            self.apply_glitch_effects()
            play_ui_sound("beep")
            
        except Exception as e:
            self.log_message(f"CRITICAL ENGINE EXCEPTION DURING INGESTION: {str(e)[:35]}", self.ALERT_RED)

    # -------------------------------------------------------------
    # MATHEMATICALLY AUTHENTIC GLITCH ALGORITHMS (OPTIMIZED NUMPY)
    # -------------------------------------------------------------
    def apply_screen_tear(self, arr, intensity):
        """
        Effect 1: Screen Tear
        Slices the image horizontally and rolls pixels offset on the X-axis wrapping edges.
        """
        h, w, c = arr.shape
        num_tears = max(1, min(15, int(intensity * 0.15) + 1))
        max_shift = int(w * (intensity / 100.0) * 0.3)
        max_shift = max(1, max_shift)
        
        out = arr.copy()
        for _ in range(num_tears):
            slice_h = random.randint(5, max(10, int(h * 0.15)))
            slice_y = random.randint(0, max(1, h - slice_h))
            shift = random.randint(-max_shift, max_shift)
            if shift != 0:
                out[slice_y:slice_y+slice_h, :, :] = np.roll(
                    out[slice_y:slice_y+slice_h, :, :],
                    shift=shift,
                    axis=1
                )
        return out

    def apply_chromatic_aberration(self, arr, offset):
        """
        Effect 2: Chromatic Aberration
        Splits Red left/up, Blue right/down, keeping Green anchored.
        """
        h, w, c = arr.shape
        shift_x = int(offset)
        shift_y = int(offset // 2)
        
        # Split RGB channels cleanly
        r = arr[:, :, 0]
        g = arr[:, :, 1]
        b = arr[:, :, 2]
        
        # Translate Red left/up and Blue right/down
        r_shifted = np.roll(r, shift=(-shift_y, -shift_x), axis=(0, 1))
        b_shifted = np.roll(b, shift=(shift_y, shift_x), axis=(0, 1))
        
        return np.stack([r_shifted, g, b_shifted], axis=2)

    def apply_pixel_sort(self, arr, threshold_val):
        """
        Effect 3: Pixel Sorting
        Finds row sequences above a luminance threshold and sorts their pixel data.
        """
        if threshold_val >= 254:
            return arr
            
        h, w, c = arr.shape
        out = arr.copy()
        
        # Calculate NTSC standard luminance values: L = 0.299R + 0.587G + 0.114B
        r = out[:, :, 0].astype(np.float32)
        g = out[:, :, 1].astype(np.float32)
        b = out[:, :, 2].astype(np.float32)
        lum = 0.299 * r + 0.587 * g + 0.114 * b
        
        # Horizontal row pixel sorting
        for y in range(h):
            row_lum = lum[y]
            # Identify where luminance exceeds the sorted threshold
            mask = row_lum > threshold_val
            
            if not np.any(mask):
                continue
                
            # Locate contiguous segments
            padded = np.concatenate([[False], mask, [False]])
            diff = np.diff(padded.astype(int))
            starts = np.where(diff == 1)[0]
            ends = np.where(diff == -1)[0]
            
            # Sort each contiguous block
            for start, end in zip(starts, ends):
                if end - start > 1:
                    segment = out[y, start:end]
                    seg_lum = row_lum[start:end]
                    sort_order = np.argsort(seg_lum)
                    out[y, start:end] = segment[sort_order]
                    
        return out

    # -------------------------------------------------------------
    # FEEDBACK VIEWPORT UPDATE HOOKS
    # -------------------------------------------------------------
    def on_parameter_change(self, *args):
        """Interactive feedback slider recalculation thread loop."""
        self.apply_glitch_effects()

    def apply_glitch_effects(self):
        """Applies active parameters to the preview master array and updates canvas."""
        if self.preview_master_arr is None:
            return
            
        tear_intensity = self.tear_intensity_var.get()
        aberration_offset = self.aberration_offset_var.get()
        sort_threshold = self.sort_threshold_var.get()
        
        # Copy preview master to apply operations
        arr = self.preview_master_arr.copy()
        
        # 1. Screen Tear
        if tear_intensity > 0:
            arr = self.apply_screen_tear(arr, tear_intensity)
            
        # 2. Chromatic Aberration
        if aberration_offset > 0:
            arr = self.apply_chromatic_aberration(arr, aberration_offset)
            
        # 3. Pixel Sort
        if sort_threshold < 255:
            arr = self.apply_pixel_sort(arr, sort_threshold)
            
        # Display rendering result
        glitched_img = Image.fromarray(arr)
        self.display_image(glitched_img)

    def display_image(self, img):
        """Draws the PIL image centered on the viewport canvas."""
        self.canvas.delete("all")
        self.canvas_image_ref = ImageTk.PhotoImage(img)
        
        cx = 400 // 2
        cy = 400 // 2
        self.canvas.create_image(cx, cy, image=self.canvas_image_ref, anchor="center")

    # -------------------------------------------------------------
    # EXPORT ENGINE & FILE CLOAKING
    # -------------------------------------------------------------
    def export_glitch(self):
        """Losslessly compiles the active parameters to full original resolution and saves png."""
        play_ui_sound("click")
        
        # Setup output directories
        glitch_dir = os.path.join(os.path.expanduser("~"), "ChaoHub_Data", "glitch")
        try:
            os.makedirs(glitch_dir, exist_ok=True)
        except Exception as e:
            self.log_message(f"ERROR: DIRECTORY COMPILER UNREACHABLE {glitch_dir}", self.ALERT_RED)
            return
            
        # Load lossless target frame (original high-res master or high-res test card)
        if self.master_image is None:
            # Procedural high-res calibration pattern (512x512)
            img_to_process = generate_procedural_test_card(512, 512)
            preview_w = 400
        else:
            img_to_process = self.master_image
            preview_w = self.preview_master.width
            
        self.log_message("COMPILING FULL LOSSLESS DATA MATRICES...", self.FG_YELLOW)
        self.update_idletasks()
        
        try:
            orig_w, orig_h = img_to_process.size
            orig_arr = np.array(img_to_process.convert("RGB"))
            
            tear_intensity = self.tear_intensity_var.get()
            aberration_offset = self.aberration_offset_var.get()
            sort_threshold = self.sort_threshold_var.get()
            
            # 1. Screen Tear (Scaled horizontally to original size)
            if tear_intensity > 0:
                num_tears = max(1, min(15, int(tear_intensity * 0.15) + 1))
                max_shift = int(orig_w * (tear_intensity / 100.0) * 0.3)
                max_shift = max(1, max_shift)
                
                orig_arr = orig_arr.copy()
                for _ in range(num_tears):
                    slice_h = random.randint(5, max(10, int(orig_h * 0.15)))
                    slice_y = random.randint(0, max(1, orig_h - slice_h))
                    shift = random.randint(-max_shift, max_shift)
                    if shift != 0:
                        orig_arr[slice_y:slice_y+slice_h, :, :] = np.roll(
                            orig_arr[slice_y:slice_y+slice_h, :, :],
                            shift=shift,
                            axis=1
                        )
                        
            # 2. Chromatic Aberration (Scaled relative to original layout sizes)
            if aberration_offset > 0:
                scale = orig_w / preview_w
                full_offset = aberration_offset * scale
                shift_x = int(full_offset)
                shift_y = int(full_offset // 2)
                
                r = orig_arr[:, :, 0]
                g = orig_arr[:, :, 1]
                b = orig_arr[:, :, 2]
                
                r_shifted = np.roll(r, shift=(-shift_y, -shift_x), axis=(0, 1))
                b_shifted = np.roll(b, shift=(shift_y, shift_x), axis=(0, 1))
                orig_arr = np.stack([r_shifted, g, b_shifted], axis=2)
                
            # 3. Pixel Sorting (Direct Luminance Sorting)
            if sort_threshold < 255:
                orig_arr = self.apply_pixel_sort(orig_arr, sort_threshold)
                
            # Save compiled file losslessly
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"GLITCH_CH_{timestamp}.png"
            filepath = os.path.join(glitch_dir, filename)
            
            final_img = Image.fromarray(orig_arr)
            final_img.save(filepath, "PNG")
            
            self.log_message(f"DATA CLOAK COMPLETE // GLITCHED: {filename}", self.FG_GREEN)
            play_ui_sound("beep")
            
            self.flash_export_success_status()
            print(f"[GlitchArtStudioPanel] Corrupted file saved to: {filepath}")
            
        except Exception as err:
            self.log_message(f"CRITICAL COMPILATION FAILED: {str(err)[:30]}", self.ALERT_RED)

    # -------------------------------------------------------------
    # DIAGNOSTIC WRITER & NOTIFICATION FLASHER
    # -------------------------------------------------------------
    def log_message(self, text, color=None):
        """Appends interactive status notifications to the styled log terminal."""
        if not color:
            color = self.FG_GREEN
            
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        formatted = f"[ {timestamp} ] {text}\n"
        
        self.log_terminal.config(state="normal")
        self.log_terminal.insert("end", formatted)
        self.log_terminal.see("end")
        self.log_terminal.config(state="disabled")

    def flash_export_success_status(self):
        """Initiates terminal status bar blink."""
        self.flash_count = 6
        self._flash_tick()
        
    def _flash_tick(self):
        if self.flash_count <= 0:
            self.status_label.config(text="[ STATUS: GLITCH PATTERN EXPORTED // DATA BROADCAST SUCCESSFUL ]", fg=self.FG_GREEN)
            self.after(4000, lambda: self.status_label.config(text="[ STATUS: CORE ACTIVE // STANDBY ]", fg=self.FG_GREEN))
            return
            
        current_fg = self.status_label.cget("fg")
        next_fg = self.FG_MAGENTA if current_fg == self.FG_GREEN else self.FG_GREEN
        self.status_label.config(fg=next_fg)
        self.flash_count -= 1
        self.after(200, self._flash_tick)

    # -------------------------------------------------------------
    # MEMORY CLEANUP
    # -------------------------------------------------------------
    def destroy(self):
        """Explicitly garbage collects massive array caches and drops canvas references."""
        try:
            if self.glitch_manager:
                self.glitch_manager.unregister_widget(self.canvas)
                self.glitch_manager.unregister_widget(self.btn_ingest)
                self.glitch_manager.unregister_widget(self.btn_export)
                self.glitch_manager.unregister_widget(self.scale_tear)
                self.glitch_manager.unregister_widget(self.scale_aberration)
                self.glitch_manager.unregister_widget(self.scale_sort)
                self.glitch_manager.unregister_widget(self.status_label)
        except Exception:
            pass
            
        # Clean caches
        self.master_image = None
        self.preview_master = None
        self.preview_master_arr = None
        self.canvas_image_ref = None
        
        super().destroy()
