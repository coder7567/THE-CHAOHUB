import os
import tkinter as tk
from tkinter import messagebox
import datetime
from PIL import Image, ImageDraw
from chiptune_tracker import ChiptuneTrackerPanel
from glitch_studio import GlitchArtStudioPanel

# Aesthetic color palettes (hacker terminal styling)
BG_DARK = "#000000"
BG_PANEL = "#0b0b0b"
FG_GREEN = "#00ff00"
FG_MAGENTA = "#ff00ff"
FG_CYAN = "#00ffff"
FG_YELLOW = "#ffff00"
ALERT_RED = "#ff0000"

def play_sound_effect(name):
    """Loads and plays one of our synthesized sound effects via Pygame."""
    try:
        # Check if we can import and run the main app's sound player first
        try:
            from chaohub import play_sound_effect as ch_play
            ch_play(name)
            return
        except ImportError:
            pass

        # Standalone playback fallback if running module directly
        import pygame
        sound_dir = os.path.join(os.path.expanduser("~"), "ChaoHub_Data", "sounds")
        path = os.path.join(sound_dir, f"{name}.wav")
        if os.path.exists(path) and pygame.mixer.get_init():
            sound = pygame.mixer.Sound(path)
            sound.set_volume(0.6)
            sound.play()
    except Exception:
        pass

