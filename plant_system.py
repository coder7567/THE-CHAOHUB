import tkinter as tk
import json
import os
import random
import time

# ==============================================================================
# PROCEDURAL ASCII ART FRAME DATABASE
# ==============================================================================
ASCII_FRAMES = {
    "SEED": {
        "normal": [
            "\n\n\n           (.)\n          (   )\n          // \\\\\n         //   \\\\\n      ===========",
            "\n\n\n           (o)\n          (   )\n          \\\\ //\n         //   \\\\\n      ==========="
        ],
        "glitched": [
            "\n\n\n           (✇)\n          ░   ░\n          ▰▰ ▰▰\n         ██   ██\n      ===========",
            "\n\n\n           (☣️)\n          █   █\n          ▰▰ ▰▰\n         ░░   ░░\n      ==========="
        ]
    },
    "SPROUT": {
        "normal": [
            "\n\n            \\ /\n           (o.o)\n            | |\n           // \\\\\n          //   \\\\\n      ===========",
            "\n\n            | /\n           (o.-)\n            | |\n           \\\\ //\n          //   \\\\\n      ==========="
        ],
        "glitched": [
            "\n\n            ✇ ░\n           (▰.▰)\n            █ █\n           ▰▰ ▰▰\n          ██   ██\n      ===========",
            "\n\n            ░ ☣️\n           (░.░)\n            █ █\n           ▰▰ ▰▰\n          ░░   ░░\n      ==========="
        ]
    },
    "PROTO-STALK": {
        "normal": [
            "\n          \\  |  /\n           \\-+-/\n             |\n           (o.o)\n           / | \\\n          /  |  \\\n         //  |  \\\\\n      ===========",
            "\n          /  |  \\\n           \\-+-/\n             |\n           (-.o)\n           \\ | /\n          /  |  \\\n         //  |  \\\\\n      ==========="
        ],
        "glitched": [
            "\n          ✇  █  ✇\n           ░-+-░\n             █\n           (▰.▰)\n           ▰ █ ▰\n          /  █  \\\n         ██  █  ██\n      ===========",
            "\n          ☣️  ░  ☣️\n           █-+-█\n             ░\n           (░.░)\n           ▰ ░ ▰\n          /  ░  \\\n         ░░  ░  ░░\n      ==========="
        ]
    },
    "MATURE_MATRIX_ROOT": {
        "normal": [
            "         .-=====-.\n        /  v.100  \\\n       |  [● _ ●]  |\n        \\   ===   /\n         '-=-=-'-'\n           | | |\n         //  |  \\\\\n        //   |   \\\\\n      ===========",
            "         .-=====-.\n        /  v.100  \\\n       |  [○ _ ○]  |\n        \\   ---   /\n         '-=-=-'-'\n           | | |\n         \\\\  |  //\n        //   |   \\\\\n      ==========="
        ],
        "glitched": [
            "         ░-▰▰▰▰▰-░\n        /  v.☣️☣️  \\\n       ░  [✇ _ ✇]  ░\n        \\\\   ▰▰▰   /\n         '-▰-▰-'-░\n           █ █ █\n         ▰▰  █  ▰▰\n        ██   █   ██\n      ===========",
            "         █-░░░░░-█\n        /  v.✇✇  \\\n       █  [☣️ _ ☣️]  █\n        \\\\   ░░░   /\n         '-░-░-'-█\n           ░ ░ ░\n         ▰▰  ░  ▰▰\n        ░░   ░   ░░\n      ==========="
        ]
    },
    "DEAD": [
        "\n\n            .-.\n           (X_X)\n             |\n            / \\\n           /   \\\n          /  ☠️  \\\n         /       \\\n      ===========",
        "\n\n            .-.\n           (x_x)\n             |\n            / \\\n           /   \\\n          /  ☠️  \\\n         /       \\\n      ==========="
    ]
}

STATE_FILE = "cyberplant_state.json"

