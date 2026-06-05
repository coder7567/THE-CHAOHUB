import os
import json
import math
import time
import random
import threading
import tkinter as tk

# Standard Colors from chaohub.py
BG_DARK = "#000000"
BG_PANEL = "#0b0b0b"
FG_GREEN = "#00ff00"
FG_MAGENTA = "#ff00ff"
FG_CYAN = "#00ffff"
FG_YELLOW = "#ffff00"
ALERT_RED = "#ff0000"

# Category-specific neon border colors for Trophy cards
CATEGORY_COLORS = {
    "ARCHIVE CONTRABAND": FG_MAGENTA,      # Books Module
    "SONIC PLUNDERER": FG_CYAN,           # Music Module
    "SHORTWAVE RADIO": FG_YELLOW,          # Podcasts/Streams Module
    "DISTRACTION WIDGETS": FG_GREEN,       # Utilities Module
    "ARCADE CORE": ALERT_RED,             # Games Module
    "CREATIVE SUITE": "#ff8000",           # Pixel Art Module (Orange/Amber)
    "TERMINAL SHELL": "#ffffff",           # CLI Module (Silver/White)
    "IRC CHAT ROOM & P2P MESH": "#a000ff", # Networking Modules (Purple)
    "GREEN MATRIX": "#00ff88"              # Custom Plugin Mod (Teal/Mint)
}

ACHIEVEMENTS_DB = {
    "bookworm": {
        "id": "bookworm",
        "name": "Bookworm",
        "description": "Read or load your first contraband text archive.",
        "category": "ARCHIVE CONTRABAND",
        "xp_value": 100,
    },
    "deep_research": {
        "id": "deep_research",
        "name": "Deep Research",
        "description": "Spend a total of 15 aggregate minutes interacting with the text engine.",
        "category": "ARCHIVE CONTRABAND",
        "xp_value": 250,
    },
    "audiophile": {
        "id": "audiophile",
        "name": "Audiophile",
        "description": "Play 10 different target audio files.",
        "category": "SONIC PLUNDERER",
        "xp_value": 150,
    },
    "continuous_stream": {
        "id": "continuous_stream",
        "name": "Continuous Stream",
        "description": "Keep the audio stream active uninterrupted for over 30 minutes.",
        "category": "SONIC PLUNDERER",
        "xp_value": 300,
    },
    "static_surfer": {
        "id": "static_surfer",
        "name": "Static Surfer",
        "description": "Fetch new RSS/stream node feeds 5 times.",
        "category": "SHORTWAVE RADIO",
        "xp_value": 100,
    },
    "focus_master": {
        "id": "focus_master",
        "name": "Focus Master",
        "description": "Complete a full Pomodoro timer session without resetting.",
        "category": "DISTRACTION WIDGETS",
        "xp_value": 200,
    },
    "high_scorer": {
        "id": "high_scorer",
        "name": "High Scorer",
        "description": "Reach a specified point threshold or play 5 distinct sessions.",
        "category": "ARCADE CORE",
        "xp_value": 200,
    },
    "master_artisan": {
        "id": "master_artisan",
        "name": "Master Artisan",
        "description": "Click the 'Export' asset button to save a custom artwork layout.",
        "category": "CREATIVE SUITE",
        "xp_value": 150,
    },
    "power_user": {
        "id": "power_user",
        "name": "Power User",
        "description": "Execute 20 commands successfully inside the input field environment.",
        "category": "TERMINAL SHELL",
        "xp_value": 150,
    },
    "grid_link": {
        "id": "grid_link",
        "name": "Grid Link",
        "description": "Detect at least 1 alternative local mesh P2P network node (peer_count > 0).",
        "category": "IRC CHAT ROOM & P2P MESH",
        "xp_value": 200,
    },
    "chatterbox": {
        "id": "chatterbox",
        "name": "Chatterbox",
        "description": "Send 10 messages across the local IRC system interface.",
        "category": "IRC CHAT ROOM & P2P MESH",
        "xp_value": 150,
    },
    "matrix_welcome": {
        "id": "matrix_welcome",
        "name": "Welcome to the Real World",
        "description": "Run the dynamic matrix plugin and switch its color mode away from default 'GREEN' for the first time.",
        "category": "GREEN MATRIX",
        "xp_value": 100,
    },
    "system_breach": {
        "id": "system_breach",
        "name": "System Breach",
        "description": "Have the Green Matrix tab open actively while a global exploit flash event (Ctrl+Shift+G) is triggered via the GlitchManager.",
        "category": "GREEN MATRIX",
        "xp_value": 250,
    }
}

