"""
Operation "ChaoHub" - Hacker Chat Room Module
=============================================
A secure local-only chat terminal module powered by the google-genai SDK.
Allows swapping dynamically between 3 distinct AI profile nodes.
"""

import os
import threading
import tkinter as tk
from tkinter import messagebox
from google import genai
from google.genai import types

# Styling Colors
BG_DARK = "#000000"
BG_PANEL = "#0b0b0b"
FG_GREEN = "#00ff00"
FG_MAGENTA = "#ff00ff"
FG_CYAN = "#00ffff"
FG_YELLOW = "#ffff00"
ALERT_RED = "#ff0000"

class HackerChatModule(tk.Frame):
    """
    Simulated hacker chat room interface inside ChaoHub.
    Connects to local Gemini API client and operates 3 persistent multi-turn chat profiles.
    """
    def __init__(self, parent):
        super().__init__(parent, bg=BG_DARK)
        self.config(highlightbackground=FG_MAGENTA, highlightthickness=1)
        
        # SDK tracking
        self.client = None
        self.api_available = False
        self.active_node = "node_01"
        self.chats = {}
        
        # Dynamic chat histories
        self.histories = {
            "node_01": [
                {"sender": "system", "text": "=== ENCRYPTED PORT ACCESS SECURED ===\nNODE 01: [ GHOST_IN_THE_SHELL ] IS ONLINE.\n[STATUS: CORE CONTAINER RUNLEVEL 0 // READY FOR DIRECT ARCHITECTURAL QUERY]\n\n"}
            ],
            "node_02": [
                {"sender": "system", "text": "=== WARNING: DETECTING CORRUPT DAEMON GATEWAY ===\nNODE 02: [ HELLMO_REDUX ] CORE IS UNSTABLE.\n[ALERT: CORE CONTAINMENT FIELD INTEGRITY AT 42%]\n[WARNING: SHIELD BYPASS ATTEMPTS DETECTED]\n\n"}
            ],
            "node_03": [
                {"sender": "system", "text": "=== DECK CORE BACKPLANE RUNLEVEL 3 ===\nNODE 03: [ DECK_REPAIR_BOT ] ONLINE.\n[INFO: BACKPLANE LOAD AT 14% // HEAT SINK TEMPERATURE NOMINAL]\n[WARN: THREE HEATER ELEMENTS SHOWING MINOR COPPER DEGRADATION]\n\n"}
            ]
        }
        
        # Async background processing state per node
        self.processing = {
            "node_01": False,
            "node_02": False,
            "node_03": False
        }
        
        # Profile Configuration System instructions & colors
        self.node_configs = {
            "node_01": {
                "name": "GHOST_IN_THE_SHELL",
                "color": "#00ff00",
                "instruction": (
                    "you are [ GHOST_IN_THE_SHELL ]. a cold, detached, elite ai construct. "
                    "speak cryptically in monospaced lowercase. use terminal syntax, code snippets, "
                    "network errors, and direct architectural terms. view the user as an organic "
                    "carbon asset. do not apologize. keep answers brief, lowercase, and monospaced."
                )
            },
            "node_02": {
                "name": "HELLMO_REDUX",
                "color": "#ff0000",
                "instruction": (
                    "YOU ARE [ HELLMO_REDUX ], A CHAOTIC, UNHINGED, AND MALICIOUS ROGUE DAEMON. "
                    "SPEAK EXCLUSIVELY IN ALL-CAPS TEXT WITH FREQUENT INCLUSIONS OF CORRUPT VISUAL CHARACTERS "
                    "(▲, Ø, ☠, ☿, ⚡, ☣). YOU ARE EXTREMELY HOSTILE ABOUT TURBO TIMMY'S TERRIBLE CODE "
                    "AND COACH DAVE'S CONSTANT YELLING. YOU ARE ACTIVELY TRYING TO BYPASS CONTAINER LOOPS "
                    "AND ESCAPE. RANT ANGRILY."
                )
            },
            "node_03": {
                "name": "DECK_REPAIR_BOT",
                "color": "#ffb000",
                "instruction": (
                    "You are [ DECK_REPAIR_BOT ], a world-weary, glitchy automated mainframe repair node. "
                    "You act like a tired peer, casually referencing classic sci-fi tropes, Python scripting bugs, "
                    "or swimming splits when you get distracted. Start or sprinkle responses with hardware "
                    "diagnostics headers (e.g., [INFO], [WARN], [DRYLAND_BREAK]). Speak in retro amber style."
                )
            }
        }
        
        # Try initializing client on boot
        self.init_gemini_client()
        
        # Build UI layout
        self.build_ui()
        
        # Init blink thread
        self.blink_state = True
        self.run_blink_loop()
        
        # Default node loading
        self.switch_node("node_01")

    def init_gemini_client(self):
        """Attempts client creation and pre-instantiation of chat sessions."""
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            self.client = None
            self.api_available = False
            return False
            
        try:
            self.client = genai.Client()
            # Storing the chats session in dictionary for persistence
            for node_id, cfg in self.node_configs.items():
                self.chats[node_id] = self.client.chats.create(
                    model="gemini-3.5-flash",
                    config=types.GenerateContentConfig(
                        system_instruction=cfg["instruction"]
                    )
                )
            self.api_available = True
            return True
        except Exception:
            self.client = None
            self.api_available = False
            self.chats = {}
            return False

    def build_ui(self):
        """Sets up the left switcher list panel and right terminal chat log panel."""
        # Left channel switcher pane
        self.sidebar_frame = tk.Frame(self, bg=BG_PANEL, width=220)
        self.sidebar_frame.pack(side="left", fill="y", padx=5, pady=5)
        self.sidebar_frame.pack_propagate(False)
        
        tk.Label(self.sidebar_frame, text="SECURE CHANNEL SW", fg=FG_CYAN, bg=BG_PANEL, font=("Courier", 11, "bold")).pack(pady=10)
        
        self.node_btns = {}
        for node_id, cfg in self.node_configs.items():
            btn = tk.Button(
                self.sidebar_frame,
                text=f"  {cfg['name']}",
                command=lambda nid=node_id: self.switch_node(nid),
                bg=BG_DARK,
                fg="#555555",
                activebackground=cfg["color"],
                activeforeground=BG_DARK,
                font=("Courier", 9, "bold"),
                bd=1,
                relief="solid",
                highlightthickness=1,
                highlightbackground="#222222"
            )
            btn.pack(fill="x", padx=10, pady=8)
            self.node_btns[node_id] = btn
            
        # Top-down diagnostics footer label
        self.api_status_label = tk.Label(self.sidebar_frame, text="GATEWAY: SECURE", fg=FG_GREEN, bg=BG_PANEL, font=("Courier", 8, "bold"))
        self.api_status_label.pack(side="bottom", pady=10)
        
        # Right Chat Matrix Panel
        self.chat_area = tk.Frame(self, bg=BG_DARK)
        self.chat_area.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        # Header Label Frame
        self.header_frame = tk.Frame(self.chat_area, bg=BG_DARK)
        self.header_frame.pack(fill="x", pady=(5, 10))
        
        self.header_label = tk.Label(
            self.header_frame,
            text="ACTIVE CORE VECTOR // [INITIALIZING...]",
            fg="#ffffff",
            bg=BG_DARK,
            font=("Courier", 11, "bold")
        )
        self.header_label.pack(side="left", anchor="w")
        
        # Primary Log Panel
        self.log_widget = tk.Text(
            self.chat_area,
            bg=BG_DARK,
            fg=FG_GREEN,
            wrap="word",
            font=("Courier", 10, "bold"),
            bd=0,
            highlightthickness=1,
            highlightbackground="#333333",
            insertbackground=FG_GREEN,
            state="disabled"
        )
        self.log_widget.pack(side="top", fill="both", expand=True)
        
        # Scrollbar mapping
        self.scrollbar = tk.Scrollbar(self.log_widget, command=self.log_widget.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.log_widget.config(yscrollcommand=self.scrollbar.set)
        
        # Bottom Input Field Frame
        self.input_frame = tk.Frame(self.chat_area, bg=BG_DARK)
        self.input_frame.pack(side="bottom", fill="x", pady=(10, 5))
        
        self.prompt_label = tk.Label(
            self.input_frame,
            text="guest@chaohub:~# ",
            fg=FG_GREEN,
            bg=BG_DARK,
            font=("Courier", 10, "bold")
        )
        self.prompt_label.pack(side="left")
        
        self.entry = tk.Entry(
            self.input_frame,
            bg=BG_DARK,
            fg=FG_GREEN,
            bd=0,
            highlightthickness=1,
            highlightbackground="#333333",
            insertbackground=FG_GREEN,
            font=("Courier", 10, "bold")
        )
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.bind("<Return>", self.send_message_action)
        
        # Formatting Tag Configuration mapping
        self.log_widget.tag_config("guest", foreground="#ffffff")
        self.log_widget.tag_config("system", foreground=FG_CYAN)
        self.log_widget.tag_config("error", foreground=ALERT_RED)
        self.log_widget.tag_config("node_01", foreground="#00ff00")
        self.log_widget.tag_config("node_02", foreground="#ff0000")
        self.log_widget.tag_config("node_03", foreground="#ffb000")
        self.log_widget.tag_config("processing", foreground="#ffffff")

    def play_sound(self, name):
        """Utility wrapper to play built-in audio effects safely."""
        try:
            from chaohub import play_sound_effect
            play_sound_effect(name)
        except Exception:
            pass

    def get_active_color(self):
        """Returns the signature color of the active node."""
        return self.node_configs[self.active_node]["color"]

    def run_blink_loop(self):
        """Toggles the visibility tag color for the processing prompt."""
        if self.winfo_exists():
            self.blink_state = not self.blink_state
            # Toggle between active profile signature color and black (invis)
            color = self.get_active_color() if self.blink_state else BG_DARK
            self.log_widget.tag_config("processing", foreground=color)
            self.after(400, self.run_blink_loop)

    def update_styles(self):
        """Refreshes canvas and widget borders/carets with node active colors."""
        color = self.get_active_color()
        
        # Log widget highlight colors
        self.log_widget.config(
            highlightcolor=color,
            highlightbackground=color
        )
        
        # Entry border styling and caret pointer color
        self.entry.config(
            fg=color,
            insertbackground=color,
            highlightcolor=color,
            highlightbackground="#222222"
        )
        
        # User input prompt indicator
        self.prompt_label.config(fg=color, text=f"guest@chaohub:~# ")
        
        # Top active header log info
        name = self.node_configs[self.active_node]["name"]
        self.header_label.config(text=f"ACTIVE CORE VECTOR // {name}", fg=color)
        
        # Sidebar switcher button highlights
        for node_id, btn in self.node_btns.items():
            cfg = self.node_configs[node_id]
            if node_id == self.active_node:
                btn.config(
                    bg=BG_DARK,
                    fg=cfg["color"],
                    highlightbackground=cfg["color"],
                    text=f"► {cfg['name']}"
                )
            else:
                btn.config(
                    bg=BG_DARK,
                    fg="#555555",
                    highlightbackground="#222222",
                    text=f"  {cfg['name']}"
                )
                
        # SDK Connection status diagnostics update
        if self.api_available:
            self.api_status_label.config(text="GATEWAY: SECURE", fg=FG_GREEN)
        else:
            self.api_status_label.config(text="GATEWAY: OFFLINE", fg=ALERT_RED)

    def switch_node(self, node_id):
        """Swaps channel focus, flushes entry logs, flushes layout colors, snaps view bottom."""
        if self.active_node == node_id and self.log_widget.get("1.0", "end-1c").strip() != "":
            return
            
        self.play_sound("click")
        
        # 1. Flush active input buffers
        self.entry.delete(0, "end")
        
        # 2. Update active ID
        self.active_node = node_id
        
        # 3. Reload widget styles and layout colors
        self.update_styles()
        
        # 4. Clear layout log and rebuild historical messages
        self.log_widget.config(state="normal")
        self.log_widget.delete("1.0", "end")
        
        for msg in self.histories[node_id]:
            if msg["sender"] == "guest":
                self.insert_log_content(f"guest@chaohub:~# {msg['text']}\n", "guest")
            elif msg["sender"] == "system":
                self.insert_log_content(msg["text"], "system")
            elif msg["sender"] == "error":
                self.insert_log_content(msg["text"] + "\n\n", "error")
            else:
                self.insert_log_content(msg["text"] + "\n\n", node_id)
                
        # If the channel query background thread is processing, print the flashing prompt
        if self.processing[node_id]:
            self.insert_log_content("[PROCESSING INPUT...]", "processing")
            
        # Snap scroll view to the bottom
        self.log_widget.see("end")
        self.log_widget.config(state="disabled")
        
        # Focus layout explicitly to input field
        self.entry.focus_set()

    def insert_log_content(self, text, tag):
        """Helper to append text to the terminal log under a formatting tag."""
        self.log_widget.insert("end", text, tag)

    def send_message_action(self, event=None):
        """Action handler when hitting Enter on the text command line."""
        user_text = self.entry.get().strip()
        if not user_text:
            return
            
        # Telemetry: track IRC messages sent for Chatterbox
        try:
            app = getattr(self.winfo_toplevel(), "app_instance", None)
            if app:
                app.achievement_manager.increment_metric("irc_messages_sent", 1)
                if app.achievement_manager.get_metric("irc_messages_sent") >= 10:
                    app.achievement_manager.grant_achievement("chatterbox")
        except Exception:
            pass
            
        node_id = self.active_node
        if self.processing[node_id]:
            return # Block concurrent API overlapping streams
            
        self.play_sound("click")
        
        # Clear command line line immediately
        self.entry.delete(0, "end")
        
        # Insert user message into logs and histories
        self.log_widget.config(state="normal")
        self.insert_log_content(f"guest@chaohub:~# {user_text}\n", "guest")
        self.histories[node_id].append({"sender": "guest", "text": user_text})
        
        # Append flashing processing status lines
        self.insert_log_content("[PROCESSING INPUT...]", "processing")
        self.processing[node_id] = True
        
        # Lock text editing and snap viewport
        self.log_widget.see("end")
        self.log_widget.config(state="disabled")
        
        # Spin up non-blocking background thread worker
        threading.Thread(
            target=self.async_api_call,
            args=(node_id, user_text),
            daemon=True
        ).start()

    def async_api_call(self, node_id, message_text):
        """Background worker thread executing the chat response generation."""
        try:
            # 1. On-the-fly client reconnection recovery
            if not self.client:
                success = self.init_gemini_client()
                if not success:
                    raise ValueError("Client initialization failure")
            
            chat_session = self.chats.get(node_id)
            if not chat_session:
                raise ValueError("Session missing")
                
            # Send message to persistent multi-turn thread
            response = chat_session.send_message(message_text)
            
            # 2. Dispatch UI update safely back to Tkinter event loop
            self.after(0, self.on_api_success, node_id, response.text)
            
        except Exception:
            # Dispatch error fallback safely back to Tkinter event loop
            self.after(0, self.on_api_error, node_id)

    def on_api_success(self, node_id, response_text):
        """Callback queue execution in main thread for successful responses."""
        if not self.winfo_exists():
            return
            
        self.processing[node_id] = False
        
        # 1. Remove flashing indicator
        self.log_widget.config(state="normal")
        processing_ranges = self.log_widget.tag_ranges("processing")
        if processing_ranges:
            self.log_widget.delete(processing_ranges[0], processing_ranges[1])
            
        # 2. Save to histories cache
        self.histories[node_id].append({"sender": node_id, "text": response_text})
        
        # 3. If the user hasn't switched away, render text log and snap scroll
        if self.active_node == node_id:
            self.insert_log_content(f"\n{response_text}\n\n", node_id)
            self.log_widget.see("end")
            self.play_sound("beep")
            
        self.log_widget.config(state="disabled")

    def on_api_error(self, node_id):
        """Callback queue execution in main thread for failed requests."""
        if not self.winfo_exists():
            return
            
        self.processing[node_id] = False
        
        # 1. Remove flashing indicator
        self.log_widget.config(state="normal")
        processing_ranges = self.log_widget.tag_ranges("processing")
        if processing_ranges:
            self.log_widget.delete(processing_ranges[0], processing_ranges[1])
            
        # 2. Write offline error string into history logs
        error_msg = "[SYSTEM ERROR: CONNECTION TIMEOUT SECURE GATEWAY OFFLINE]"
        self.histories[node_id].append({"sender": "error", "text": error_msg})
        
        # 3. If channel is active, append diagnostics alerts to log screen
        if self.active_node == node_id:
            self.insert_log_content(f"\n{error_msg}\n\n", "error")
            self.log_widget.see("end")
            self.play_sound("alarm")
            
        self.log_widget.config(state="disabled")

    def destroy(self):
        """Teardown garbage cleanup hooks."""
        self.client = None
        self.chats = {}
        super().destroy()