class CreativeSuiteModule(tk.Frame):
    """Module G: Cyber-Neon Pixel Art Editor with matrix decoupling and PNG cloaking."""
    def __init__(self, parent):
        super().__init__(parent, bg=BG_DARK)
        self.config(highlightbackground=FG_MAGENTA, highlightthickness=1)

        # Active grid configuration parameters
        self.grid_size = 16
        self.grid_visible = True
        
        # Neon-Only Color Palette Swatches (exactly 5 + eraser)
        self.palette = [
            ("#00ff00", "MATRIX GREEN"),
            ("#00ffff", "NEON CYAN"),
            ("#ff00ff", "HOT MAGENTA"),
            ("#ff0000", "LASER RED"),
            ("#ffff00", "WARNING YELLOW"),
            ("#000000", "ERASER DATA")
        ]
        self.active_color = "#00ff00" # Default selector is Matrix Green

        # Decoupled matrix state
        self.reset_matrix_state()

        # Layout splitting frames setup
        self.build_ui()

    def reset_matrix_state(self):
        """Initializes/wipes the backend sparse state array."""
        self.grid_data = [[None for _ in range(self.grid_size)] for _ in range(self.grid_size)]

    def build_ui(self):
        # 1. Tab Bar at the top
        self.tab_frame = tk.Frame(self, bg=BG_DARK)
        self.tab_frame.pack(fill="x", side="top", padx=10, pady=(5, 5))
        
        self.btn_tab_pixel = tk.Button(self.tab_frame, text="[ PIXEL ART MATRIX EDITOR ]", command=self.show_pixel_editor,
                                       bg=FG_GREEN, fg=BG_DARK, activebackground=FG_GREEN, activeforeground=BG_DARK,
                                       font=("Courier", 10, "bold"), bd=1, relief="flat", highlightbackground=FG_GREEN)
        self.btn_tab_pixel.pack(side="left", padx=5)
        
        self.btn_tab_tracker = tk.Button(self.tab_frame, text="[ CHIPTUNE TRACKER MATRIX ]", command=self.show_tracker_panel,
                                         bg=BG_DARK, fg=FG_CYAN, activebackground=FG_CYAN, activeforeground=BG_DARK,
                                         font=("Courier", 10, "bold"), bd=1, relief="flat", highlightbackground=FG_CYAN)
        self.btn_tab_tracker.pack(side="left", padx=5)
        
        self.btn_tab_glitch = tk.Button(self.tab_frame, text="[ GLITCH ART STUDIO ]", command=self.show_glitch_panel,
                                        bg=BG_DARK, fg=FG_MAGENTA, activebackground=FG_MAGENTA, activeforeground=BG_DARK,
                                        font=("Courier", 10, "bold"), bd=1, relief="flat", highlightbackground=FG_MAGENTA)
        self.btn_tab_glitch.pack(side="left", padx=5)
        
        # 2. Outer containers for views
        self.pixel_editor_container = tk.Frame(self, bg=BG_DARK)
        self.pixel_editor_container.pack(fill="both", expand=True)
        
        self.tracker_container = tk.Frame(self, bg=BG_DARK)
        self.glitch_container = tk.Frame(self, bg=BG_DARK)
        
        # -------------------------------------------------------------
        # BUILD PIXEL EDITOR VIEW (Inside self.pixel_editor_container)
        # -------------------------------------------------------------
        # Left Panel (Drawing Canvas Viewport Container)
        self.left_frame = tk.Frame(self.pixel_editor_container, bg=BG_DARK)
        self.left_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        canvas_header = tk.Frame(self.left_frame, bg=BG_DARK)
        canvas_header.pack(fill="x", pady=(0, 5))
        tk.Label(canvas_header, text="VECTOR ART MATRIX VIEWPORT", fg=FG_CYAN, bg=BG_DARK, font=("Courier", 11, "bold")).pack(side="left")

        # Crisp Canvas Viewport (480x480)
        self.canvas_size = 480
        self.canvas = tk.Canvas(self.left_frame, width=self.canvas_size, height=self.canvas_size,
                                bg=BG_DARK, highlightthickness=1, highlightbackground=FG_MAGENTA)
        self.canvas.pack(anchor="center")

        # Bind Drawing mouse events
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)

        # Right Panel (Control Dashboard & Palette Bar)
        self.right_frame = tk.Frame(self.pixel_editor_container, bg=BG_PANEL, highlightthickness=1, highlightbackground="#333333", width=320)
        self.right_frame.pack(side="right", fill="both", expand=False, padx=10, pady=10)
        self.right_frame.pack_propagate(False)

        # Title Label
        title_lbl = tk.Label(self.right_frame, text="PIXEL ART MATRIX CORE", fg=FG_MAGENTA, bg=BG_PANEL, font=("Courier", 12, "bold"))
        title_lbl.pack(pady=15, padx=10)

        # 1. Grid Size Swapper Frame
        grid_sel_frame = tk.Frame(self.right_frame, bg=BG_PANEL)
        grid_sel_frame.pack(fill="x", padx=15, pady=5)
        tk.Label(grid_sel_frame, text="GRID RESOLUTION:", fg=FG_YELLOW, bg=BG_PANEL, font=("Courier", 10, "bold")).pack(anchor="w", pady=(0, 5))

        self.btn_16 = tk.Button(grid_sel_frame, text="[ 16x16 MATRIX ]", command=lambda: self.change_grid_size(16),
                                bg=BG_DARK, fg=FG_GREEN, activebackground=FG_GREEN, activeforeground=BG_DARK,
                                font=("Courier", 9, "bold"), bd=1, relief="flat", highlightbackground=FG_GREEN)
        self.btn_16.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.btn_32 = tk.Button(grid_sel_frame, text="[ 32x32 MATRIX ]", command=lambda: self.change_grid_size(32),
                                bg=BG_DARK, fg=FG_GREEN, activebackground=FG_GREEN, activeforeground=BG_DARK,
                                font=("Courier", 9, "bold"), bd=1, relief="flat", highlightbackground=FG_GREEN)
        self.btn_32.pack(side="right", fill="x", expand=True, padx=(5, 0))

        # Initial Button Styling highlights
        self.update_resolution_buttons()

        # 2. Color Palette Swatches Container
        palette_label = tk.Label(self.right_frame, text="NEON PALETTE SWATCHES:", fg=FG_YELLOW, bg=BG_PANEL, font=("Courier", 10, "bold"))
        palette_label.pack(anchor="w", padx=15, pady=(15, 5))

        self.palette_container = tk.Frame(self.right_frame, bg=BG_PANEL)
        self.palette_container.pack(fill="x", padx=15, pady=5)

        self.swatch_frames = {}
        for color, name in self.palette:
            swatch_row = tk.Frame(self.palette_container, bg=BG_PANEL, cursor="hand2")
            swatch_row.pack(fill="x", pady=4)

            # Border wrapper frame for active indicator highlights
            border_frame = tk.Frame(swatch_row, bg=BG_DARK, highlightthickness=1, highlightbackground="#333333", width=26, height=26)
            border_frame.pack(side="left", padx=(0, 10))
            border_frame.pack_propagate(False)

            # Colored visual indicator inside border
            color_box = tk.Canvas(border_frame, bg=color, highlightthickness=0, width=24, height=24)
            color_box.pack(fill="both", expand=True)

            # Label for color swatch name
            label = tk.Label(swatch_row, text=name, fg=color if color != "#000000" else "#555555", bg=BG_PANEL, font=("Courier", 9, "bold"))
            label.pack(side="left")

            # Bind click triggers
            swatch_row.bind("<Button-1>", lambda e, c=color: self.select_color(c))
            color_box.bind("<Button-1>", lambda e, c=color: self.select_color(c))
            label.bind("<Button-1>", lambda e, c=color: self.select_color(c))

            self.swatch_frames[color] = border_frame

        # Highlight current swatch color
        self.update_swatch_highlights()

        # 3. Canvas Utilities Section
        utils_label = tk.Label(self.right_frame, text="CANVAS DIAGNOSTICS:", fg=FG_YELLOW, bg=BG_PANEL, font=("Courier", 10, "bold"))
        utils_label.pack(anchor="w", padx=15, pady=(15, 5))

        self.btn_grid_toggle = tk.Button(self.right_frame, text="[ TOGGLE GRID OVERLAY: ON ]", command=self.toggle_grid,
                                         bg=BG_DARK, fg=FG_CYAN, activebackground=FG_CYAN, activeforeground=BG_DARK,
                                         font=("Courier", 9, "bold"), bd=1, relief="flat", highlightbackground=FG_CYAN)
        self.btn_grid_toggle.pack(fill="x", padx=15, pady=5)

        self.btn_wipe = tk.Button(self.right_frame, text="[ WIPE CANVAS DATA ]", command=self.wipe_canvas_action,
                                  bg=BG_DARK, fg=ALERT_RED, activebackground=ALERT_RED, activeforeground=BG_DARK,
                                  font=("Courier", 9, "bold"), bd=1, relief="flat", highlightbackground=ALERT_RED)
        self.btn_wipe.pack(fill="x", padx=15, pady=5)

        # 4. Export Section
        export_label = tk.Label(self.right_frame, text="COMPILE & SECURE:", fg=FG_YELLOW, bg=BG_PANEL, font=("Courier", 10, "bold"))
        export_label.pack(anchor="w", padx=15, pady=(15, 5))

        self.btn_export = tk.Button(self.right_frame, text="[ EXPORT ARTIFACT ]", command=self.export_artifact_action,
                                    bg=BG_DARK, fg=FG_MAGENTA, activebackground=FG_MAGENTA, activeforeground=BG_DARK,
                                    font=("Courier", 10, "bold"), bd=1, relief="flat", highlightbackground=FG_MAGENTA, height=2)
        self.btn_export.pack(fill="x", padx=15, pady=5)

        # Bottom status display line
        self.status_label = tk.Label(self.right_frame, text="[ STATUS: CORE SYSTEM ONLINE ]", fg=FG_GREEN, bg=BG_PANEL, font=("Courier", 9, "bold"))
        self.status_label.pack(side="bottom", fill="x", pady=15)

        # Force initial drawing grids rendering
        self.draw_grid_lines()
        
        # -------------------------------------------------------------
        # BUILD TRACKER VIEW (Inside self.tracker_container)
        # -------------------------------------------------------------
        parent_glitch_mgr = None
        if hasattr(self, "master") and hasattr(self.master, "glitch_manager"):
            parent_glitch_mgr = self.master.glitch_manager
        elif hasattr(self, "glitch_manager"):
            parent_glitch_mgr = self.glitch_manager
            
        self.tracker_panel = ChiptuneTrackerPanel(self.tracker_container, glitch_manager=parent_glitch_mgr)
        self.tracker_panel.pack(fill="both", expand=True, padx=10, pady=10)
        
        # -------------------------------------------------------------
        # BUILD GLITCH STUDIO VIEW (Inside self.glitch_container)
        # -------------------------------------------------------------
        self.glitch_panel = GlitchArtStudioPanel(self.glitch_container, glitch_manager=parent_glitch_mgr)
        self.glitch_panel.pack(fill="both", expand=True, padx=10, pady=10)

    def show_pixel_editor(self):
        play_sound_effect("click")
        if hasattr(self, "tracker_panel"):
            self.tracker_panel.stop_playback()
        self.tracker_container.pack_forget()
        self.glitch_container.pack_forget()
        self.pixel_editor_container.pack(fill="both", expand=True)
        self.btn_tab_pixel.config(bg=FG_GREEN, fg=BG_DARK)
        self.btn_tab_tracker.config(bg=BG_DARK, fg=FG_CYAN)
        self.btn_tab_glitch.config(bg=BG_DARK, fg=FG_MAGENTA)

    def show_tracker_panel(self):
        play_sound_effect("click")
        self.pixel_editor_container.pack_forget()
        self.glitch_container.pack_forget()
        self.tracker_container.pack(fill="both", expand=True)
        self.btn_tab_pixel.config(bg=BG_DARK, fg=FG_GREEN)
        self.btn_tab_tracker.config(bg=FG_CYAN, fg=BG_DARK)
        self.btn_tab_glitch.config(bg=BG_DARK, fg=FG_MAGENTA)

    def show_glitch_panel(self):
        # 1. Update audio thread state flag from previous tab first to avoid stutter/thread collision
        if hasattr(self, "tracker_panel"):
            self.tracker_panel.stop_playback()
            
        play_sound_effect("click")
        
        # Hide other editors
        self.pixel_editor_container.pack_forget()
        self.tracker_container.pack_forget()
        
        # Show glitch panel
        self.glitch_container.pack(fill="both", expand=True)
        
        # Highlight active tab buttons
        self.btn_tab_pixel.config(bg=BG_DARK, fg=FG_GREEN)
        self.btn_tab_tracker.config(bg=BG_DARK, fg=FG_CYAN)
        self.btn_tab_glitch.config(bg=FG_MAGENTA, fg=BG_DARK)

    def destroy(self):
        """Override destroy to safely clear audio loops and threads before dropping views."""
        try:
            if hasattr(self, "tracker_panel") and self.tracker_panel:
                self.tracker_panel.cleanup()
        except Exception as e:
            print(f"[CreativeSuiteModule] Tracker cleanup exception: {e}")
        try:
            if hasattr(self, "glitch_panel") and self.glitch_panel:
                self.glitch_panel.destroy()
        except Exception as e:
            print(f"[CreativeSuiteModule] Glitch panel cleanup exception: {e}")
        super().destroy()

    def update_resolution_buttons(self):
        """Toggles the visual state highlighting on resolution selectors."""
        if self.grid_size == 16:
            self.btn_16.config(bg=FG_GREEN, fg=BG_DARK)
            self.btn_32.config(bg=BG_DARK, fg=FG_GREEN)
        else:
            self.btn_16.config(bg=BG_DARK, fg=FG_GREEN)
            self.btn_32.config(bg=FG_GREEN, fg=BG_DARK)

    def select_color(self, color):
        """Activates color swatch selection and updates visual border highlight cues."""
        play_sound_effect("click")
        self.active_color = color
        self.update_swatch_highlights()

    def update_swatch_highlights(self):
        """Highlights the active swatch with a thick cyan or magenta highlight border."""
        for color, frame in self.swatch_frames.items():
            if color == self.active_color:
                # Active swatch gets Cyan highlight border
                frame.config(highlightbackground=FG_CYAN, highlightthickness=2)
            else:
                # Inactive swatches get subtle dark boundary line
                frame.config(highlightbackground="#333333", highlightthickness=1)

    def change_grid_size(self, size):
        """Changes grid resolution, warning user if drawing data exists on canvas."""
        if self.grid_size == size:
            return

        # Check if the canvas contains active custom artwork data
        has_artwork = False
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                if self.grid_data[row][col] is not None:
                    has_artwork = True
                    break
            if has_artwork:
                break

        if has_artwork:
            play_sound_effect("beep")
            # Ask confirmation dialogue
            proceed = messagebox.askyesno("WARNING", "Changing grid size will wipe the active canvas data. Proceed?")
            if not proceed:
                return

        play_sound_effect("click")
        self.grid_size = size
        self.reset_matrix_state()
        
        # Explicitly clear out all canvas items to prevent orphan lag
        self.canvas.delete("all")
        self.draw_grid_lines()
        self.update_resolution_buttons()

    def toggle_grid(self):
        """Toggles the vector grid overlay rendering state ON or OFF."""
        play_sound_effect("click")
        self.grid_visible = not self.grid_visible
        if self.grid_visible:
            self.btn_grid_toggle.config(text="[ TOGGLE GRID OVERLAY: ON ]", fg=FG_CYAN)
        else:
            self.btn_grid_toggle.config(text="[ TOGGLE GRID OVERLAY: OFF ]", fg="#555555")
        
        self.draw_grid_lines()

    def wipe_canvas_action(self):
        """Wipes the active canvas and prompts warning."""
        play_sound_effect("beep")
        proceed = messagebox.askyesno("WARNING", "Wipe all pixel drawing matrix elements?")
        if proceed:
            play_sound_effect("click")
            self.reset_matrix_state()
            self.canvas.delete("pixel")
            self.draw_grid_lines()

    def draw_grid_lines(self):
        """Draws clean vector outline grid lines over the cells."""
        self.canvas.delete("grid_line")
        if not self.grid_visible:
            return

        cell_size = self.canvas_size // self.grid_size
        # Draw vertical lines
        for i in range(1, self.grid_size):
            x = i * cell_size
            self.canvas.create_line(x, 0, x, self.canvas_size, fill="#222222", tags="grid_line")

        # Draw horizontal lines
        for j in range(1, self.grid_size):
            y = j * cell_size
            self.canvas.create_line(0, y, self.canvas_size, y, fill="#222222", tags="grid_line")

    def get_cell_coordinates(self, event):
        """Converts mouse click x,y to grid matrix indices row,col."""
        cell_size = self.canvas_size // self.grid_size
        col = event.x // cell_size
        row = event.y // cell_size
        # Clamp indices in valid bounds
        row = max(0, min(self.grid_size - 1, row))
        col = max(0, min(self.grid_size - 1, col))
        return row, col

    def draw_pixel_at(self, row, col):
        """Updates internal matrix state array and draws/erases the canvas visual item."""
        cell_size = self.canvas_size // self.grid_size
        tag = f"cell_{row}_{col}"

        if self.active_color == "#000000":
            # Eraser mode (wipes state, deletes canvas rectangle)
            self.grid_data[row][col] = None
            self.canvas.delete(tag)
        else:
            # Color draw mode (sets state, draws flat colored box)
            if self.grid_data[row][col] != self.active_color:
                self.grid_data[row][col] = self.active_color
                self.canvas.delete(tag)

                x1 = col * cell_size
                y1 = row * cell_size
                x2 = x1 + cell_size
                y2 = y1 + cell_size
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=self.active_color, outline="", tags=(tag, "pixel"))

        # Re-raise vector grid lines to the top so they stay visible
        self.canvas.tag_raise("grid_line")

    def on_canvas_click(self, event):
        """Single click mouse pixel painting handler."""
        row, col = self.get_cell_coordinates(event)
        self.draw_pixel_at(row, col)

    def on_canvas_drag(self, event):
        """Click and drag mouse pixel painting handler."""
        row, col = self.get_cell_coordinates(event)
        self.draw_pixel_at(row, col)

    def export_artifact_action(self):
        """Compiles grid matrix, upscales to 512x512 with nearest-neighbor, and saves it as .png.enc."""
        play_sound_effect("click")
        
        # Telemetry: check master_artisan achievement
        try:
            # Retrieve app instance from root
            app = getattr(self.winfo_toplevel(), "app_instance", None)
            if app:
                app.achievement_manager.grant_achievement("master_artisan")
        except Exception:
            pass

        # 1. Initialize data folders safely targeting user directory
        art_dir = os.path.join(os.path.expanduser("~"), "ChaoHub_Data", "art")
        try:
            if not os.path.exists(art_dir):
                os.makedirs(art_dir)
        except Exception as e:
            self.status_label.config(text=f"[ ERROR: CANNOT ACCESS {art_dir} ]", fg=ALERT_RED)
            return

        # 2. Draw raw micro-scale image pixels
        try:
            # Solid black canvas background
            raw_img = Image.new("RGBA", (self.grid_size, self.grid_size), (0, 0, 0, 255))
            draw = ImageDraw.Draw(raw_img)

            for r in range(self.grid_size):
                for c in range(self.grid_size):
                    color = self.grid_data[r][c]
                    if color is not None:
                        # Extract color hex to RGB tuple
                        r_val = int(color[1:3], 16)
                        g_val = int(color[3:5], 16)
                        b_val = int(color[5:7], 16)
                        draw.point((c, r), fill=(r_val, g_val, b_val, 255))
                    else:
                        draw.point((c, r), fill=(0, 0, 0, 255))

            # 3. Upscale using Nearest-Neighbor interpolation for pixel sharpness
            upscaled = raw_img.resize((512, 512), Image.NEAREST)

            # 4. Generate timestamp name (ART_CH_YYYYMMDD_HHMMSS.png.enc)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ART_CH_{timestamp}.png.enc"
            filepath = os.path.join(art_dir, filename)

            # Save file explicitly in PNG format to support the ".enc" twist
            upscaled.save(filepath, format="PNG")

            # 5. UI Success Notification
            play_sound_effect("beep")
            self.flash_status()
            
            # Print shell message for logs
            print(f"[CreativeSuiteModule] Art successfully compiled to: {filepath}")

        except Exception as err:
            self.status_label.config(text=f"[ ERROR: COMPILE FAILED: {str(err)[:22]} ]", fg=ALERT_RED)

    def flash_status(self, count=6):
        """Blinks status bar color between green and magenta to notify write success."""
        if count <= 0:
            self.status_label.config(text="[ STATUS: ARTIFACT ENCRYPTED & SECURED TO DISK ]", fg=FG_GREEN)
            # Reset default status label after 4 seconds
            self.after(4000, lambda: self.status_label.config(text="[ STATUS: CORE SYSTEM ONLINE ]", fg=FG_GREEN))
            return

        current_fg = self.status_label.cget("fg")
        next_fg = FG_MAGENTA if current_fg == FG_GREEN else FG_GREEN
        self.status_label.config(fg=next_fg)
        self.after(200, lambda: self.flash_status(count - 1))