def play_sound_effect(name):
    """Safely queues sound playback via Pygame mixer."""
    try:
        from chaohub import play_sound_effect as ch_play
        ch_play(name)
    except Exception:
        pass

# ==============================================================================
# 1. NON-BLOCKING TOAST NOTIFICATIONS
# ==============================================================================
class AchievementToast(tk.Frame):
    """
    Cyberspace alert toast that slides onto the screen and dismisses itself
    after standard incubation duration.
    """
    def __init__(self, root, title, xp_value):
        super().__init__(root, bg=BG_DARK, highlightbackground=FG_GREEN, highlightthickness=2)
        self.root = root
        
        lbl_header = tk.Label(self, text="⚡ TROPHY DELIVERED ⚡", fg=FG_MAGENTA, bg=BG_DARK, font=("Courier", 9, "bold"))
        lbl_header.pack(padx=20, pady=(6, 2))
        
        lbl_title = tk.Label(self, text=title.upper(), fg=FG_GREEN, bg=BG_DARK, font=("Courier", 11, "bold"))
        lbl_title.pack(padx=20, pady=2)
        
        lbl_xp = tk.Label(self, text=f"+{xp_value} XP INDEXED", fg=FG_YELLOW, bg=BG_DARK, font=("Courier", 9, "bold"))
        lbl_xp.pack(padx=20, pady=(2, 6))
        
        # Position at top right
        self.y_pos = -120
        self.place(relx=0.98, x=0, y=self.y_pos, anchor="ne")
        self.slide_in()
        
    def slide_in(self):
        if not self.winfo_exists():
            return
        if self.y_pos < 25:
            self.y_pos += 6
            self.place_configure(y=self.y_pos)
            self.after(16, self.slide_in)
        else:
            self.after(3500, self.slide_out)
            
    def slide_out(self):
        if not self.winfo_exists():
            return
        if self.y_pos > -120:
            self.y_pos -= 6
            self.place_configure(y=self.y_pos)
            self.after(16, self.slide_out)
        else:
            self.destroy()

class LevelUpToast(tk.Frame):
    """
    Aggressive warning toast overlay that flashes Level-Up actions to screen center.
    """
    def __init__(self, root, new_level):
        super().__init__(root, bg=BG_DARK, highlightbackground=FG_YELLOW, highlightthickness=2)
        self.root = root
        
        lbl_header = tk.Label(self, text="☣ COGNITIVE RATING ELEVATION ☣", fg=ALERT_RED, bg=BG_DARK, font=("Courier", 12, "bold"))
        lbl_header.pack(padx=30, pady=(10, 2))
        
        lbl_level = tk.Label(self, text=f"SYSTEM LEVEL {new_level:02d} DETECTED", fg=FG_YELLOW, bg=BG_DARK, font=("Courier", 18, "bold"))
        lbl_level.pack(padx=30, pady=4)
        
        lbl_detail = tk.Label(self, text="CORE PROCESSING CAPABILITY ENHANCED", fg=FG_CYAN, bg=BG_DARK, font=("Courier", 9, "bold"))
        lbl_detail.pack(padx=30, pady=(2, 10))
        
        # Stagger placement center-top
        self.y_pos = -150
        self.place(relx=0.5, y=self.y_pos, anchor="n")
        self.slide_in()
        
    def slide_in(self):
        if not self.winfo_exists():
            return
        if self.y_pos < 60:
            self.y_pos += 8
            self.place_configure(y=self.y_pos)
            self.after(16, self.slide_in)
        else:
            self.after(4000, self.slide_out)
            
    def slide_out(self):
        if not self.winfo_exists():
            return
        if self.y_pos > -150:
            self.y_pos -= 8
            self.place_configure(y=self.y_pos)
            self.after(16, self.slide_out)
        else:
            self.destroy()

