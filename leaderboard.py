import os
import json
import time
import random
import threading
import tkinter as tk
from datetime import datetime
from tkinter import messagebox

# ==============================================================================
# LEADERBOARD CONSTANTS & STYLE STRINGS
# ==============================================================================
DATA_DIR = os.path.join(os.path.expanduser("~"), "ChaoHub_Data")
LEADERBOARD_FILE = os.path.join(DATA_DIR, "leaderboard_matrix.json")
LEADERBOARD_LOCK = threading.Lock()

# Re-use color constants matching chaohub.py
BG_DARK = "#000000"
BG_PANEL = "#0b0b0b"
FG_GREEN = "#00ff00"
FG_MAGENTA = "#ff00ff"
FG_CYAN = "#00ffff"
FG_YELLOW = "#ffff00"
ALERT_RED = "#ff0000"

# Sound trigger helper
def trigger_sound(name):
    try:
        from chaohub import play_sound_effect
        play_sound_effect(name)
    except Exception:
        pass

# ==============================================================================
# LORE-ACCURATE FALLBACK GENERATOR
# ==============================================================================
def get_default_leaderboard():
    games = ["PONG GLITCH", "SNAKE PROTOCOL", "DEFUSE FIREWORK", "CYBER BREAK", "NEON RUNNER"]
    data = {}
    
    for game in games:
        data[game] = {}
        for tier in ["1", "2", "3", "4"]:
            entries = []
            if tier == "4":
                # Level 04: dominated by HELLMO_REDUX and GHOST_IN_THE_SHELL at Rank 1 & 2
                names = [
                    "HELLMO_REDUX",
                    "GHOST_IN_THE_SHELL",
                    "NORMAN",
                    "JOSEPH",
                    "ZERO_COOL",
                    "ACID_BURN",
                    "CEREBRAM",
                    "THE_PLAGUE",
                    "KRONOS",
                    "NEO"
                ]
            elif tier == "3":
                names = [
                    "NORMAN",
                    "ACID_BURN",
                    "ZERO_COOL",
                    "JOSEPH",
                    "CEREBRAM",
                    "KRONOS",
                    "THE_PLAGUE",
                    "TRINITY",
                    "CYBER_NINJA",
                    "VECTOR_X"
                ]
            elif tier == "2":
                names = [
                    "NORMAN",
                    "ZERO_COOL",
                    "ACID_BURN",
                    "JOSEPH",
                    "CEREBRAM",
                    "TRINITY",
                    "NEO",
                    "CYBER_NINJA",
                    "VECTOR_X",
                    "HACKER_ANON"
                ]
            else: # tier == "1"
                # Level 01: TURBO_TIMMY at Rank 10 on all games
                names = [
                    "ZERO_COOL",
                    "ACID_BURN",
                    "NORMAN",
                    "JOSEPH",
                    "TRINITY",
                    "NEO",
                    "CYBER_NINJA",
                    "VECTOR_X",
                    "HACKER_ANON",
                    "TURBO_TIMMY"
                ]
                
            for rank_idx, name in enumerate(names):
                rank = rank_idx + 1
                
                # Determine score/time based on game type
                if game == "DEFUSE FIREWORK":
                    # Time metric (ascending: lower is better)
                    if tier == "4":
                        if name == "HELLMO_REDUX":
                            score_val = 112  # Insanely fast for 32x32 / 180 mines
                        elif name == "GHOST_IN_THE_SHELL":
                            score_val = 138
                        elif name == "NORMAN":
                            score_val = 210  # calculated
                        elif name == "JOSEPH":
                            score_val = 345  # moderate
                        else:
                            score_val = 360 + rank * 20
                    elif tier == "3":
                        if name == "NORMAN":
                            score_val = 64
                        elif name == "JOSEPH":
                            score_val = 98
                        else:
                            score_val = 110 + rank * 10
                    elif tier == "2":
                        if name == "NORMAN":
                            score_val = 27
                        elif name == "JOSEPH":
                            score_val = 45
                        else:
                            score_val = 50 + rank * 8
                    else: # tier == "1"
                        if name == "TURBO_TIMMY":
                            score_val = 999  # pathetic worst-place time
                        elif name == "NORMAN":
                            score_val = 6
                        elif name == "JOSEPH":
                            score_val = 15
                        else:
                            score_val = 12 + rank * 5
                else:
                    # Score metric (descending: higher is better)
                    if game == "PONG GLITCH":
                        # Pong plays to 5
                        if tier == "4":
                            if name == "HELLMO_REDUX":
                                score_val = 13375  # Hacked high score
                            elif name == "GHOST_IN_THE_SHELL":
                                score_val = 9005
                            elif name == "NORMAN":
                                score_val = 5
                            elif name == "JOSEPH":
                                score_val = 4
                            else:
                                score_val = max(1, 5 - (rank // 2))
                        elif tier == "3":
                            if name == "NORMAN":
                                score_val = 5
                            elif name == "JOSEPH":
                                score_val = 3
                            else:
                                score_val = max(1, 4 - (rank // 2))
                        elif tier == "2":
                            if name == "NORMAN":
                                score_val = 5
                            elif name == "JOSEPH":
                                score_val = 3
                            else:
                                score_val = max(1, 4 - (rank // 2))
                        else: # tier == "1"
                            if name == "TURBO_TIMMY":
                                score_val = 1  # Pathetic score
                            elif name == "NORMAN":
                                score_val = 5
                            elif name == "JOSEPH":
                                score_val = 3
                            else:
                                score_val = max(1, 4 - (rank // 3))
                    else:
                        # Snake, Cyber Break, Neon Runner
                        mult = 1.0
                        if game == "SNAKE PROTOCOL":
                            mult = 2.0
                        elif game == "CYBER BREAK":
                            mult = 15.0
                        elif game == "NEON RUNNER":
                            mult = 8.0
                            
                        if tier == "4":
                            if name == "HELLMO_REDUX":
                                score_val = int(9999 * mult)
                            elif name == "GHOST_IN_THE_SHELL":
                                score_val = int(8888 * mult)
                            elif name == "NORMAN":
                                score_val = int(4500 * mult)
                            elif name == "JOSEPH":
                                score_val = int(2800 * mult)
                            else:
                                score_val = int((2500 - rank * 150) * mult)
                        elif tier == "3":
                            if name == "NORMAN":
                                score_val = int(3200 * mult)
                            elif name == "JOSEPH":
                                score_val = int(1900 * mult)
                            else:
                                score_val = int((1800 - rank * 100) * mult)
                        elif tier == "2":
                            if name == "NORMAN":
                                score_val = int(1500 * mult)
                            elif name == "JOSEPH":
                                score_val = int(950 * mult)
                            else:
                                score_val = int((900 - rank * 50) * mult)
                        else: # tier == "1"
                            if name == "TURBO_TIMMY":
                                score_val = 1
                            elif name == "NORMAN":
                                score_val = int(500 * mult)
                            elif name == "JOSEPH":
                                score_val = int(350 * mult)
                            else:
                                score_val = int((300 - rank * 20) * mult)
                                
                # Time format
                if name == "JOSEPH":
                    timestamp = "ERROR://TIME_CORRUPT_" + "".join(random.choices("0123456789ABCDEF", k=4))
                else:
                    day = 10 - rank
                    timestamp = f"2026-05-{day:02d} {12+rank:02d}:30:45"
                    
                entries.append({
                    "handle": name,
                    "score": score_val,
                    "timestamp": timestamp
                })
            
            # Final sorting
            if game == "DEFUSE FIREWORK":
                data[game][tier] = sorted(entries, key=lambda x: x["score"])
            else:
                data[game][tier] = sorted(entries, key=lambda x: x["score"], reverse=True)
                
    return data

# ==============================================================================
# FILE READ & WRITE OPERATIONS (THREAD-SAFE & ATOMIC)
# ==============================================================================
def load_leaderboard():
    with LEADERBOARD_LOCK:
        if not os.path.exists(LEADERBOARD_FILE):
            data = get_default_leaderboard()
            try:
                os.makedirs(DATA_DIR, exist_ok=True)
                with open(LEADERBOARD_FILE, "w") as f:
                    json.dump(data, f, indent=4)
            except Exception as e:
                print(f"Error initializing leaderboard file: {e}")
            return data
        
        try:
            with open(LEADERBOARD_FILE, "r") as f:
                data = json.load(f)
                
            # Self-healing validation
            expected_games = ["PONG GLITCH", "SNAKE PROTOCOL", "DEFUSE FIREWORK", "CYBER BREAK", "NEON RUNNER"]
            updated = False
            for game in expected_games:
                if game not in data:
                    data[game] = { "1": [], "2": [], "3": [], "4": [] }
                    updated = True
                else:
                    for tier in ["1", "2", "3", "4"]:
                        if tier not in data[game]:
                            data[game][tier] = []
                            updated = True
            if updated:
                with open(LEADERBOARD_FILE, "w") as f:
                    json.dump(data, f, indent=4)
            return data
        except Exception as e:
            print(f"Error loading leaderboard file: {e}")
            return get_default_leaderboard()

def save_leaderboard(data):
    with LEADERBOARD_LOCK:
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            temp_file = LEADERBOARD_FILE + ".tmp"
            with open(temp_file, "w") as f:
                json.dump(data, f, indent=4)
            os.replace(temp_file, LEADERBOARD_FILE)
        except Exception as e:
            print(f"Error saving leaderboard file: {e}")

# ==============================================================================
# QUALIFICATION CHECKS & SCORE INSERTION
# ==============================================================================
def check_qualification(game_name, difficulty_tier, score):
    data = load_leaderboard()
    tier_str = str(difficulty_tier)
    records = data.get(game_name, {}).get(tier_str, [])
    
    if len(records) < 10:
        return True
        
    if game_name == "DEFUSE FIREWORK":
        # Ascending order: lower time is better. Qualifies if lower than the worst (max) in top 10.
        records_sorted = sorted(records, key=lambda x: x["score"])
        return score < records_sorted[-1]["score"]
    else:
        # Descending order: higher score is better. Qualifies if higher than the worst (min) in top 10.
        records_sorted = sorted(records, key=lambda x: x["score"], reverse=True)
        return score > records_sorted[-1]["score"]

def add_leaderboard_entry(game_name, difficulty_tier, score, handle):
    data = load_leaderboard()
    tier_str = str(difficulty_tier)
    if game_name not in data:
        data[game_name] = { "1": [], "2": [], "3": [], "4": [] }
    if tier_str not in data[game_name]:
        data[game_name][tier_str] = []
        
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_entry = {
        "handle": handle.upper(),
        "score": score,
        "timestamp": timestamp
    }
    data[game_name][tier_str].append(new_entry)
    
    # Sort
    if game_name == "DEFUSE FIREWORK":
        data[game_name][tier_str] = sorted(data[game_name][tier_str], key=lambda x: x["score"])
    else:
        data[game_name][tier_str] = sorted(data[game_name][tier_str], key=lambda x: x["score"], reverse=True)
        
    # Truncate
    data[game_name][tier_str] = data[game_name][tier_str][:10]
    
    # Save atomically
    save_leaderboard(data)

def check_and_intercept_score(parent_widget, game_name, difficulty_tier, score, post_submit_callback=None):
    """
    Evaluates if score/time qualifies for the top 10.
    If so, blocks execution and triggers the Custom Name Input Interceptor Modal.
    Once submitted, writes to database and invokes post_submit_callback.
    """
    # Telemetry: check high scorer achievement points thresholds
    try:
        app = getattr(parent_widget.winfo_toplevel(), "app_instance", None)
        if app:
            # Grant if Snake score >= 50, Pong score >= 5, or Minesweeper victory (time > 0)
            if (game_name == "SNAKE PROTOCOL" and score >= 50) or \
               (game_name == "PONG GLITCH" and score >= 5) or \
               (game_name == "DEFUSE FIREWORK" and score > 0):
                app.achievement_manager.grant_achievement("high_scorer")
    except Exception:
        pass

    if check_qualification(game_name, difficulty_tier, score):
        def submit_callback(handle):
            add_leaderboard_entry(game_name, difficulty_tier, score, handle)
            if post_submit_callback:
                post_submit_callback()
                
        # Locate application root safely
        root_win = parent_widget.winfo_toplevel()
        CustomNameInputPopup(root_win, game_name, difficulty_tier, score, submit_callback)
    else:
        if post_submit_callback:
            post_submit_callback()

# ==============================================================================
# CUSTOM NAME INPUT INTERCEPTOR POPUP (MODAL DIALOG)
# ==============================================================================
class CustomNameInputPopup(tk.Toplevel):
    def __init__(self, root_win, game_name, difficulty_tier, score, submit_callback):
        super().__init__(root_win, bg="#000000")
        self.game_name = game_name
        self.difficulty_tier = difficulty_tier
        self.score = score
        self.submit_callback = submit_callback
        
        self.title("HIGH SCORE DETECTED")
        self.geometry("500x260")
        self.resizable(False, False)
        
        # Enforce strict modality to lock the main game frame inputs
        self.transient(root_win)
        self.grab_set()
        
        # Position popup directly in the center of the root app window
        root_x = root_win.winfo_x()
        root_y = root_win.winfo_y()
        root_w = root_win.winfo_width()
        root_h = root_win.winfo_height()
        pos_x = root_x + (root_w // 2) - 250
        pos_y = root_y + (root_h // 2) - 130
        self.geometry(f"+{pos_x}+{pos_y}")
        
        border_color = ALERT_RED if difficulty_tier == 4 else FG_CYAN
        self.config(highlightbackground=border_color, highlightthickness=3, bd=0)
        
        # Intercept window close event to ensure entry gets committed
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Metadata Flashing Headers
        self.header_lbl = tk.Label(
            self, text="[NEW HIGH SCORE DETECTED IN MATRIX]", 
            fg=border_color, bg="#000000", font=("Courier", 12, "bold")
        )
        self.header_lbl.pack(pady=(25, 5))
        
        node_text = f"[NODE: {self.game_name} // TIER: LEVEL 0{self.difficulty_tier}]"
        self.node_lbl = tk.Label(
            self, text=node_text, 
            fg=FG_GREEN, bg="#000000", font=("Courier", 10, "bold")
        )
        self.node_lbl.pack(pady=5)
        
        # Score Value Display
        score_text = f"SCORE RECORD: {self.score}"
        if self.game_name == "DEFUSE FIREWORK":
            score_text = f"TIME ELAPSED: {self.score} SECONDS"
        self.score_lbl = tk.Label(
            self, text=score_text, 
            fg=FG_YELLOW, bg="#000000", font=("Courier", 11, "bold")
        )
        self.score_lbl.pack(pady=5)
        
        # Character constraint wrapper
        self.entry_var = tk.StringVar()
        self.entry_var.trace_add("write", self.validate_input)
        
        self.entry = tk.Entry(
            self, textvariable=self.entry_var, bg="#0b0b0b", fg=FG_GREEN, 
            insertbackground=FG_GREEN, font=("Courier", 14, "bold"), justify="center",
            bd=2, highlightthickness=1, highlightbackground="#222222", highlightcolor=border_color, width=15
        )
        self.entry.pack(pady=15)
        self.entry.focus_set()
        
        # Commit Button
        self.btn = tk.Button(
            self, text="[ TRANSMIT DATA CORE KEY ]", command=self.commit_entry,
            bg="#000000", fg=border_color, activebackground=border_color, activeforeground="#000000",
            font=("Courier", 10, "bold"), bd=1, highlightthickness=1, highlightbackground=border_color, padx=10, pady=5
        )
        self.btn.pack(pady=5)
        
        # Keybind
        self.entry.bind("<Return>", lambda e: self.commit_entry())
        
        # Start Header Flashing
        self.flash_state = True
        self.flash_loop()
        
    def validate_input(self, *args):
        val = self.entry_var.get().upper()
        # Enforce maximum of 12 uppercase monospaced alphanumeric characters
        filtered = "".join([c for c in val if c.isalnum()])[:12]
        if val != filtered:
            self.entry_var.set(filtered)
            
    def flash_loop(self):
        try:
            if not self.winfo_exists():
                return
            self.flash_state = not self.flash_state
            border_color = ALERT_RED if self.difficulty_tier == 4 else FG_CYAN
            col = "#ffffff" if self.flash_state else border_color
            self.header_lbl.config(fg=col)
            self.after(350, self.flash_loop)
        except Exception:
            pass
            
    def commit_entry(self):
        handle = self.entry_var.get().strip().upper()
        if not handle:
            trigger_sound("explosion")
            return
        
        trigger_sound("click")
        self.grab_release()
        self.destroy()
        self.submit_callback(handle)
        
    def on_close(self):
        # Force default entry to keep matrix integrity if closed
        self.grab_release()
        self.destroy()
        self.submit_callback("HACKER_ANON")

# ==============================================================================
# TWO-TIERED NESTED TAB VIEWPORT PANEL
# ==============================================================================
class LeaderboardModule(tk.Frame):
    def __init__(self, parent, glitch_manager=None):
        super().__init__(parent, bg=BG_DARK)
        self.glitch_manager = glitch_manager
        
        # Global selection state
        self.active_game = "PONG GLITCH"
        self.active_difficulty = 2 # Default: LEVEL 02: DON'T HURT ME.
        
        self.config(highlightbackground=FG_CYAN, highlightthickness=1)
        
        # 1. Primary Navigation Selector Panel (Game Selector Horizontal Row)
        self.game_selector_frame = tk.Frame(self, bg=BG_PANEL, bd=1, relief="solid")
        self.game_selector_frame.pack(fill="x", side="top", pady=(5, 5), padx=5)
        
        self.game_buttons = {}
        games_list = ["PONG GLITCH", "SNAKE PROTOCOL", "DEFUSE FIREWORK", "CYBER BREAK", "NEON RUNNER"]
        for g_name in games_list:
            btn = tk.Button(
                self.game_selector_frame, text=f"[ {g_name} ]", 
                command=lambda name=g_name: self.set_active_game(name),
                bg=BG_DARK, fg=FG_GREEN, activebackground=FG_GREEN, activeforeground=BG_DARK,
                font=("Courier", 9, "bold"), bd=0, relief="flat", highlightthickness=0, padx=5, pady=6
            )
            btn.pack(side="left", expand=True, fill="x", padx=2, pady=2)
            self.game_buttons[g_name] = btn
            
        # 2. Secondary Navigation Selector Panel (Difficulty Selector Horizontal Tabs)
        self.diff_tabs_frame = tk.Frame(self, bg=BG_DARK)
        self.diff_tabs_frame.pack(fill="x", side="top", pady=2, padx=5)
        
        self.diff_tabs = {}
        difficulty_labels = {
            1: "[ CAN I PLAY DADDY? ]",
            2: "[ DON'T HURT ME. ]",
            3: "[ BRING 'EM ON! ]",
            4: "[ CRIMSON MODE ]"
        }
        
        for d_tier, d_lbl in difficulty_labels.items():
            btn = tk.Button(
                self.diff_tabs_frame, text=d_lbl,
                command=lambda tier=d_tier: self.set_active_difficulty(tier),
                bg=BG_DARK, fg=FG_CYAN, activebackground=FG_CYAN, activeforeground=BG_DARK,
                font=("Courier", 8, "bold"), bd=1, relief="solid", highlightthickness=0, padx=4, pady=4
            )
            btn.pack(side="left", expand=True, fill="x", padx=3)
            self.diff_tabs[d_tier] = btn
            
        # 3. Output Grid Table Header Frame
        self.headers_frame = tk.Frame(self, bg=BG_PANEL)
        self.headers_frame.pack(fill="x", side="top", pady=(10, 2), padx=10)
        
        col_headers = [
            ("RANK", 0.1),
            ("HACKER ALIAS", 0.35),
            ("SCORE RECORD", 0.25),
            ("MATRIX STAMP", 0.3)
        ]
        for name, width_weight in col_headers:
            lbl = tk.Label(
                self.headers_frame, text=name, fg=FG_GREEN, bg=BG_PANEL,
                font=("Courier", 9, "bold"), anchor="w"
            )
            lbl.pack(side="left", expand=True, fill="x", padx=5)
            
        # 4. Viewport Data Frame Container
        self.viewport_frame = tk.Frame(self, bg=BG_DARK, highlightbackground="#333333", highlightthickness=1)
        self.viewport_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Rank 1 flashing state holder
        self.top_rank_labels = []
        self.flash_top = False
        
        # Load and draw active view
        self.refresh_leaderboard_view()
        self.run_rank_flash_loop()
        
    def set_active_game(self, game_name):
        trigger_sound("click")
        self.active_game = game_name
        self.refresh_leaderboard_view()
        
    def set_active_difficulty(self, tier):
        trigger_sound("click")
        self.active_difficulty = tier
        
        # Special alert sound if switching to Crimson Mode (Level 4)
        if tier == 4:
            trigger_sound("alarm")
            if self.glitch_manager:
                self.glitch_manager.trigger_throttled_global_glitch(duration=200, magnitude=0.5, min_interval=1.0)
                
        self.refresh_leaderboard_view()
        
    def refresh_leaderboard_view(self):
        # Update Game selector buttons
        for name, btn in self.game_buttons.items():
            if name == self.active_game:
                btn.config(fg="#000000", bg=FG_GREEN)
            else:
                btn.config(fg=FG_GREEN, bg=BG_DARK)
                
        # Update Difficulty Selector Tabs
        # If CRIMSON MODE (Level 4) is active: style border and text in violent laser crimson (#ff0000)
        is_crimson = (self.active_difficulty == 4)
        tab_border_col = ALERT_RED if is_crimson else "#222222"
        tab_active_col = ALERT_RED if is_crimson else FG_CYAN
        
        self.config(highlightbackground=tab_active_col)
        self.headers_frame.config(bg=BG_PANEL)
        
        for tier, btn in self.diff_tabs.items():
            if tier == self.active_difficulty:
                # Active tab
                btn.config(
                    bg=tab_active_col, fg="#000000", 
                    activebackground=tab_active_col, activeforeground="#000000",
                    highlightbackground=tab_active_col
                )
            else:
                # Inactive tabs
                inactive_text_col = ALERT_RED if (tier == 4) else FG_CYAN
                btn.config(
                    bg=BG_DARK, fg=inactive_text_col,
                    activebackground=tab_active_col, activeforeground=BG_DARK,
                    highlightbackground=tab_border_col
                )
                
        # Clean current rows in viewport frame
        for widget in self.viewport_frame.winfo_children():
            widget.destroy()
            
        self.top_rank_labels.clear()
        
        # Load and render entries from the JSON store
        db = load_leaderboard()
        records = db.get(self.active_game, {}).get(str(self.active_difficulty), [])
        
        # Ensure list is padded to exactly 10 slots with fallback records if necessary
        # (Though load_leaderboard guarantees data exists, we have local safety logic)
        while len(records) < 10:
            records.append({"handle": "EMPTY_SLOT", "score": 0, "timestamp": "---"})
            
        # Draw the 10 rows
        for idx, item in enumerate(records):
            rank_str = f"{idx+1:02d}"
            handle = item.get("handle", "EMPTY_SLOT")
            score_raw = item.get("score", 0)
            timestamp = item.get("timestamp", "---")
            
            # Formatted score record string
            if self.active_game == "DEFUSE FIREWORK":
                score_str = f"{score_raw}s" if score_raw > 0 else "---"
            elif self.active_game == "PONG GLITCH":
                score_str = f"{score_raw} PTS" if score_raw > 0 else "---"
            else:
                score_str = f"{score_raw:05d}" if score_raw > 0 else "---"
                
            # Row Container
            # Alternating rows must shift between a dark grey and dark purple gradient background
            row_bg = "#111111" if (idx % 2 == 0) else "#1a052e"
            
            row_frame = tk.Frame(self.viewport_frame, bg=row_bg, height=22)
            row_frame.pack(fill="x", side="top", pady=1, padx=2)
            row_frame.pack_propagate(False) # lock height
            
            # Setup columns widths
            col_specs = [
                (rank_str, 0.12, "center"),
                (handle, 0.38, "w"),
                (score_str, 0.22, "w"),
                (timestamp, 0.28, "w")
            ]
            
            # Highlight logic for Rank 01
            # Rank 01 must highlight/flash in gold (#ffff00) or magenta (FG_MAGENTA)
            if idx == 0:
                fg_col = FG_YELLOW
            else:
                fg_col = ALERT_RED if is_crimson else FG_GREEN
                
            for text_val, width_weight, alignment in col_specs:
                lbl = tk.Label(
                    row_frame, text=text_val, fg=fg_col, bg=row_bg,
                    font=("Courier", 9, "bold" if idx == 0 else "normal"), anchor=alignment
                )
                lbl.pack(side="left", expand=True, fill="both", padx=5)
                
                # Keep reference to Rank 01 labels for flashing loop
                if idx == 0:
                    self.top_rank_labels.append(lbl)
                    
    def run_rank_flash_loop(self):
        try:
            if not self.winfo_exists():
                return
            self.flash_top = not self.flash_top
            # Flash color alternates between gold and magenta
            flash_col = FG_MAGENTA if self.flash_top else FG_YELLOW
            for lbl in self.top_rank_labels:
                if lbl.winfo_exists():
                    lbl.config(fg=flash_col)
            self.after(500, self.run_rank_flash_loop)
        except Exception:
            pass