class CyberPlantManager:
    def __init__(self, parent_frame, glitch_manager=None):
        self.parent_frame = parent_frame
        self.glitch_manager = glitch_manager

        # -------------------------------------------------------------
        # 1. SIMULATION STATE INITIALIZATION
        # -------------------------------------------------------------
        self.growth_points = 0.0
        self.hydration = 50.0
        self.radiation_level = 0.0
        self.alive = True
        self.animation_frame = 0
        self.ticks_since_save = 0

        # Logger / Alert Console History
        self.alerts = []

        # Load persisted state from disk
        self.load_state()

        # Build UI layout elements
        self.build_ui()

        # -------------------------------------------------------------
        # 2. START SIMULATION AND ANIMATION SCHEDULES
        # -------------------------------------------------------------
        self.tick_job = None
        self.breath_job = None
        self.start_loops()

    # -------------------------------------------------------------
    # PERSISTENCE / FILE I/O LAYER (ATOMIC SADO-SAVE)
    # -------------------------------------------------------------
    def load_state(self):
        """Attempts to load initial state variables from the JSON save file."""
        try:
            if os.path.exists(STATE_FILE):
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.growth_points = max(0.0, min(100.0, float(data.get("growth_points", 0.0))))
                    self.hydration = max(0.0, min(100.0, float(data.get("hydration", 50.0))))
                    self.radiation_level = max(0.0, min(100.0, float(data.get("radiation_level", 0.0))))
                    self.alive = bool(data.get("alive", True))
                self.add_alert("[ STATE LOADED ] Decrypted previous state.")
            else:
                self.add_alert("[ SYSTEM INIT ] No state file found. Standard SEED online.")
        except Exception as e:
            self.add_alert(f"[ ERROR ] Load failed: {str(e)[:25]}")
            # Restore defaults in case of corrupted file
            self.growth_points = 0.0
            self.hydration = 50.0
            self.radiation_level = 0.0
            self.alive = True

    def save_state(self):
        """Dumps simulation fields atomically into the JSON file to prevent corruption."""
        state_data = {
            "growth_points": self.growth_points,
            "hydration": self.hydration,
            "radiation_level": self.radiation_level,
            "alive": self.alive
        }
        temp_file = STATE_FILE + ".tmp"
        try:
            # Atomic swap structure: Write to temp file then rename
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(state_data, f, indent=4)
            os.replace(temp_file, STATE_FILE)
        except Exception as e:
            self.add_alert(f"[ ERROR ] Write failed: {str(e)[:25]}")
            # Ensure cleanup of tmp file if left behind
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass

    # -------------------------------------------------------------
    # UI ASSEMBLY & THEMING
    # -------------------------------------------------------------
    def build_ui(self):
        """Builds terminal-themed layout panels within the parent frame."""
        try:
            # Main container frame spanning parent
            self.main_container = tk.Frame(self.parent_frame, bg="#000000", highlightthickness=1, highlightbackground="#00ff00")
            self.main_container.pack(fill="both", expand=True, padx=5, pady=5)

            # Left Panel: Procedural ASCII Art Viewer
            self.left_panel = tk.Frame(self.main_container, bg="#000000", width=250)
            self.left_panel.pack(side="left", fill="both", expand=True, padx=5, pady=5)
            self.left_panel.pack_propagate(False)

            tk.Label(self.left_panel, text="// BIOMETRIC SCANNER", fg="#00ffff", bg="#000000", font=("Courier", 10, "bold")).pack(anchor="w", pady=(5, 2))
            
            self.txt_ascii = tk.Text(self.left_panel, bg="#000000", bd=0, highlightthickness=0, font=("Courier", 11, "bold"), wrap="none", height=10, width=22)
            self.txt_ascii.pack(fill="both", expand=True, padx=5, pady=5)
            self.txt_ascii.config(state=tk.DISABLED)

            # Right Panel: Stats and Alerts Readout
            self.right_panel = tk.Frame(self.main_container, bg="#0b0b0b", highlightthickness=1, highlightbackground="#333333")
            self.right_panel.pack(side="right", fill="both", expand=True, padx=5, pady=5)

            # Stage Name Header
            self.lbl_stage_title = tk.Label(self.right_panel, text="SPECIES STAGE:", fg="#ffff00", bg="#0b0b0b", font=("Courier", 10, "bold"))
            self.lbl_stage_title.pack(anchor="w", padx=10, pady=(10, 0))

            self.lbl_stage_val = tk.Label(self.right_panel, text="SEED (NOMINAL)", fg="#00ff00", bg="#0b0b0b", font=("Courier", 11, "bold"))
            self.lbl_stage_val.pack(anchor="w", padx=10, pady=(0, 10))

            # Progress Bar Indicators (Hydration, Growth, Radiation)
            tk.Label(self.right_panel, text="H2O HYDRATION", fg="#00ffff", bg="#0b0b0b", font=("Courier", 9, "bold")).pack(anchor="w", padx=10)
            self.lbl_hyd_bar = tk.Label(self.right_panel, text="", fg="#00ffff", bg="#0b0b0b", font=("Courier", 10, "bold"))
            self.lbl_hyd_bar.pack(anchor="w", padx=10, pady=(0, 8))

            tk.Label(self.right_panel, text="DEVELOPMENT PROGRESS", fg="#00ff00", bg="#0b0b0b", font=("Courier", 9, "bold")).pack(anchor="w", padx=10)
            self.lbl_growth_bar = tk.Label(self.right_panel, text="", fg="#00ff00", bg="#0b0b0b", font=("Courier", 10, "bold"))
            self.lbl_growth_bar.pack(anchor="w", padx=10, pady=(0, 8))

            tk.Label(self.right_panel, text="MUTATION MATRIX", fg="#ffff00", bg="#0b0b0b", font=("Courier", 9, "bold")).pack(anchor="w", padx=10)
            self.lbl_rad_bar = tk.Label(self.right_panel, text="", fg="#ffff00", bg="#0b0b0b", font=("Courier", 10, "bold"))
            self.lbl_rad_bar.pack(anchor="w", padx=10, pady=(0, 10))

            # Console Alert Log Panel
            tk.Label(self.right_panel, text="CONSOLE OUTPUT", fg="#ff00ff", bg="#0b0b0b", font=("Courier", 8, "bold")).pack(anchor="w", padx=10)
            self.txt_console = tk.Text(self.right_panel, bg="#000000", fg="#00ff00", font=("Courier", 8), height=4, width=32, bd=1, highlightthickness=1, highlightbackground="#333333")
            self.txt_console.pack(fill="x", padx=10, pady=(2, 10))
            self.txt_console.config(state=tk.DISABLED)

            # Action Bar: Control Buttons at Bottom
            self.action_bar = tk.Frame(self.parent_frame, bg="#000000")
            self.action_bar.pack(fill="x", side="bottom", padx=5, pady=(0, 5))

            self.btn_h2o = tk.Button(self.action_bar, text="[ INJECT H2O ]", bg="#000000", fg="#00ffff", activebackground="#00ffff", activeforeground="#000000", bd=1, highlightthickness=1, highlightbackground="#00ffff", font=("Courier", 9, "bold"), command=self.inject_h2o)
            self.btn_h2o.pack(side="left", fill="x", expand=True, padx=2)

            self.btn_rad = tk.Button(self.action_bar, text="[ EMIT RADIATION ]", bg="#000000", fg="#ff00ff", activebackground="#ff00ff", activeforeground="#000000", bd=1, highlightthickness=1, highlightbackground="#ff00ff", font=("Courier", 9, "bold"), command=self.emit_radiation)
            self.btn_rad.pack(side="left", fill="x", expand=True, padx=2)

            self.btn_purge = tk.Button(self.action_bar, text="[ PURGE PROTOCOL ]", bg="#000000", fg="#ff0000", activebackground="#ff0000", activeforeground="#000000", bd=1, highlightthickness=1, highlightbackground="#ff0000", font=("Courier", 9, "bold"), command=self.purge_protocol)
            self.btn_purge.pack(side="left", fill="x", expand=True, padx=2)

            # Bind hover animations for standard fallbacks
            self.bind_cyber_hover(self.btn_h2o, "#00ffff", "#ffffff", "#00ffff", "#ffffff")
            self.bind_cyber_hover(self.btn_rad, "#ff00ff", "#ffffff", "#ff00ff", "#ffffff")
            self.bind_cyber_hover(self.btn_purge, "#ff0000", "#ffffff", "#ff0000", "#ffffff")

            # Register with GlitchManager if available
            if self.glitch_manager is not None:
                try:
                    self.glitch_manager.register_widget(self.btn_h2o, magnitude=0.15)
                    self.glitch_manager.register_widget(self.btn_rad, magnitude=0.15)
                    self.glitch_manager.register_widget(self.btn_purge, magnitude=0.15)
                except Exception as ex:
                    self.add_alert(f"[ GLITCH WARN ] Register failed: {str(ex)[:15]}")

            # Initial draw
            self.update_ui()
            self.update_ascii_display()
        except Exception as e:
            # Fatal GUI setup intercept
            print(f"[CyberPlantManager] Layout construction failed: {e}")

    # -------------------------------------------------------------
    # CUSTOM INTERFACE EFFECTS
    # -------------------------------------------------------------
    def bind_cyber_hover(self, widget, normal_fg, hover_fg, normal_border, hover_border):
        """Binds responsive high-contrast hover effects for the action buttons."""
        def on_enter(event):
            try:
                if widget["state"] != tk.DISABLED:
                    widget.config(fg=hover_fg, highlightbackground=hover_border)
            except:
                pass

        def on_leave(event):
            try:
                if widget["state"] != tk.DISABLED:
                    widget.config(fg=normal_fg, highlightbackground=normal_border)
            except:
                pass

        widget.bind("<Enter>", on_enter, add="+")
        widget.bind("<Leave>", on_leave, add="+")

    def make_progress_bar(self, value, width=15):
        """Procedurally draws block progress lines for console aesthetic."""
        percent = max(0.0, min(100.0, value))
        filled_len = int(round((percent / 100.0) * width))
        empty_len = width - filled_len
        return f"[ {'▰' * filled_len}{'▱' * empty_len} ] {percent:5.1f}%"

    def add_alert(self, msg):
        """Pushes a timed log notification onto the terminal alert queue."""
        timestamp = time.strftime("%H:%M:%S")
        self.alerts.append(f"[{timestamp}] {msg}")
        if len(self.alerts) > 4:
            self.alerts.pop(0)
        self.refresh_console_log()

    def refresh_console_log(self):
        """Writes buffered alert alerts inside the console display widget."""
        try:
            if hasattr(self, 'txt_console') and self.txt_console.winfo_exists():
                self.txt_console.config(state=tk.NORMAL)
                self.txt_console.delete("1.0", tk.END)
                self.txt_console.insert(tk.END, "\n".join(self.alerts))
                self.txt_console.see(tk.END)
                self.txt_console.config(state=tk.DISABLED)
        except:
            pass

    # -------------------------------------------------------------
    # SIMULATION TICK LOGIC
    # -------------------------------------------------------------
    def start_loops(self):
        """Launches the independent visual and state simulation loops."""
        self.simulation_tick()
        self.breathing_tick()

    def stop_loops(self):
        """Terminates asynchronous timing schedule queues cleanly."""
        try:
            if self.tick_job:
                self.parent_frame.after_cancel(self.tick_job)
                self.tick_job = None
            if self.breath_job:
                self.parent_frame.after_cancel(self.breath_job)
                self.breath_job = None
        except:
            pass

    def get_stage(self):
        """Calculates developmental stages dynamically based on growth scale."""
        g = self.growth_points
        if g <= 15.0:
            return "SEED"
        elif g <= 45.0:
            return "SPROUT"
        elif g <= 80.0:
            return "PROTO-STALK"
        else:
            return "MATURE_MATRIX_ROOT"

    def simulation_tick(self):
        """Core loop processing state steps every 1000ms."""
        try:
            if not self.parent_frame.winfo_exists():
                return

            if self.alive:

                # Death boundaries FIRST
                if self.hydration <= 0.0:
                    self.alive = False
                    self.add_alert("[ CRITICAL ] Plant died of dehydration!")
                    self.save_state()

                elif self.hydration >= 100.0:
                    self.alive = False
                    self.add_alert("[ CRITICAL ] Plant died of ROOT ROT!")
                    self.save_state()

                else:
                    # THEN drain hydration
                    self.hydration = max(0.0, self.hydration - 0.5)

                    # Growth rules
                    if 25.0 <= self.hydration <= 75.0:
                        prev_stage = self.get_stage()
                        self.growth_points = min(100.0, self.growth_points + 0.2)
                        curr_stage = self.get_stage()

                        if prev_stage != curr_stage:
                            self.add_alert(f"[ EVOLUTION ] Evolved into {curr_stage}!")

                # 4. Auto-save every 10 ticks
                self.ticks_since_save += 1
                if self.ticks_since_save >= 10:
                    self.save_state()
                    self.ticks_since_save = 0
                    self.add_alert("[ SYSTEM ] State autosaved to disk.")

            # Update UI controls
            self.update_ui()

        except Exception as ex:
            # Stop tick loop schedules if widgets are invalid or missing
            return

        # Queue next simulation cycle
        self.tick_job = self.parent_frame.after(1000, self.simulation_tick)

    def breathing_tick(self):
        """Asynchronous breathing frame sub-loop cycling around 600ms."""
        try:
            if not self.parent_frame.winfo_exists():
                return
            
            # Alternate animation index
            self.animation_frame = 1 - self.animation_frame
            self.update_ascii_display()
        except:
            return

        # Cycle visual framing (500ms - 800ms)
        self.breath_job = self.parent_frame.after(600, self.breathing_tick)

    # -------------------------------------------------------------
    # ACTION BAR INTERACTIONS
    # -------------------------------------------------------------
    def inject_h2o(self):
        """Action logic to replenish hydration matrix."""
        if not self.alive:
            return
        self.hydration = min(100.0, self.hydration + 15.0)
        self.add_alert("[ INJECT ] H2O Hydration +15.0%")
        self.update_ui()
        self.update_ascii_display()

    def emit_radiation(self):
        """Action logic to emit digital mutation waves."""
        if not self.alive:
            return
        self.radiation_level = min(100.0, self.radiation_level + 10.0)
        self.add_alert("[ RADIATION ] Mutation Vector +10.0%")
        if self.radiation_level > 50.0 and (self.radiation_level - 10.0) <= 50.0:
            self.add_alert("[ ALERT ] Gene structural mutation detected!")
        self.update_ui()
        self.update_ascii_display()

    def purge_protocol(self):
        """Action logic to wipe trace logs and reset simulator state."""
        # Only active if dead
        if self.alive:
            return

        # Delete JSON save file
        try:
            if os.path.exists(STATE_FILE):
                os.remove(STATE_FILE)
            self.add_alert("[ PURGE ] Saved trace files deleted.")
        except Exception as e:
            self.add_alert(f"[ ERROR ] Deletion failed: {str(e)[:15]}")

        # Reset states to defaults
        self.growth_points = 0.0
        self.hydration = 50.0
        self.radiation_level = 0.0
        self.alive = True
        self.animation_frame = 0
        self.ticks_since_save = 0

        self.alerts.clear()
        self.add_alert("[ RESET ] Plant system default restored.")
        self.add_alert("[ SYSTEM READY ] Seeding nominal matrix.")

        self.update_ui()
        self.update_ascii_display()

    # -------------------------------------------------------------
    # DISPLAY ENGINE RENDERING UPDATES
    # -------------------------------------------------------------
    def update_ui(self):
        """Redraws readout bars and configures interaction buttons based on state."""
        try:
            if not self.parent_frame.winfo_exists():
                return

            # Button Deactivation Logic with low-visibility hex coloring
            if not self.alive:
                self.btn_h2o.config(state=tk.DISABLED, fg="#333333", highlightbackground="#222222")
                self.btn_rad.config(state=tk.DISABLED, fg="#333333", highlightbackground="#222222")
                self.btn_purge.config(state=tk.NORMAL, fg="#ff0000", highlightbackground="#ff0000")
            else:
                self.btn_h2o.config(state=tk.NORMAL, fg="#00ffff", highlightbackground="#00ffff")
                self.btn_rad.config(state=tk.NORMAL, fg="#ff00ff", highlightbackground="#ff00ff")
                self.btn_purge.config(state=tk.DISABLED, fg="#333333", highlightbackground="#222222")

            # Determine Stage and Status formatting
            stage = self.get_stage()
            if not self.alive:
                status_text = "DECEASED"
                status_color = "#ff0000"
            elif self.radiation_level > 50.0:
                status_text = "MUTATED"
                status_color = "#ff00ff"
            else:
                status_text = "NOMINAL"
                status_color = "#00ff00"

            self.lbl_stage_val.config(text=f"{stage} ({status_text})", fg=status_color)

            # Update text bars
            self.lbl_hyd_bar.config(text=self.make_progress_bar(self.hydration))
            self.lbl_growth_bar.config(text=self.make_progress_bar(self.growth_points))
            self.lbl_rad_bar.config(text=self.make_progress_bar(self.radiation_level))

            # Dynamic bar coloring based on nominal/critical boundaries
            if self.hydration < 25.0 or self.hydration > 75.0:
                self.lbl_hyd_bar.config(fg="#ff0000")  # Critical warning red
            else:
                self.lbl_hyd_bar.config(fg="#00ffff")  # Safe cyan

            if self.radiation_level > 50.0:
                self.lbl_rad_bar.config(fg="#ff00ff")  # Mutated magenta
            else:
                self.lbl_rad_bar.config(fg="#ffff00")  # Warning yellow

        except Exception:
            pass

    def update_ascii_display(self):
        """Resolves ASCII frame sequences based on stage and mutation flags."""
        try:
            if not hasattr(self, 'txt_ascii') or not self.txt_ascii.winfo_exists():
                return

            # Determine frame subset
            if not self.alive:
                frames = ASCII_FRAMES["DEAD"]
            else:
                stage = self.get_stage()
                if self.radiation_level > 50.0:
                    frames = ASCII_FRAMES[stage]["glitched"]
                else:
                    frames = ASCII_FRAMES[stage]["normal"]

            frame_idx = self.animation_frame % len(frames)
            ascii_text = frames[frame_idx]

            # Render text update
            self.txt_ascii.config(state=tk.NORMAL)
            self.txt_ascii.delete("1.0", tk.END)
            self.txt_ascii.insert(tk.END, ascii_text)

            # Color aesthetic matches current status
            if not self.alive:
                color = "#ff0000"
            elif self.radiation_level > 50.0:
                color = "#ff00ff"
            else:
                color = "#00ff00"

            self.txt_ascii.config(fg=color, state=tk.DISABLED)
        except Exception:
            pass

