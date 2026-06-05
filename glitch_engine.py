import tkinter as tk
import numpy as np
import random
import time
import math
from PIL import Image, ImageTk, ImageGrab, ImageDraw, ImageEnhance

# -------------------------------------------------------------
# GLITCH TEXT CONSTANTS
# -------------------------------------------------------------
GLITCH_CHARS = ["█", "░", "▒", "▓", "§", "æ", "0", "1", "©", "Ø", "µ", "ß", "¶", "☠", "⚡", "☣", "👽", "👾", "Ø", "Æ"]

# ==============================================================================
# 1. FALLBACK SAFETY LAYER
# ==============================================================================
class GlitchSafety:
    """
    Context manager that monitors execution time of frame processing.
    If the process raises an exception or exceeds a threshold (16ms for 60FPS),
    it aborts cleanly and triggers cleanup to protect UI responsiveness.
    """
    def __init__(self, label="GlitchFrame", limit_ms=16.0, on_abort=None):
        self.label = label
        self.limit_ms = limit_ms
        self.on_abort = on_abort
        self.start_time = 0.0

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = (time.perf_counter() - self.start_time) * 1000.0
        if exc_type is not None or elapsed > self.limit_ms:
            # If there's an exception or we exceeded the time limit, abort
            if exc_type is not None:
                print(f"[GlitchSafety] Exception intercepted in {self.label}: {exc_val}")
            if self.on_abort:
                try:
                    self.on_abort()
                except Exception as clean_err:
                    print(f"[GlitchSafety] Error during cleanup callback: {clean_err}")
            
            # Suppress exceptions inside the block to preserve UI thread stability
            return True
        return False