# ==============================================================================
# 2. THE CENTRALIZED THREAD-SAFE ACHIEVEMENT MANAGER (SINGLETON)
# ==============================================================================
class AchievementManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(AchievementManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, root=None):
        if self._initialized:
            # Re-hook root if updated (e.g. on application rebuild)
            if root is not None:
                self.root = root
            return
            
        self.root = root
        self.lock = threading.Lock()
        
        # Persistence setup target "~/ChaoHub_Data/system/achievements.json"
        self.data_dir = os.path.join(os.path.expanduser("~"), "ChaoHub_Data", "system")
        self.file_path = os.path.join(self.data_dir, "achievements.json")
        
        # Self-healing baseline memory footprint layout
        self.state = {
            "unlocked_achievements": {}, # id -> unlock_timestamp
            "stats": {
                "books_time_seconds": 0,
                "audio_files_played": [],
                "rss_fetch_count": 0,
                "pomodoro_sessions_completed": 0,
                "games_played": 0,
                "games_distinct": [],
                "pixel_art_exports": 0,
                "terminal_commands_count": 0,
                "irc_messages_sent": 0,
                "matrix_color_switched": False,
                "matrix_glitched": False
            }
        }
        
        self.load_state()
        self._initialized = True

    def load_state(self):
        """Atomically loads current file configs or initializes baseline file."""
        with self.lock:
            if not os.path.exists(self.data_dir):
                try:
                    os.makedirs(self.data_dir, exist_ok=True)
                except Exception as e:
                    print(f"[AchievementManager] Exception writing folder tree: {e}")
                    
            if os.path.exists(self.file_path):
                try:
                    with open(self.file_path, "r") as f:
                        loaded = json.load(f)
                        if "unlocked_achievements" in loaded:
                            self.state["unlocked_achievements"] = loaded["unlocked_achievements"]
                        if "stats" in loaded:
                            # Safely merge statistics keeping defaults intact
                            for k, v in loaded["stats"].items():
                                self.state["stats"][k] = v
                except Exception as e:
                    print(f"[AchievementManager] Error reading file: {e}. Rewriting baseline.")
                    self.save_state_unlocked()
            else:
                self.save_state_unlocked()

    def save_state_unlocked(self):
        """Internal worker method writing database state without lock locks."""
        try:
            temp_file = self.file_path + ".tmp"
            with open(temp_file, "w") as f:
                json.dump(self.state, f, indent=4)
            os.replace(temp_file, self.file_path)
        except Exception as e:
            print(f"[AchievementManager] File I/O exception writing state: {e}")

    def save_state(self):
        """Public thread-safe database synchronization checkpoint."""
        with self.lock:
            self.save_state_unlocked()

    def get_metric(self, name):
        """Getter for core analytics metrics."""
        with self.lock:
            return self.state["stats"].get(name)

    def set_metric(self, name, value):
        """Setter for core analytics metrics."""
        with self.lock:
            self.state["stats"][name] = value
            self.save_state_unlocked()

    def increment_metric(self, name, amount=1):
        """Appends metrics totals safely."""
        with self.lock:
            val = self.state["stats"].get(name, 0)
            self.state["stats"][name] = val + amount
            self.save_state_unlocked()

    def add_unique_metric(self, name, item):
        """Tracks list items uniquely."""
        with self.lock:
            val = self.state["stats"].get(name)
            if not isinstance(val, list):
                val = []
            if item not in val:
                val.append(item)
                self.state["stats"][name] = val
                self.save_state_unlocked()

    def get_xp_and_level(self):
        """Computes cumulative XP and level using quadratic progression curves."""
        with self.lock:
            xp = 0
            for aid in self.state["unlocked_achievements"]:
                if aid in ACHIEVEMENTS_DB:
                    xp += ACHIEVEMENTS_DB[aid]["xp_value"]
            # Level N requires 100 * (N-1)**2.
            level = int(math.sqrt(xp / 100)) + 1
            return xp, level

    def grant_achievement(self, achievement_id):
        """Hooks achievements, checks lock limits, updates levels, queues toasts."""
        if achievement_id not in ACHIEVEMENTS_DB:
            return False
            
        old_xp, old_level = self.get_xp_and_level()
        unlocked = False
        
        with self.lock:
            if achievement_id not in self.state["unlocked_achievements"]:
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                self.state["unlocked_achievements"][achievement_id] = timestamp
                self.save_state_unlocked()
                unlocked = True
                
        if unlocked:
            new_xp, new_level = self.get_xp_and_level()
            ach_info = ACHIEVEMENTS_DB[achievement_id]
            
            # Dispatch to main Tkinter loop for visual overlay notifications
            if self.root:
                try:
                    self.root.after(0, lambda: AchievementToast(self.root, ach_info["name"], ach_info["xp_value"]))
                    if new_level > old_level:
                        self.root.after(850, lambda: LevelUpToast(self.root, new_level))
                except Exception as e:
                    print(f"[AchievementManager] Failed to dispatch notifications: {e}")
            return True
        return False