# ==============================================================================
# 5. STANDALONE VERIFICATION CLIENT
# ==============================================================================
if __name__ == "__main__":
    # Create diagnostic standalone window frame
    root = tk.Tk()
    root.title("ChaoHub CyberPlant Manager - System Diagnostics")
    root.geometry("640x400")
    root.config(bg="#000000")

    # Attempt to load GlitchEngine to verify hover registrations
    glitch_mgr = None
    try:
        from glitch_engine import GlitchManager
        glitch_mgr = GlitchManager(root)
        print("[TEST] GlitchManager initialized and hooked successfully.")
    except Exception as e:
        print(f"[TEST] GlitchManager unavailable, using fallback hover layout: {e}")

    # Build header banner
    header = tk.Frame(root, bg="#0b0b0b", highlightthickness=1, highlightbackground="#00ff00")
    header.pack(fill="x", padx=10, pady=5)
    tk.Label(header, text="CYBER VIRTUAL PLANT SIMULATOR v2.8", fg="#00ff00", bg="#0b0b0b", font=("Courier", 12, "bold")).pack(pady=5)

    # Frame to anchor simulator module
    client_frame = tk.Frame(root, bg="#000000")
    client_frame.pack(fill="both", expand=True, padx=10, pady=5)

    # Instantiate CyberPlantManager
    manager = CyberPlantManager(client_frame, glitch_manager=glitch_mgr)

    # Run GUI loop
    root.mainloop()