# ==============================================================================
# STANDALONE DIAGNOSTIC RUN BLOCK
# ==============================================================================
if __name__ == "__main__":
    # Create diagnostics standalone window frame
    root = tk.Tk()
    root.title("ChaoHub Creative Suite Module - Standalone Diagnostics")
    root.geometry("820x540")
    root.config(bg="#000000")

    # Header label banner
    header = tk.Frame(root, bg=BG_PANEL, highlightthickness=1, highlightbackground=FG_GREEN)
    header.pack(fill="x", padx=10, pady=5)
    tk.Label(header, text="CREATIVE SUITE PROTO PROTOCOL v1.0", fg=FG_GREEN, bg=BG_PANEL, font=("Courier", 12, "bold")).pack(pady=5)

    # Frame container to anchor module
    container = tk.Frame(root, bg="#000000")
    container.pack(fill="both", expand=True, padx=10, pady=5)

    # Initialize Pygame Mixer before loading class for sounds if standalone
    try:
        import pygame
        pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
        # Synthesize temporary clicks for sound effect testing if folder path missing
        sound_dir = os.path.join(os.path.expanduser("~"), "ChaoHub_Data", "sounds")
        if not os.path.exists(sound_dir):
            os.makedirs(sound_dir)
        import wave, struct, math
        click_path = os.path.join(sound_dir, "click.wav")
        if not os.path.exists(click_path):
            with wave.open(click_path, 'wb') as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(22050)
                frames = []
                for i in range(2205):
                    t = i / 22050
                    val = int(15000 * math.sin(2 * math.pi * 1000 * t) * math.exp(-30 * t))
                    frames.append(struct.pack('<h', val))
                wav.writeframes(b''.join(frames))
        beep_path = os.path.join(sound_dir, "beep.wav")
        if not os.path.exists(beep_path):
            with wave.open(beep_path, 'wb') as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(22050)
                frames = []
                for i in range(4410):
                    t = i / 22050
                    val = int(12000 * math.sin(2 * math.pi * 880 * t) * math.exp(-12 * t))
                    frames.append(struct.pack('<h', val))
                wav.writeframes(b''.join(frames))
    except Exception as e:
        print(f"Standalone sound setup warning: {e}")

    # Instantiate CreativeSuiteModule
    suite = CreativeSuiteModule(container)
    suite.pack(fill="both", expand=True)

    root.mainloop()