# ==============================================================================
# 3. TROPHY VIEWPORT LAYOUT & COMPONENT LAYERS
# ==============================================================================
class ScrollableFrame(tk.Frame):
    """
    Standard scrollable canvas container helper.
    Isolates mousewheel hook bindings defensively.
    """
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.canvas = tk.Canvas(self, bg=BG_DARK, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=BG_DARK)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.bind('<Configure>', lambda event: self.canvas.itemconfig(self.canvas_window, width=event.width))
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Bind scrolling to cursor presence
        self.canvas.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>", self._on_mousewheel))
        self.canvas.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))
        
    def _on_mousewheel(self, event):
        if self.canvas.winfo_exists():
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

class AchievementsModule(tk.Frame):
    """
    The main Trophy Room viewport tab.
    Displays Level metrics, XP progress bars, and scrollable rosters.
    """
    def __init__(self, parent):
        super().__init__(parent, bg=BG_DARK)
        self.config(highlightbackground=FG_MAGENTA, highlightthickness=1)
        
        self.app = self.winfo_toplevel().app_instance
        self.manager = self.app.achievement_manager
        
        # Re-verify manager mapping
        if self.manager.root is None:
            self.manager.root = self.winfo_toplevel()
            
        self.build_ui()

    def build_ui(self):
        # 1. Top Dashboard Header Panel
        self.dashboard = tk.Frame(self, bg=BG_PANEL, highlightthickness=1, highlightbackground=FG_CYAN)
        self.dashboard.pack(fill="x", padx=10, pady=10)
        
        # Grid splits dashboard into Level section and Progress metrics
        self.dashboard.columnconfigure(0, weight=1)
        self.dashboard.columnconfigure(1, weight=1)
        
        xp, level = self.manager.get_xp_and_level()
        
        # Level thresholds
        current_threshold = 100 * (level - 1)**2
        next_threshold = 100 * level**2
        xp_needed = next_threshold - current_threshold
        xp_earned = xp - current_threshold
        
        # Left Panel (Level Status Node)
        self.left_panel = tk.Frame(self.dashboard, bg=BG_PANEL)
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=15, pady=10)
        
        tk.Label(self.left_panel, text="SYSTEM COGNITIVE LEVEL", fg=FG_CYAN, bg=BG_PANEL, font=("Courier", 10, "bold")).pack(anchor="w")
        
        lvl_frame = tk.Frame(self.left_panel, bg=BG_PANEL)
        lvl_frame.pack(anchor="w", pady=5)
        
        tk.Label(lvl_frame, text="LVL", fg=FG_YELLOW, bg=BG_PANEL, font=("Courier", 14, "bold")).pack(side="left", anchor="sw", pady=(0, 4))
        self.lbl_level_val = tk.Label(lvl_frame, text=f"{level:02d}", fg=FG_YELLOW, bg=BG_PANEL, font=("Courier", 38, "bold"))
        self.lbl_level_val.pack(side="left", padx=5)
        
        # Progression Bar Canvas (Level progression)
        self.bar_canvas = tk.Canvas(self.left_panel, height=20, bg=BG_DARK, highlightthickness=1, highlightbackground=FG_GREEN)
        self.bar_canvas.pack(fill="x", pady=5)
        
        self.lbl_xp_metrics = tk.Label(self.left_panel, text=f"{xp} / {next_threshold} XP (Level Progress: {xp_earned}/{xp_needed} XP)", fg=FG_GREEN, bg=BG_PANEL, font=("Courier", 8, "bold"))
        self.lbl_xp_metrics.pack(anchor="w")
        
        # Right Panel (Macro Game Completion)
        self.right_panel = tk.Frame(self.dashboard, bg=BG_PANEL)
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=15, pady=10)
        
        tk.Label(self.right_panel, text="ABSOLUTE ENCLAVE COMPLETION", fg=FG_MAGENTA, bg=BG_PANEL, font=("Courier", 10, "bold")).pack(anchor="w")
        
        # Determine stats
        total_trophies = len(ACHIEVEMENTS_DB)
        unlocked_count = len(self.manager.state["unlocked_achievements"])
        comp_percentage = int((unlocked_count / total_trophies) * 100) if total_trophies > 0 else 0
        
        comp_lbl_frame = tk.Frame(self.right_panel, bg=BG_PANEL)
        comp_lbl_frame.pack(anchor="w", pady=5)
        
        self.lbl_completion_val = tk.Label(comp_lbl_frame, text=f"{comp_percentage}%", fg=FG_CYAN, bg=BG_PANEL, font=("Courier", 38, "bold"))
        self.lbl_completion_val.pack(side="left")
        
        # Macro Completion Canvas
        self.comp_canvas = tk.Canvas(self.right_panel, height=20, bg=BG_DARK, highlightthickness=1, highlightbackground=FG_MAGENTA)
        self.comp_canvas.pack(fill="x", pady=5)
        
        self.lbl_trophy_stats = tk.Label(self.right_panel, text=f"Unlocked Trophies: {unlocked_count} / {total_trophies}", fg=FG_YELLOW, bg=BG_PANEL, font=("Courier", 8, "bold"))
        self.lbl_trophy_stats.pack(anchor="w")
        
        # Register dashboard widgets to glitch manager temporal ticks
        self.app.glitch_manager.register_widget(self.dashboard, hover=False, click=False, temporal=True, magnitude=0.08)
        self.app.glitch_manager.register_widget(self.lbl_level_val, hover=True, click=True, temporal=True, magnitude=0.2)
        self.app.glitch_manager.register_widget(self.lbl_completion_val, hover=True, click=True, temporal=True, magnitude=0.2)
        
        # Handle Canvas Resize Configuration binds to draw the fills accurately
        self.bar_canvas.bind("<Configure>", lambda e: self.draw_level_bar(xp_earned, xp_needed))
        self.comp_canvas.bind("<Configure>", lambda e: self.draw_completion_bar(unlocked_count, total_trophies))
        
        # 2. ScrollableBadge Roster Frame
        roster_label = tk.Label(self, text="⚡ SYSTEM DATA CORE RECORD CHANNELS ⚡", fg=FG_GREEN, bg=BG_DARK, font=("Courier", 11, "bold"))
        roster_label.pack(anchor="w", padx=15, pady=(10, 5))
        self.app.glitch_manager.register_widget(roster_label, hover=True, click=True, temporal=True, magnitude=0.15)
        
        self.scroll_frame = ScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.populate_badges()

    def draw_level_bar(self, current, needed):
        self.bar_canvas.delete("all")
        width = self.bar_canvas.winfo_width()
        height = self.bar_canvas.winfo_height()
        if width <= 1:
            return
            
        ratio = current / needed if needed > 0 else 0.0
        fill_width = int(ratio * (width - 6))
        
        # Draw segmented retro progress bar blocks
        block_w = 8
        spacing = 3
        blocks_count = fill_width // (block_w + spacing)
        
        for i in range(blocks_count):
            x1 = 3 + i * (block_w + spacing)
            y1 = 3
            x2 = x1 + block_w
            y2 = height - 3
            self.bar_canvas.create_rectangle(x1, y1, x2, y2, fill=FG_GREEN, outline="")

    def draw_completion_bar(self, unlocked, total):
        self.comp_canvas.delete("all")
        width = self.comp_canvas.winfo_width()
        height = self.comp_canvas.winfo_height()
        if width <= 1:
            return
            
        ratio = unlocked / total if total > 0 else 0.0
        fill_width = int(ratio * (width - 6))
        
        block_w = 8
        spacing = 3
        blocks_count = fill_width // (block_w + spacing)
        
        for i in range(blocks_count):
            x1 = 3 + i * (block_w + spacing)
            y1 = 3
            x2 = x1 + block_w
            y2 = height - 3
            self.comp_canvas.create_rectangle(x1, y1, x2, y2, fill=FG_CYAN, outline="")

    def populate_badges(self):
        """Loops achievement database and draws dynamic badge cards to the scroll frame."""
        for widget in self.scroll_frame.scrollable_frame.winfo_children():
            widget.destroy()
            
        unlocked_state = self.manager.state["unlocked_achievements"]
        
        # Sort achievements list (unlocked first, then sorted by category)
        sorted_keys = sorted(
            ACHIEVEMENTS_DB.keys(),
            key=lambda k: (k not in unlocked_state, ACHIEVEMENTS_DB[k]["category"], ACHIEVEMENTS_DB[k]["name"])
        )
        
        for key in sorted_keys:
            ach = ACHIEVEMENTS_DB[key]
            is_unlocked = key in unlocked_state
            unlock_time = unlocked_state.get(key)
            
            # Card Container
            # Neon border category style matching target modifications
            border_color = CATEGORY_COLORS.get(ach["category"], "#ffffff") if is_unlocked else "#222222"
            
            card = tk.Frame(self.scroll_frame.scrollable_frame, bg="#000000",
                            highlightbackground=border_color, highlightthickness=1)
            card.pack(fill="x", padx=10, pady=5, ipady=4)
            
            # Register cards dynamically to glitch events
            # Locked cards glitch less aggressively than unlocked ones
            mag = 0.15 if is_unlocked else 0.05
            self.app.glitch_manager.register_widget(card, hover=True, click=True, temporal=is_unlocked, magnitude=mag)
            
            # Check badge indicator column (Left)
            badge_canvas = tk.Canvas(card, width=40, height=40, bg="#000000", highlightthickness=0)
            badge_canvas.pack(side="left", padx=10)
            
            if is_unlocked:
                # Draw terminal green/cyan check mark check mark
                badge_canvas.create_oval(5, 5, 35, 35, outline=FG_GREEN, width=2)
                # Check vector shape coordinates
                badge_canvas.create_line(12, 20, 18, 26, fill=FG_GREEN, width=2)
                badge_canvas.create_line(18, 26, 28, 14, fill=FG_GREEN, width=2)
            else:
                # Draw dimmed lock pad padlock coordinates
                badge_canvas.create_oval(10, 10, 30, 20, outline="#444444", width=2)
                badge_canvas.create_rectangle(8, 20, 32, 35, fill="#000000", outline="#444444", width=2)
                # keyhole notch
                badge_canvas.create_oval(18, 24, 22, 28, fill="#444444", outline="")
                badge_canvas.create_line(20, 28, 20, 32, fill="#444444", width=2)
                
            # Details block (Center-Left)
            details_frame = tk.Frame(card, bg="#000000")
            details_frame.pack(side="left", fill="both", expand=True, padx=5)
            
            # Header line: name + category tag
            title_text_color = border_color if is_unlocked else "#555555"
            lbl_title = tk.Label(details_frame, text=ach["name"].upper(), fg=title_text_color, bg="#000000", font=("Courier", 11, "bold"))
            lbl_title.pack(anchor="w", pady=(2, 0))
            
            tag_text = f"[{ach['category']} MODULE]"
            lbl_tag = tk.Label(details_frame, text=tag_text, fg="#555555" if not is_unlocked else border_color, bg="#000000", font=("Courier", 8, "bold"))
            lbl_tag.pack(anchor="w")
            
            # Description line
            desc_color = "#888888" if is_unlocked else "#444444"
            lbl_desc = tk.Label(details_frame, text=ach["description"], fg=desc_color, bg="#000000", font=("Courier", 9), justify="left", wrap=500)
            lbl_desc.pack(anchor="w", pady=(3, 2))
            
            # Value/Time block (Right)
            right_frame = tk.Frame(card, bg="#000000")
            right_frame.pack(side="right", padx=15, fill="y")
            
            xp_color = FG_YELLOW if is_unlocked else "#333333"
            lbl_xp = tk.Label(right_frame, text=f"+{ach['xp_value']} XP", fg=xp_color, bg="#000000", font=("Courier", 10, "bold"))
            lbl_xp.pack(anchor="e", pady=(4, 0))
            
            if is_unlocked:
                lbl_time = tk.Label(right_frame, text=f"UNLOCKED:\n{unlock_time}", fg=FG_CYAN, bg="#000000", font=("Courier", 7, "bold"), justify="right")
                lbl_time.pack(anchor="e", pady=(2, 4))
            else:
                lbl_time = tk.Label(right_frame, text="LOCKED", fg="#444444", bg="#000000", font=("Courier", 8, "bold"))
                lbl_time.pack(anchor="e", pady=(5, 4))