# ==============================================================================
# 2. GLITCH MATRIX SPECIFICATIONS (PIL + NUMPY ACTIONS)
# ==============================================================================
class GlitchEffects:
    """
    Contains optimized static methods executing the 8 visual glitch effects.
    Uses C-accelerated NumPy array manipulations and PIL operations.
    """

    @staticmethod
    def screen_tear(arr, magnitude=0.2):
        """
        Effect 1: Screen Tear Effect
        Selects random horizontal slices and rolls the pixels horizontally,
        wrapping edges cleanly.
        """
        h, w, c = arr.shape
        # Scale magnitude
        max_shift = int(w * magnitude * 0.4)
        if max_shift <= 0:
            max_shift = 10
            
        num_tears = random.randint(1, 3)
        for _ in range(num_tears):
            slice_h = random.randint(5, max(10, int(h * 0.25)))
            slice_y = random.randint(0, max(1, h - slice_h))
            shift = random.randint(-max_shift, max_shift)
            if shift != 0:
                arr[slice_y:slice_y+slice_h, :, :3] = np.roll(
                    arr[slice_y:slice_y+slice_h, :, :3], 
                    shift=shift, 
                    axis=1
                )
        return arr

    @staticmethod
    def pixel_sort(arr, magnitude=0.3):
        """
        Effect 2: Pixel Sorting Glitch
        Sorts horizontal pixel segments based on their luminance values
        to create software memory bleeding streaks.
        """
        h, w, c = arr.shape
        # Define a sorting bounding box to process in <16ms
        bw = random.randint(int(w * 0.2), int(w * 0.6))
        bh = random.randint(5, max(10, int(h * 0.3)))
        bx = random.randint(0, max(1, w - bw))
        by = random.randint(0, max(1, h - bh))
        
        region = arr[by:by+bh, bx:bx+bw]
        if region.size == 0:
            return arr
            
        # Calculate luminance: L = 0.299R + 0.587G + 0.114B
        r = region[:, :, 0].astype(np.float32)
        g = region[:, :, 1].astype(np.float32)
        b = region[:, :, 2].astype(np.float32)
        lum = 0.299 * r + 0.587 * g + 0.114 * b
        
        # Sort each row in the slice independently by luminance
        for i in range(bh):
            sort_indices = np.argsort(lum[i])
            arr[by + i, bx:bx+bw, :3] = region[i][sort_indices]
            
        return arr

    @staticmethod
    def chromatic_aberration(arr, magnitude=0.15):
        """
        Effect 3: RGB Channel Separation (Chromatic Aberration)
        Splits red, green, and blue channels, offsetting red left/up and blue right/down.
        """
        h, w, c = arr.shape
        shift_x = int(w * magnitude * 0.08)
        shift_y = int(h * magnitude * 0.04)
        
        # Clamp shifts to reasonable values
        shift_x = max(1, min(w // 6, shift_x))
        shift_y = max(0, min(h // 12, shift_y))
        
        # Shift Red channel left/up
        arr[:, :, 0] = np.roll(arr[:, :, 0], shift=(-shift_y, -shift_x), axis=(0, 1))
        # Shift Blue channel right/down
        arr[:, :, 2] = np.roll(arr[:, :, 2], shift=(shift_y, shift_x), axis=(0, 1))
        return arr

    @staticmethod
    def data_corruption(arr, magnitude=0.4):
        """
        Effect 4: Data Corruption Overlay
        Draws sharp, procedurally-generated noise blocks or solid accent color blocks.
        """
        h, w, c = arr.shape
        num_blocks = random.randint(2, 6)
        for _ in range(num_blocks):
            size = random.randint(8, 32)
            bx = random.randint(0, max(1, w - size))
            by = random.randint(0, max(1, h - size))
            bw = random.randint(8, min(size, w - bx))
            bh = random.randint(8, min(size, h - by))
            
            if bw <= 0 or bh <= 0:
                continue
                
            block_mode = random.choice(["noise", "color", "invert"])
            if block_mode == "noise":
                arr[by:by+bh, bx:bx+bw, :3] = np.random.randint(0, 256, (bh, bw, 3), dtype=np.uint8)
            elif block_mode == "color":
                # Saturated cyberpunk palette (Green, Magenta, Cyan)
                col = random.choice([[0, 255, 0], [255, 0, 255], [0, 255, 255]])
                arr[by:by+bh, bx:bx+bw, :3] = col
            elif block_mode == "invert":
                arr[by:by+bh, bx:bx+bw, :3] = 255 - arr[by:by+bh, bx:bx+bw, :3]
        return arr

    @staticmethod
    def tv_static(arr, magnitude=0.25):
        """
        Effect 5: TV Static Interference
        Blends a random white noise texture over the pixel data at 15-30% opacity.
        """
        h, w, c = arr.shape
        alpha = random.uniform(0.15, 0.3)
        noise = np.random.randint(0, 256, (h, w, 3), dtype=np.uint8)
        arr[:, :, :3] = (arr[:, :, :3] * (1.0 - alpha) + noise * alpha).astype(np.uint8)
        return arr

    @staticmethod
    def scanline_glitch(arr, magnitude=0.3):
        """
        Effect 6: Scanline Glitch
        Darkens alternating horizontal row patterns and injects a vertical wave sync offset.
        """
        h, w, c = arr.shape
        freq = random.randint(2, 5)
        thickness = random.randint(1, 2)
        opacity = random.uniform(0.4, 0.65)
        
        # Apply raster lines overlay
        rows = np.arange(h)
        mask = (rows % freq) < thickness
        arr[mask, :, :3] = (arr[mask, :, :3] * opacity).astype(np.uint8)
        
        # Wave/Sync jitter (offsets horizontal columns using sine wave)
        if random.random() < 0.7:
            wave_amp = int(w * 0.04 * magnitude)
            if wave_amp > 0:
                wave_freq = random.uniform(0.04, 0.15)
                for y in range(h):
                    shift = int(wave_amp * math.sin(y * wave_freq))
                    if shift != 0:
                        arr[y, :, :3] = np.roll(arr[y, :, :3], shift=shift, axis=0)
        return arr

    @staticmethod
    def draw_hex_overlay(pil_img, magnitude=0.4):
        """
        Part of Effect 4 (Data Corruption Overlay):
        Renders procedurally generated hexadecimal string clusters directly on the PIL image.
        """
        w, h = pil_img.size
        draw = ImageDraw.Draw(pil_img)
        num_clusters = random.randint(1, 3)
        for _ in range(num_clusters):
            x = random.randint(0, max(0, w - 80))
            y = random.randint(0, max(0, h - 16))
            hex_str = "0x" + "".join(random.choice("0123456789ABCDEF") for _ in range(random.choice([2, 4, 6])))
            color = random.choice(["#00ff00", "#ff00ff", "#00ffff", "#ffff00"])
            draw.text((x, y), hex_str, fill=color)
        return pil_img

    @staticmethod
    def corrupt_text(text, magnitude=0.15):
        """
        Effect 7: Text Character Corruption
        Swaps characters in strings with binary digits or raw Unicode glitched blocks.
        """
        if not text:
            return text
        chars = list(text)
        length = len(chars)
        num_corrupt = max(1, int(length * magnitude))
        indices = random.sample(range(length), min(num_corrupt, length))
        
        for idx in indices:
            if chars[idx].strip():  # Skip whitespace to preserve layout bounds
                chars[idx] = random.choice(GLITCH_CHARS)
                
        return "".join(chars)

# ==============================================================================
# 3. CENTRAL MANAGER CLASS (GLITCHMANAGER)
# ==============================================================================
class GlitchManager:
    """
    Centralized controller that manages glitch registration, event bindings,
    rendering loops, text corruption caching, and background temporal loops.
    """
    def __init__(self, root):
        self.root = root
        self.targets = {}           # widget -> config dict
        self.active_glitches = {}   # widget -> active overlay Canvas
        self.text_backups = {}      # widget -> (original_text, property_name)
        
        # Mouse Trail tracking variables
        self.mouse_trail_active = False
        self.trail_canvas = None
        self.trail_history = []     # List of dicts (pil_image, x, y, age, speed_x, speed_y)
        self.trail_job = None
        
        # Initiate global background temporal loop
        self.temporal_job = None
        self.start_temporal_loop()
        
        # Mod visual effect pipeline (Vector B)
        self.global_glitch_active = False
        self.visual_modifiers = []
        self.tick_mods()

    # -------------------------------------------------------------
    # REGISTRATION & EVENTS
    # -------------------------------------------------------------
    def register_widget(self, widget, hover=True, click=True, temporal=True, magnitude=0.25):
        """Registers target widget and binds event listeners with non-blocking add='+' hooks."""
        self.targets[widget] = {
            "temporal": temporal,
            "magnitude": magnitude
        }
        
        if hover:
            widget.bind("<Enter>", lambda e: self.trigger_glitch(widget, duration=200, magnitude=magnitude * 0.6), add="+")
        if click:
            widget.bind("<Button-1>", lambda e: self.trigger_glitch(widget, duration=350, magnitude=magnitude * 1.5), add="+")
            
        # Hook mouse movement for trails if target widget requests it
        widget.bind("<Motion>", self.on_widget_motion, add="+")

    def unregister_widget(self, widget):
        """Safely cleans up registered widgets."""
        if widget in self.targets:
            del self.targets[widget]
        self.stop_widget_glitch(widget)

    # -------------------------------------------------------------
    # VISUAL MODIFIERS REGISTRY & TICK LOOPS (Vector B)
    # -------------------------------------------------------------
    def register_visual_modifier(self, callback):
        """Registers a custom callback to inject visual mod effects."""
        if callback not in self.visual_modifiers:
            self.visual_modifiers.append(callback)

    def unregister_visual_modifier(self, callback):
        """Unregisters a custom visual mod effect callback."""
        if callback in self.visual_modifiers:
            self.visual_modifiers.remove(callback)

    def tick_mods(self):
        """Ticking thread to pass temporal ticks to mods for background layout jiggles or adjustments."""
        if hasattr(self.root, "winfo_exists") and self.root.winfo_exists():
            for callback in list(self.visual_modifiers):
                try:
                    callback(None)
                except Exception:
                    pass
            self.root.after(100, self.tick_mods)

    # -------------------------------------------------------------
    # FIXED NON-BLOCKING MOUSE TRAIL GLITCH (EFFECT 8)
    # -------------------------------------------------------------
    def set_mouse_trail(self, active=True):
        """Toggles the Mouse Trail Glitch globally without full-screen overlays."""
        self.mouse_trail_active = active
        if not active:
            if self.trail_job:
                self.root.after_cancel(self.trail_job)
                self.trail_job = None
            # Clean up any leftover floating trail fragments
            if hasattr(self, 'trail_windows'):
                for tw in self.trail_windows:
                    try: tw.destroy()
                    except: pass
                self.trail_windows.clear()
            self.trail_history.clear()
        else:
            self.trail_windows = []
            self.run_mouse_trail_loop()

    def on_widget_motion(self, event):
        """Captures micro-snapshots and spawns them as transient lightweight overlays."""
        if not self.mouse_trail_active:
            return
            
        widget = event.widget
        mx = widget.winfo_rootx() + event.x
        my = widget.winfo_rooty() + event.y
        
        size = 40
        bx0 = mx - size // 2
        by0 = my - size // 2
        
        try:
            # Quick screen grab of what's under the cursor
            crop_img = ImageGrab.grab(bbox=(bx0, by0, bx0 + size, by0 + size))
            arr = np.array(crop_img)
            
            # Apply slight chaotic displacement math
            if random.random() < 0.5:
                arr = GlitchEffects.chromatic_aberration(arr, magnitude=0.5)
            else:
                arr = GlitchEffects.screen_tear(arr, magnitude=0.4)
            crop_img = Image.fromarray(arr)
            
            # Spawn an explicit, lightweight borderless popup window for THIS trail artifact
            tw = tk.Toplevel(self.root)
            tw.overrideredirect(True)
            tw.geometry(f"{size}x{size}+{bx0}+{by0}")
            tw.attributes("-topmost", True)
            
            photo = ImageTk.PhotoImage(crop_img)
            lbl = tk.Label(tw, image=photo, bd=0, bg="black", highlightthickness=0)
            lbl.pack()
            lbl.image_ref = photo # Prevent garbage collection
            
            self.trail_windows.append({
                "window": tw,
                "label": lbl,
                "img": crop_img,
                "x": bx0,
                "y": by0,
                "age": 1.0,
                "dx": random.uniform(-2.0, 2.0),
                "dy": random.uniform(-1.0, -3.0)
            })
        except Exception:
            pass

    def run_mouse_trail_loop(self):
        """Updates physics vectors, alpha fades, and kills old trail windows."""
        if not self.mouse_trail_active:
            return
            
        with GlitchSafety("MouseTrailLoop", limit_ms=16.0):
            retained = []
            for item in self.trail_windows:
                tw = item["window"]
                item["age"] -= 0.15 # Fast decay tracking
                
                if item["age"] <= 0.0 or not tw.winfo_exists():
                    try: tw.destroy()
                    except: pass
                    continue
                
                # Jitter step calculations
                item["x"] += int(item["dx"] + random.uniform(-1, 1))
                item["y"] += int(item["dy"] + random.uniform(-1, 1))
                
                try:
                    # Update screen coordinates dynamically
                    tw.geometry(f"+{item['x']}+{item['y']}")
                    
                    # Simulated artifact fade out using Pillow brightness scaling
                    enhancer = ImageEnhance.Brightness(item["img"])
                    faded = enhancer.enhance(item["age"])
                    photo = ImageTk.PhotoImage(faded)
                    
                    item["label"].config(image=photo)
                    item["label"].image_ref = photo
                    retained.append(item)
                except Exception:
                    try: tw.destroy()
                    except: pass
                    
            self.trail_windows = retained
            
        self.trail_job = self.root.after(33, self.run_mouse_trail_loop)

    # -------------------------------------------------------------
    # BACKGROUND TEMPORAL TRIGGER LOOP
    # -------------------------------------------------------------
    def start_temporal_loop(self):
        """Triggers randomized temporal glitches at unpredictable intervals (2.0 to 15.0 seconds)."""
        interval = int(random.uniform(2.0, 15.0) * 1000)
        self.temporal_job = self.root.after(interval, self.trigger_temporal_glitch)

    def trigger_temporal_glitch(self):
        if not self.targets:
            self.start_temporal_loop()
            return
            
        # 15% chance for a global screen-wide glitch
        if random.random() < 0.15:
            self.trigger_global_glitch(duration=random.randint(150, 400))
        else:
            # Otherwise select a random registered widget
            widget = random.choice(list(self.targets.keys()))
            if widget.winfo_exists() and widget.winfo_ismapped():
                cfg = self.targets[widget]
                if cfg["temporal"]:
                    duration = random.randint(80, 300)
                    self.trigger_glitch(widget, duration=duration, magnitude=cfg["magnitude"])
                    
        self.start_temporal_loop()

    def trigger_throttled_global_glitch(self, duration=300, magnitude=0.4, min_interval=1.5):
        """Triggers a global glitch only if min_interval seconds have passed since the last global glitch."""
        now = time.time()
        if not hasattr(self, '_last_global_glitch_time'):
            self._last_global_glitch_time = 0.0
        if now - self._last_global_glitch_time >= min_interval:
            self._last_global_glitch_time = now
            self.trigger_global_glitch(duration, magnitude)

    def trigger_throttled_glitch(self, widget, duration=200, magnitude=0.25, min_interval=1.0):
        """Triggers a widget glitch only if min_interval seconds have passed since the last glitch on this widget."""
        now = time.time()
        if not hasattr(self, '_last_widget_glitch_times'):
            self._last_widget_glitch_times = {}
        last_time = self._last_widget_glitch_times.get(widget, 0.0)
        if now - last_time >= min_interval:
            self._last_widget_glitch_times[widget] = now
            self.trigger_glitch(widget, duration, magnitude)

    # -------------------------------------------------------------
    # TARGETED GLITCH MECHANISM
    # -------------------------------------------------------------
    def trigger_glitch(self, widget, duration=200, magnitude=0.25):
        """Fires a localized glitch on a widget. Intercepts pixel data and overlays a canvas."""
        if not widget.winfo_exists() or not widget.winfo_ismapped():
            return
            
        # Clean up existing glitch overlay on the widget if it's currently running
        self.stop_widget_glitch(widget)
        
        # Grab dimensions and absolute screen position
        x = widget.winfo_rootx()
        y = widget.winfo_rooty()
        w = widget.winfo_width()
        h = widget.winfo_height()
        
        if w <= 4 or h <= 4:
            return
            
        # Capture the widget's current appearance ONCE to eliminate capture overhead in loop
        try:
            base_image = ImageGrab.grab(bbox=(x, y, x + w, y + h))
        except Exception:
            return
            
        # Handle Text Corruption (Effect 7) on standard widgets
        self.corrupt_text_widgets_in(widget, magnitude)
        
        # Create the canvas overlay layer positioned relative to the parent widget
        px = widget.winfo_x()
        py = widget.winfo_y()
        
        canvas = tk.Canvas(widget.master, width=w, height=h, highlightthickness=0, bd=0, bg="black")
        canvas.place(x=px, y=py, width=w, height=h)
        tk.Misc.lift(canvas)

        canvas.bind("<Button-1>", lambda e: widget.event_generate("<Button-1>", x=e.x, y=e.y))
        canvas.bind("<ButtonRelease-1>", lambda e: widget.event_generate("<ButtonRelease-1>", x=e.x, y=e.y))
        
        self.active_glitches[widget] = canvas
        
        # Start the local visual frame-render ticks
        start_time = time.time()
        self.render_glitch_frames(widget, base_image, start_time, duration, magnitude)

    def render_glitch_frames(self, widget, base_image, start_time, duration, magnitude):
        """Recursively draws glitched frames using cached image data to prevent frame drops."""
        if widget not in self.active_glitches:
            return
            
        elapsed = (time.time() - start_time) * 1000.0
        if elapsed >= duration or not widget.winfo_exists():
            self.stop_widget_glitch(widget)
            return
            
        canvas = self.active_glitches[widget]
        
        # Safe processing threshold
        with GlitchSafety("WidgetGlitchFrame", limit_ms=25.0, on_abort=lambda: self.stop_widget_glitch(widget)):
            # Convert cached base image to array instead of running an active screen grab
            arr = np.array(base_image)
            
            # Apply dynamic visual modifiers from loaded mods (Vector B)
            for modifier in list(self.visual_modifiers):
                try:
                    res = modifier(arr)
                    if res is not None:
                        arr = res
                except Exception as e:
                    print(f"Error applying widget visual modifier: {e}")
            
            effects = [
                GlitchEffects.screen_tear,
                GlitchEffects.pixel_sort,
                GlitchEffects.chromatic_aberration,
                GlitchEffects.data_corruption,
                GlitchEffects.tv_static,
                GlitchEffects.scanline_glitch
            ]
            
            # Keep effect calculations modest to leave CPU headroom for ChaoHub logic
            chosen = random.sample(effects, k=random.randint(1, 2))
            for effect in chosen:
                arr = effect(arr, magnitude=magnitude)
                
            frame_img = Image.fromarray(arr)
            
            if random.random() < 0.3:
                frame_img = GlitchEffects.draw_hex_overlay(frame_img, magnitude)
                
            photo = ImageTk.PhotoImage(frame_img)
            
            if canvas.winfo_exists():
                canvas.delete("all")
                canvas.create_image(0, 0, image=photo, anchor="nw")
                canvas.photo_ref = photo
            
        # Queue frame update comfortably at 45ms loops (~22 updates a sec is great for glitches)
        widget.after(45, lambda: self.render_glitch_frames(widget, base_image, start_time, duration, magnitude))

    def stop_widget_glitch(self, widget):
        """Removes the overlay canvas and restores the original widget visibility."""
        if widget in self.active_glitches:
            canvas = self.active_glitches.pop(widget)
            try:
                canvas.destroy()
            except Exception:
                pass
        
        # Restore corrupted text
        self.restore_text_widgets_in(widget)

    # -------------------------------------------------------------
    # TEXT CORRUPTION LOGIC (EFFECT 7)
    # -------------------------------------------------------------
    def corrupt_text_widgets_in(self, parent, magnitude):
        """Traverses the parent widget tree and corrupts text strings in labels and buttons."""
        widgets = [parent]
        # Gather child widgets
        try:
            widgets.extend(parent.winfo_children())
        except Exception:
            pass
            
        for w in widgets:
            # Check widgets that support text properties
            for prop in ["text", "label"]:
                if hasattr(w, "cget"):
                    try:
                        val = w.cget(prop)
                        if val and isinstance(val, str) and w not in self.text_backups:
                            self.text_backups[w] = (val, prop)
                            corrupted = GlitchEffects.corrupt_text(val, magnitude)
                            w.config(**{prop: corrupted})
                    except Exception:
                        pass
                # Handle special case: custom components that store text differently
                if hasattr(w, "text") and isinstance(w.text, str) and w not in self.text_backups:
                    self.text_backups[w] = (w.text, "text")
                    corrupted = GlitchEffects.corrupt_text(w.text, magnitude)
                    w.text = corrupted
                    # If it's a BrokenImageButton, it has a Label inside it
                    if hasattr(w, "label") and w.label.winfo_exists():
                        try:
                            w.label.config(text=corrupted)
                        except Exception:
                            pass

    def restore_text_widgets_in(self, parent):
        """Restores original text backups for all children."""
        restored_keys = []
        for w, (original_val, prop) in self.text_backups.items():
            try:
                if w.winfo_exists():
                    if prop == "text" and hasattr(w, "text"):
                        w.text = original_val
                    w.config(**{prop: original_val})
            except Exception:
                pass
            restored_keys.append(w)
            
        for w in restored_keys:
            self.text_backups.pop(w, None)

    # -------------------------------------------------------------
    # GLOBAL FULL-SCREEN GLITCH
    # -------------------------------------------------------------
    def trigger_global_glitch(self, duration=300, magnitude=0.4):
        """Captures the entire screen and renders a full-window glitch overlay."""
        self.global_glitch_active = True
        
        # Telemetry: check system_breach achievement if GreenMatrixMod is active
        try:
            app = getattr(self.root, "app_instance", None)
            if app and hasattr(app, "current_frame") and app.current_frame:
                if app.current_frame.__class__.__name__ == "GreenMatrixMod":
                    app.achievement_manager.grant_achievement("system_breach")
        except Exception:
            pass

        w = self.root.winfo_width()
        h = self.root.winfo_height()
        
        if w <= 10 or h <= 10:
            self.global_glitch_active = False
            return
            
        # Draw full screen overlay canvas directly placed on the root
        canvas = tk.Canvas(self.root, width=w, height=h, highlightthickness=0, bd=0, bg="black")
        canvas.place(x=0, y=0, width=w, height=h)
        tk.Misc.lift(canvas)
        
        # Capture root screen
        try:
            rx = self.root.winfo_rootx()
            ry = self.root.winfo_rooty()
            base_image = ImageGrab.grab(bbox=(rx, ry, rx + w, ry + h))
        except Exception:
            self.global_glitch_active = False
            canvas.destroy()
            return
            
        # Trigger background audio beep/screech for immersion if available
        try:
            from chaohub import play_sound_effect
            play_sound_effect("click")
        except (ImportError, AttributeError):
            pass  # Fallback gracefully if running standalone without chaohub
        
        # Local loop tracking
        start_time = time.time()
        self.render_global_frames(canvas, base_image, start_time, duration, magnitude)

    def render_global_frames(self, canvas, base_image, start_time, duration, magnitude):
        """Loops rendering of fullscreen glitched frames using cached image manipulation."""
        if not canvas.winfo_exists():
            self.global_glitch_active = False
            return
            
        elapsed = (time.time() - start_time) * 1000.0
        if elapsed >= duration or not self.root.winfo_exists():
            try: canvas.destroy()
            except: pass
            self.global_glitch_active = False
            return
            
        # Limit limit checking to lower precision if CPU is busy
        with GlitchSafety("GlobalGlitchFrame", limit_ms=25.0, on_abort=lambda: self.safe_destroy_canvas(canvas)):
            # Work on a lightweight copy of the snapshot
            arr = np.array(base_image)
            
            # Apply dynamic visual modifiers from loaded mods (Vector B)
            for modifier in list(self.visual_modifiers):
                try:
                    res = modifier(arr)
                    if res is not None:
                        arr = res
                except Exception as e:
                    print(f"Error applying global visual modifier: {e}")
            
            # Reduce effect stack count for global frames to protect processing headroom
            arr = GlitchEffects.chromatic_aberration(arr, magnitude=magnitude * 1.1)
            if random.random() < 0.5:
                arr = GlitchEffects.screen_tear(arr, magnitude=magnitude * 1.2)
            if random.random() < 0.3:
                arr = GlitchEffects.tv_static(arr, magnitude=magnitude * 0.5)
                
            frame_img = Image.fromarray(arr)
            
            if random.random() < 0.4:
                frame_img = GlitchEffects.draw_hex_overlay(frame_img, magnitude)
                
            photo = ImageTk.PhotoImage(frame_img)
            
            if canvas.winfo_exists():
                canvas.delete("all")
                canvas.create_image(0, 0, image=photo, anchor="nw")
                canvas.photo_ref = photo
            
        # Throttle update slightly to 45ms to reduce CPU render storm
        self.root.after(45, lambda: self.render_global_frames(canvas, base_image, start_time, duration, magnitude))

    def safe_destroy_canvas(self, canvas):
        """Safely tears down canvas element without throwing thread execution errors."""
        try:
            if canvas.winfo_exists():
                canvas.destroy()
        except:
            pass


# ==============================================================================
# 4. INTERACTIVE TEST CLIENT
# ==============================================================================
if __name__ == "__main__":
    # Create standalone demo application showcasing GlitchManager
    root = tk.Tk()
    root.title("Glitch Engine Terminal Diagnostics")
    root.geometry("800x600")
    root.config(bg="#000000")
    
    # Header Panel
    hdr = tk.Frame(root, bg="#0b0b0b", highlightthickness=1, highlightbackground="#ff00ff")
    hdr.pack(fill="x", padx=10, pady=10)
    tk.Label(hdr, text="GLITCH MATRIX CORE DIAGNOSTIC CLIENT", fg="#ff00ff", bg="#0b0b0b", font=("Courier", 14, "bold")).pack(pady=10)
    
    # Info label
    info = tk.Label(root, text="Hover buttons or click them to test intercepts. Background temporal loop active.", fg="#00ff00", bg="#000000", font=("Courier", 10))
    info.pack(pady=5)
    
    # Manager
    manager = GlitchManager(root)
    manager.set_mouse_trail(True) # Turn on mouse trails
    
    # Left container
    left = tk.Frame(root, bg="#000000")
    left.pack(side="left", fill="both", expand=True, padx=10, pady=10)
    
    # Buttons
    btn1 = tk.Button(left, text="TRIGGER GLOBAL SCREEN GLITCH", bg="#111", fg="#00ffff", activebackground="#00ffff", activeforeground="#111", font=("Courier", 10, "bold"), bd=1)
    btn1.pack(fill="x", pady=5)
    btn1.config(command=lambda: manager.trigger_global_glitch(duration=400, magnitude=0.5))
    manager.register_widget(btn1, hover=True, click=True, magnitude=0.3)
    
    btn2 = tk.Button(left, text="CORRUPT THIS PANEL TEXT", bg="#111", fg="#ffff00", activebackground="#ffff00", activeforeground="#111", font=("Courier", 10, "bold"), bd=1)
    btn2.pack(fill="x", pady=5)
    manager.register_widget(btn2, hover=True, click=True, magnitude=0.4)
    
    # Label to test Text Corruption
    lbl = tk.Label(left, text="DIAGNOSTIC BLOCK INTTACT - READY FOR FLOOD", fg="#00ff00", bg="#050505", font=("Courier", 11, "bold"), highlightthickness=1, highlightbackground="#00ff00")
    lbl.pack(fill="x", pady=15, ipady=10)
    manager.register_widget(lbl, hover=True, click=True, magnitude=0.25)
    
    # Exploit graph mock canvas
    cvs = tk.Canvas(left, bg="#050505", height=150, highlightthickness=1, highlightbackground="#00ff00")
    cvs.pack(fill="x", pady=5)
    cvs.create_line(10, 100, 150, 20, fill="#00ff00", width=2)
    cvs.create_line(150, 20, 290, 120, fill="#00ff00", width=2)
    cvs.create_line(290, 120, 400, 40, fill="#00ff00", width=2)
    cvs.create_text(200, 75, text="MOCK RADAR SCAN", fill="#ff00ff", font=("Courier", 12, "bold"))
    manager.register_widget(cvs, hover=True, click=True, magnitude=0.35)
    
    root.mainloop()
