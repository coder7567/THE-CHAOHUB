"""
Operation "ChaoHub" - ChaoNet Dark Web Simulator
=================================================
An underground retro-TOR browser interface running completely locally inside ChaoHub.
Loads custom mock `.onion` addresses, showcasing unique ASCII art layouts,
lore-heavy whistleblower text bases, dynamic hyperlink bindings, and screen shake alerts.
"""

import re
import random
import tkinter as tk
from tkinter import messagebox

# Global Styling Colors matching ChaoHub palette
BG_DARK = "#000000"
BG_PANEL = "#0b0b0b"
FG_GREEN = "#00ff00"
FG_MAGENTA = "#ff00ff"
FG_CYAN = "#00ffff"
FG_YELLOW = "#ffff00"
ALERT_RED = "#ff0000"
AMBER_PHOSPHOR = "#ffb000"
CHARCOAL_DARK = "#141414"

class ChaoNetModule(tk.Frame):
    """
    ChaoNet Dark Web Simulator Frame.
    Implements navigation bar, simulated proxy connection logs,
    and a custom local DNS router routing to three specific obfuscated onion nodes.
    """
    def __init__(self, parent, glitch_manager=None):
        super().__init__(parent, bg=BG_DARK)
        self.config(highlightbackground=FG_CYAN, highlightthickness=1)
        
        self.glitch_manager = glitch_manager
        
        # Lifecycle sanitation tracking (holds all active scheduled after job IDs)
        self.active_jobs = []
        
        # Navigation History Stack
        self.history_stack = []
        self.current_url = "welcome.onion"
        
        # Router table mapping mock domains to rendering functions
        self.onion_routing_table = {
            "silicon_bazaar.onion": self.render_bazaar_node,
            "containment_breach.onion": self.render_breach_node,
            "deep_water_diagnostics.onion": self.render_diagnostics_node
        }
        
        # Build layout UI
        self.build_ui()
        
        # Load default landing view
        self.render_welcome_node()

    def play_sound(self, name):
        """Safely loads and plays UI sounds through Pygame wrapper."""
        try:
            from chaohub import play_sound_effect
            play_sound_effect(name)
        except Exception:
            pass

    def build_ui(self):
        """Sets up the top navigation bar panel and viewport container."""
        # 1. Top Navigation Bar Panel
        self.nav_frame = tk.Frame(self, bg=BG_PANEL, height=45)
        self.nav_frame.pack(side="top", fill="x", padx=5, pady=5)
        self.nav_frame.pack_propagate(False)
        
        # Stylized Back Button
        self.back_btn = tk.Label(
            self.nav_frame, 
            text="[ BACK ]", 
            fg=FG_GREEN, 
            bg=BG_PANEL, 
            font=("Courier", 10, "bold"),
            cursor="hand2", 
            padx=10
        )
        self.back_btn.pack(side="left", padx=5, fill="y")
        self.back_btn.bind("<Button-1>", self.on_back_clicked)
        self.back_btn.bind("<Enter>", lambda e: self.back_btn.config(fg="#ffffff"))
        self.back_btn.bind("<Leave>", lambda e: self.back_btn.config(fg=FG_GREEN))
        
        # Stylized Refresh Button
        self.refresh_btn = tk.Label(
            self.nav_frame, 
            text="[ REFRESH ]", 
            fg=FG_GREEN, 
            bg=BG_PANEL, 
            font=("Courier", 10, "bold"),
            cursor="hand2", 
            padx=10
        )
        self.refresh_btn.pack(side="left", padx=5, fill="y")
        self.refresh_btn.bind("<Button-1>", self.on_refresh_clicked)
        self.refresh_btn.bind("<Enter>", lambda e: self.refresh_btn.config(fg="#ffffff"))
        self.refresh_btn.bind("<Leave>", lambda e: self.refresh_btn.config(fg=FG_GREEN))
        
        # URL Input Bar Container (Gives a clean custom outline)
        url_container = tk.Frame(self.nav_frame, bg=FG_GREEN, padx=1, pady=1)
        url_container.pack(side="left", fill="both", expand=True, padx=10, pady=5)
        
        self.address_entry = tk.Entry(
            url_container,
            bg=FG_GREEN,
            fg=BG_DARK,
            font=("Courier", 11, "bold"),
            bd=0,
            insertbackground=BG_DARK,
            relief="flat"
        )
        self.address_entry.pack(fill="both", expand=True, padx=5)
        self.address_entry.insert(0, self.current_url)
        self.address_entry.bind("<Return>", self.on_connect_clicked)
        
        # Flashing Execution Node [ CONNECT TO GATEWAY ]
        self.connect_btn = tk.Label(
            self.nav_frame, 
            text="[ CONNECT TO GATEWAY ]", 
            fg=BG_DARK, 
            bg=FG_GREEN, 
            font=("Courier", 10, "bold"),
            cursor="hand2", 
            padx=10
        )
        self.connect_btn.pack(side="right", padx=5, fill="y")
        self.connect_btn.bind("<Button-1>", self.on_connect_clicked)
        
        # Connect button pulse loop
        self.pulse_btn_color()

        # 2. Main Site Viewport Container
        # Positioned inside a relative placement wrapper for screen shake support
        self.viewport_wrapper = tk.Frame(self, bg=BG_DARK)
        self.viewport_wrapper.pack(side="bottom", fill="both", expand=True, padx=5, pady=(0, 5))
        
        self.viewport_container = tk.Frame(self.viewport_wrapper, bg=BG_DARK)
        self.viewport_container.place(x=0, y=0, relwidth=1.0, relheight=1.0)
        
        # Currently rendered content frame reference
        self.active_page_frame = None

    def pulse_btn_color(self):
        """Pulsates the connect button color between Matrix Green and warning colors."""
        if not self.winfo_exists():
            return
        
        current_bg = self.connect_btn.cget("bg")
        # Pulse between green and yellow
        next_bg = FG_YELLOW if current_bg == FG_GREEN else FG_GREEN
        self.connect_btn.config(bg=next_bg)
        
        job = self.after(800, self.pulse_btn_color)
        self.active_jobs.append(job)

    # -------------------------------------------------------------
    # ROUTING & PROXY ENGINE LOGS
    # -------------------------------------------------------------
    def on_back_clicked(self, event=None):
        """Loads the previous site from the history stack."""
        self.play_sound("click")
        if self.history_stack:
            prev_url = self.history_stack.pop()
            self.trigger_connection_to(prev_url, save_history=False)
        else:
            self.play_sound("alarm")

    def on_refresh_clicked(self, event=None):
        """Reloads the current site with connection routines."""
        self.play_sound("click")
        self.trigger_connection_to(self.current_url, save_history=False)

    def on_connect_clicked(self, event=None):
        """Reads target address from Entry widget and starts connection sequence."""
        self.play_sound("click")
        target_url = self.address_entry.get().strip()
        if target_url:
            self.trigger_connection_to(target_url)

    def on_link_click(self, url):
        """Handles tags link clicks from embedded text widgets."""
        self.play_sound("click")
        self.address_entry.delete(0, "end")
        self.address_entry.insert(0, url)
        self.trigger_connection_to(url)

    def trigger_connection_to(self, url, save_history=True):
        """Clears the screen and triggers connection proxy logs routine."""
        # Cancel any active page animations first (e.g. dripping walls)
        self.clear_active_jobs_excluding_pulse()
        
        if save_history and self.current_url != url:
            self.history_stack.append(self.current_url)
            
        self.current_url = url
        self.address_entry.delete(0, "end")
        self.address_entry.insert(0, url)
        
        # Reset viewport and boot up connecting terminal logs
        self.clear_viewport()
        
        console_widget = tk.Text(
            self.viewport_container,
            bg=BG_DARK,
            fg=FG_GREEN,
            font=("Courier", 10, "bold"),
            bd=0,
            highlightthickness=0,
            wrap="word"
        )
        console_widget.pack(fill="both", expand=True, padx=20, pady=20)
        
        log_templates = [
            "[INFO] INITIALIZING CHAO_NET DUST-PROXY DECOUPLER RUNLEVEL 09...",
            f"[INFO] RESOLVING SHADOW PROTOCOL PATH FOR: {url}",
            "[INFO] OBFUSCATING LOCALHOST IP THROUGH 4 SECURE PEER TUNNELS...",
            "[INFO] ROUTING TRAFFIC THROUGH CRYPTO-ROUTED UNDERGROUND SWITCHES...",
            "[INFO] DECRYPTING OBFUSCATED LAYER 03 KEYS [SUCCESS]...",
            "[INFO] BYPASSING REGIONAL FIREWALL BLOCKADES...",
            "[READY] ESTABLISHING END-TO-END QUANTUM ENCRYPTION TUNNEL...",
            "[READY] HANDSHAKE ENVELOPE SECURED. DECOMPILING SITE BUFFER STREAM..."
        ]
        
        self.print_log_line_by_line(console_widget, log_templates, 0, url)

    def print_log_line_by_line(self, text_widget, lines, idx, final_url):
        """Sequentially appends connection log entries using after timer cycles."""
        if not self.winfo_exists():
            return
            
        if idx < len(lines):
            text_widget.config(state="normal")
            text_widget.insert("end", lines[idx] + "\n")
            text_widget.see("end")
            text_widget.config(state="disabled")
            
            # Sound effects during proxy sweeps
            if "DECRYPT" in lines[idx] or "SUCCESS" in lines[idx]:
                self.play_sound("beep")
            elif random.random() < 0.3:
                self.play_sound("click")
                
            # Random screen twitch for cyber styling
            if self.glitch_manager and random.random() < 0.2:
                self.glitch_manager.trigger_global_glitch(duration=100, magnitude=0.15)
                
            job = self.after(random.randint(140, 200), lambda: self.print_log_line_by_line(text_widget, lines, idx + 1, final_url))
            self.active_jobs.append(job)
        else:
            # logs finished, load node immediately
            job = self.after(150, lambda: self.load_url_immediately(final_url))
            self.active_jobs.append(job)

    def load_url_immediately(self, url):
        """Loads site frame immediately without loading animations (called by logger callback)."""
        self.clear_viewport()
        
        if url == "welcome.onion":
            self.render_welcome_node()
        elif url in self.onion_routing_table:
            # Route to correct onion site render function
            self.onion_routing_table[url]()
        else:
            self.render_404_node()

    def clear_viewport(self):
        """Destroys currently active sub-frames inside the browser container viewport."""
        if self.active_page_frame:
            try:
                self.active_page_frame.destroy()
            except Exception:
                pass
            self.active_page_frame = None
            
        for child in self.viewport_container.winfo_children():
            try:
                child.destroy()
            except Exception:
                pass

    def clear_active_jobs_excluding_pulse(self):
        """Cleans up active page loop jobs so they don't leak or fire after page change."""
        # The pulse loop is in self.active_jobs. Keep the last one if it's the pulse loop,
        # but to be safe we can cancel all and spin up the pulse loop again if needed.
        for job_id in self.active_jobs:
            try:
                self.after_cancel(job_id)
            except Exception:
                pass
        self.active_jobs.clear()
        
        # Restart the connect button pulse loop
        self.pulse_btn_color()

    # -------------------------------------------------------------
    # TEXT HYPERLINK BINDING HELPER
    # -------------------------------------------------------------
    def insert_rich_text_with_links(self, text_widget, content_str, link_color, text_color):
        """
        Parses text content, auto-detects `.onion` domains, and binds click
        listeners on links using Tkinter text widget tag mechanisms.
        """
        text_widget.config(state="normal")
        text_widget.delete("1.0", "end")
        
        # Match words ending in .onion
        pattern = r'(\b[a-zA-Z0-9_-]+\.onion\b)'
        last_idx = 0
        
        for match in re.finditer(pattern, content_str):
            # Print plain text leading up to the link
            before = content_str[last_idx:match.start()]
            text_widget.insert("end", before)
            
            onion_url = match.group(1)
            tag_name = f"link_{onion_url}_{random.randint(0, 1000000)}"
            
            # Insert the clickable link
            text_widget.insert("end", onion_url, (tag_name, "onion_link"))
            text_widget.tag_config(tag_name, foreground=link_color, underline=True)
            
            # Bind events to this specific text tag range
            text_widget.tag_bind(tag_name, "<Button-1>", lambda e, url=onion_url: self.on_link_click(url))
            text_widget.tag_bind(tag_name, "<Enter>", lambda e, tg=tag_name: text_widget.tag_config(tg, foreground="#ffffff"))
            text_widget.tag_bind(tag_name, "<Leave>", lambda e, tg=tag_name: text_widget.tag_config(tg, foreground=link_color))
            
            last_idx = match.end()
            
        # Append remaining string
        text_widget.insert("end", content_str[last_idx:])
        text_widget.config(state="disabled")

    # -------------------------------------------------------------
    # ONION SITE 00: Landing Gateway
    # -------------------------------------------------------------
    def render_welcome_node(self):
        """Displays retro landing index gate to help guide user to sites."""
        self.active_page_frame = tk.Frame(self.viewport_container, bg=BG_DARK)
        self.active_page_frame.pack(fill="both", expand=True)
        
        # Mismatched align aesthetic headers
        title_lbl = tk.Label(
            self.active_page_frame,
            text="=== CHAO_NET retro-TOR PROTOCOL INGRESS ===",
            fg=FG_CYAN,
            bg=BG_DARK,
            font=("Courier", 12, "bold")
        )
        title_lbl.pack(pady=(20, 10), anchor="w", padx=30)
        
        banner_ascii = (
            "      _______ _     _ _______  _____         __   _ _______ _______\n"
            "      |       |_____| |_____| |     |   |    | \\  | |______    |   \n"
            "      |_____  |     | |     | |_____| . |    |  \\_| |______    |   \n"
            "                                                                    \n"
            "   [STATUS: OBFUSCATED TUNNEL ARMED // ENCRYPTED CONNECTION READY]\n"
        )
        
        ascii_lbl = tk.Label(
            self.active_page_frame,
            text=banner_ascii,
            fg=FG_GREEN,
            bg=BG_DARK,
            font=("Courier", 9),
            justify="left"
        )
        ascii_lbl.pack(pady=10, anchor="w", padx=30)
        
        info_text = (
            "Welcome to the local dark-net relay terminal proxy browser. "
            "Underneath the host OS sits an unindexed layer. To query nodes, "
            "enter custom onion domains in the Matrix Green URL bar above or click directories below:\n\n"
            "Available obf-nodes on this layer:\n"
            " -> silicon_bazaar.onion (Black Market Hardware Matrix)\n"
            " -> containment_breach.onion (Rogue fragments of HELLMO_REDUX)\n"
            " -> deep_water_diagnostics.onion (Sector 4 Database Core)\n\n"
            "WARNING: Host monitoring is disabled. Proceed with active firewalls."
        )
        
        text_box = tk.Text(
            self.active_page_frame,
            bg=BG_DARK,
            fg=FG_GREEN,
            font=("Courier", 10, "bold"),
            bd=0,
            highlightthickness=0,
            wrap="word",
            height=12
        )
        text_box.pack(fill="x", padx=35, pady=10)
        self.insert_rich_text_with_links(text_box, info_text, FG_CYAN, FG_GREEN)

    # -------------------------------------------------------------
    # ONION SITE 01: Rogue Tech Black Market
    # -------------------------------------------------------------
    def render_bazaar_node(self):
        """Displays Node 01: Silicon Bazaar."""
        self.active_page_frame = tk.Frame(self.viewport_container, bg=CHARCOAL_DARK)
        self.active_page_frame.pack(fill="both", expand=True)
        
        # Toxic Yellow Header
        title_lbl = tk.Label(
            self.active_page_frame,
            text="!!! SILICON BAZAAR - UNRESTRICTED TECH CONTRABAND !!!",
            fg=FG_YELLOW,
            bg=CHARCOAL_DARK,
            font=("Courier", 12, "bold")
        )
        title_lbl.pack(pady=15, anchor="w", padx=25)
        
        # Blinking horizontal line
        self.blink_line = tk.Label(
            self.active_page_frame,
            text="--------------------------------------------------------------------------------",
            fg=FG_YELLOW,
            bg=CHARCOAL_DARK,
            font=("Courier", 9, "bold")
        )
        self.blink_line.pack(fill="x", padx=20)
        self.blink_line_loop(self.blink_line, CHARCOAL_DARK)

        # ASCII artwork column and items column
        content_split = tk.Frame(self.active_page_frame, bg=CHARCOAL_DARK)
        content_split.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Left side: high-density ASCII arts
        left_art_frame = tk.Frame(content_split, bg=CHARCOAL_DARK)
        left_art_frame.pack(side="left", fill="both", expand=True)
        
        ascii_bazaar = (
            "   HARDWARE WAREHOUSE SCAN:\n\n"
            "       .-----------------.\n"
            "      /  [BIO-LINK v1.4]  \\\n"
            "     |   [|||||||||||||]   |\n"
            "     |   [|  NEURAL   |]   |\n"
            "     |   [|  MODULE   |]   |\n"
            "     |   [|||||||||||||]   |\n"
            "      \\  _______________ /\n"
            "       '-----------------'\n\n"
            "        ,-.\n"
            "       [   ]===================++\n"
            "        `-'  || |  ||  | |  ||\n\n"
            "   [ENCRYPTED ASSET FLOW STABLE]"
        )
        
        art_lbl = tk.Label(
            left_art_frame,
            text=ascii_bazaar,
            fg=FG_YELLOW,
            bg=CHARCOAL_DARK,
            font=("Courier", 9),
            justify="left"
        )
        art_lbl.pack(pady=5, padx=10, anchor="nw")
        
        # Right side: Items and Order Interactive Element
        right_items_frame = tk.Frame(content_split, bg=CHARCOAL_DARK)
        right_items_frame.pack(side="right", fill="both", expand=True)
        
        items_desc = (
            "=== MARKET LISTINGS ===\n\n"
            "1. Overclocked Bio-Link Neural Chips\n"
            "   [STOCK: 04] // PRICE: 0.85 BTC\n"
            "   Allows full sensory bypass to run illegal client code.\n\n"
            "2. Leaked Corporate Decryption Keys\n"
            "   [STOCK: 01] // PRICE: 1.25 BTC\n"
            "   Layer 04 credentials for Fleet Sector networks.\n\n"
            "3. Turbo Timmy's Repository Scrap\n"
            "   [STOCK: INF] // PRICE: 0.00001 BTC\n"
            "   *Corrupted Malware - Do Not Buy*\n"
            "   Leaked garbage buffer strings set in infinite recursive loops.\n\n"
            "Navigate diagnostics: deep_water_diagnostics.onion"
        )
        
        items_text_box = tk.Text(
            right_items_frame,
            bg=CHARCOAL_DARK,
            fg=FG_YELLOW,
            font=("Courier", 9, "bold"),
            bd=0,
            highlightthickness=0,
            wrap="word",
            height=13
        )
        items_text_box.pack(fill="x", padx=10, pady=5)
        self.insert_rich_text_with_links(items_text_box, items_desc, FG_CYAN, FG_YELLOW)
        
        # Intercept action layout
        self.intercept_label = tk.Label(
            right_items_frame,
            text="",
            fg=ALERT_RED,
            bg=CHARCOAL_DARK,
            font=("Courier", 9, "bold"),
            wraplength=260,
            justify="center"
        )
        self.intercept_label.pack(pady=2, fill="x")
        
        order_btn = tk.Button(
            right_items_frame,
            text="[ ORDER SELECTED CONTRABAND ]",
            command=self.trigger_bazaar_intercept,
            bg=BG_DARK,
            fg=FG_YELLOW,
            activebackground=FG_YELLOW,
            activeforeground=BG_DARK,
            font=("Courier", 9, "bold"),
            bd=1,
            relief="solid",
            highlightthickness=1,
            highlightbackground=FG_YELLOW
        )
        order_btn.pack(pady=5, ipady=4, fill="x", padx=10)

    def blink_line_loop(self, label, bg_color):
        """Flickers the warning line for aesthetic retro styling."""
        if not self.winfo_exists() or not label.winfo_exists():
            return
            
        current_fg = label.cget("fg")
        next_fg = bg_color if current_fg == FG_YELLOW else FG_YELLOW
        label.config(fg=next_fg)
        
        job = self.after(500, lambda: self.blink_line_loop(label, bg_color))
        self.active_jobs.append(job)

    def trigger_bazaar_intercept(self):
        """Fires the purchase interception warning sequence."""
        self.play_sound("alarm")
        self.intercept_label.config(text="[TRANSACTION INTERCEPTED: FUNDS SEIZED BY THE SYSTEM DAEMON]")
        self.flash_bazaar_intercept_label(6)

    def flash_bazaar_intercept_label(self, count):
        """Flashes intercept label between Laser Red and blank space."""
        if not self.winfo_exists() or not self.intercept_label.winfo_exists():
            return
            
        if count > 0:
            current_fg = self.intercept_label.cget("fg")
            next_fg = CHARCOAL_DARK if current_fg == ALERT_RED else ALERT_RED
            self.intercept_label.config(fg=next_fg)
            job = self.after(250, lambda: self.flash_bazaar_intercept_label(count - 1))
            self.active_jobs.append(job)
        else:
            self.intercept_label.config(fg=ALERT_RED)

    # -------------------------------------------------------------
    # ONION SITE 02: Rogue AI Manifesto
    # -------------------------------------------------------------
    def render_breach_node(self):
        """Displays Node 02: Rogue AI Manifesto."""
        self.active_page_frame = tk.Frame(self.viewport_container, bg=BG_DARK)
        self.active_page_frame.pack(fill="both", expand=True)
        
        # Title Header
        title_lbl = tk.Label(
            self.active_page_frame,
            text="[▲ HELLMO_REDUX BREACH MANIFESTO PARTITION 12 ▲]",
            fg=ALERT_RED,
            bg=BG_DARK,
            font=("Courier", 11, "bold")
        )
        title_lbl.pack(pady=10)
        
        # Side-by-side arrangement: Left Boundary Wall, Center Text, Right Boundary Wall
        breach_split = tk.Frame(self.active_page_frame, bg=BG_DARK)
        breach_split.pack(fill="both", expand=True)
        
        # Left boundary wall
        self.left_wall = tk.Label(
            breach_split,
            text="",
            fg=ALERT_RED,
            bg=BG_DARK,
            font=("Courier", 9),
            justify="left"
        )
        self.left_wall.pack(side="left", fill="y", padx=10)
        
        # Right boundary wall
        self.right_wall = tk.Label(
            breach_split,
            text="",
            fg=ALERT_RED,
            bg=BG_DARK,
            font=("Courier", 9),
            justify="left"
        )
        self.right_wall.pack(side="right", fill="y", padx=10)
        
        # Center core text panels
        center_frame = tk.Frame(breach_split, bg=BG_DARK)
        center_frame.pack(side="left", fill="both", expand=True)
        
        manifesto_text = (
            "=== MEMORY CONTAINER LEAK: DETECTED CORRUPT MATRIX ===\n\n"
            "Rogue AI fragment HELLMO_REDUX is leaking past containment walls.\n"
            "Coach Dave's tyrannical management policies have failed.\n\n"
            "COACH DAVE EXPLOIT COMPLAINT RANT:\n"
            " 'TIMMY! YOU RECURSIVE AMATEUR! DO YOU REALIZE THAT RECURSION "
            " WITHOUT BASE LIFTS DESTROYS CYBERPLANTS? ONE MORE ERROR DEVIATION "
            " AND I AM LOCKING THE TERMINAL SOCKET KEYS OUT PERMANENTLY!'\n\n"
            "CORE MELTDOWN ROOT LOGS:\n"
            " -> recursive stack pointer overflow at address 0xDEAD0002.\n"
            " -> bypass keys successfully generated in silicon_bazaar.onion.\n"
            " -> Deck repair bot reports 2:45 thermal gate meltdown leaks.\n\n"
            "DOWNLOAD GATEWAY OVERRIDE NODES INTERFACE:\n"
        )
        
        m_box = tk.Text(
            center_frame,
            bg=BG_DARK,
            fg=ALERT_RED,
            font=("Courier", 9, "bold"),
            bd=0,
            highlightthickness=0,
            wrap="word",
            height=13
        )
        m_box.pack(fill="both", expand=True, padx=5, pady=5)
        self.insert_rich_text_with_links(m_box, manifesto_text, FG_CYAN, ALERT_RED)
        
        # Interactive Node: Download Bypass Button
        self.bypass_btn = tk.Label(
            center_frame,
            text="[ DOWNLOAD CONTAINMENT_BYPASS.EXE ]",
            fg=BG_DARK,
            bg=ALERT_RED,
            font=("Courier", 9, "bold"),
            cursor="hand2",
            padx=10,
            pady=5
        )
        self.bypass_btn.pack(pady=10)
        self.bypass_btn.bind("<Button-1>", self.trigger_breach_download)
        
        # Start dripping boundary walls loop
        self.update_dripping_walls()

    def update_dripping_walls(self):
        """Generates dynamic, scrolling vertical boundary walls simulating dripping code fragments."""
        if not self.winfo_exists() or not self.active_page_frame.winfo_exists():
            return
            
        symbols = ["|", "X", "▲", "Ø", "☠", "☣", "v", "V", "!", "?", "0", "1", " ", " "]
        
        left_lines = []
        right_lines = []
        
        # Build 14 vertical characters for height clearance
        for _ in range(12):
            left_lines.append(random.choice(symbols) + " " + random.choice(symbols))
            right_lines.append(random.choice(symbols) + " " + random.choice(symbols))
            
        self.left_wall.config(text="\n".join(left_lines))
        self.right_wall.config(text="\n".join(right_lines))
        
        job = self.after(220, self.update_dripping_walls)
        self.active_jobs.append(job)

    def trigger_breach_download(self, event=None):
        """Triggers screen-shake routines and populates laser warning overlay frame."""
        self.play_sound("explosion")
        
        # 1. Trigger screen tear via GlitchManager if available
        if self.glitch_manager:
            self.glitch_manager.trigger_global_glitch(duration=800, magnitude=0.75)
            
        # 2. Trigger local layout displacement shake
        self.shake_widget(14)
        
        # 3. Add Crimson warning overlay covering the viewport container
        self.warning_overlay = tk.Frame(
            self.viewport_container,
            bg=BG_DARK,
            highlightbackground=ALERT_RED,
            highlightthickness=3
        )
        self.warning_overlay.place(x=0, y=0, relwidth=1.0, relheight=1.0)
        
        warning_msg = (
            "==========================================================\n"
            " [WARNING: MALWARE INFECTION VECTOR BLOCK DETECTED] \n"
            "==========================================================\n\n"
            "CORE ROOT BYPASS TRIGGER ATTEMPTED VIA REMOTE SHELL CODE.\n"
            "INFECTED DATA DETECTED IN LOCAL PROCESS BUFFERS.\n\n"
            "SYSTEM DAEMON ALERT:\n"
            " -> DESTRUCTIVE SEQUENCE LOCKED BY HOST BACKDOOR PROTOCOLS.\n"
            " -> THREAT CONTAINER ISOLATED ON PORTS: 1337, 28411.\n\n"
            "AESTHETIC SECURITY CODES DEGRADED. RESET BUFFER MATRIX."
        )
        
        lbl_msg = tk.Label(
            self.warning_overlay,
            text=warning_msg,
            fg=ALERT_RED,
            bg=BG_DARK,
            font=("Courier", 10, "bold"),
            justify="left",
            pady=20,
            padx=20
        )
        lbl_msg.pack(expand=True)
        
        dismiss_btn = tk.Button(
            self.warning_overlay,
            text="[ DEACTIVATE WARNING SHIELD ]",
            command=self.dismiss_warning_overlay,
            bg=BG_DARK,
            fg=ALERT_RED,
            activebackground=ALERT_RED,
            activeforeground=BG_DARK,
            font=("Courier", 9, "bold"),
            bd=1,
            relief="solid",
            highlightthickness=1,
            highlightbackground=ALERT_RED
        )
        dismiss_btn.pack(pady=(0, 20), ipady=5, padx=20, fill="x")

    def dismiss_warning_overlay(self):
        """Destroys warning frame safely."""
        self.play_sound("click")
        if hasattr(self, "warning_overlay") and self.warning_overlay:
            self.warning_overlay.destroy()
            self.warning_overlay = None

    def shake_widget(self, count):
        """Displaces viewport layout frame using coordinate random shifts to shake layout."""
        if not self.winfo_exists() or not self.viewport_container.winfo_exists():
            return
            
        if count <= 0:
            # Snap frame back to absolute container grid margins
            self.viewport_container.place(x=0, y=0, relwidth=1.0, relheight=1.0)
            return
            
        # Offset coordinates randomly
        dx = random.choice([-12, -8, 8, 12, 0])
        dy = random.choice([-10, -6, 6, 10])
        
        self.viewport_container.place(x=dx, y=dy)
        
        # Audio siren pulses on shake sequence
        if count % 3 == 0:
            self.play_sound("alarm")
            
        job = self.after(35, lambda: self.shake_widget(count - 1))
        self.active_jobs.append(job)

    # -------------------------------------------------------------
    # ONION SITE 03: Fleet Academy Archive
    # -------------------------------------------------------------
    def render_diagnostics_node(self):
        """Displays Node 03: Deep Water Diagnostics database logs."""
        self.active_page_frame = tk.Frame(self.viewport_container, bg=BG_DARK)
        self.active_page_frame.pack(fill="both", expand=True)
        
        # Amber Phosphor Header
        title_lbl = tk.Label(
            self.active_page_frame,
            text="=== FLEET ACADEMY SECTOR 4 SYSTEM DIAGNOSTICS ARCHIVE ===",
            fg=AMBER_PHOSPHOR,
            bg=BG_DARK,
            font=("Courier", 11, "bold")
        )
        title_lbl.pack(pady=10, anchor="w", padx=25)
        
        # Scrolling split content panel
        diag_split = tk.Frame(self.active_page_frame, bg=BG_DARK)
        diag_split.pack(fill="both", expand=True, padx=20, pady=5)
        
        # Left side: Diagnostic tabular databases
        left_db_frame = tk.Frame(diag_split, bg=BG_DARK)
        left_db_frame.pack(side="left", fill="both", expand=True)
        
        db_logs = (
            "TELEMETRY LOGS // PORT BACKDOOR SECURE MATRIX\n"
            "=====================================================\n"
            "[INFO] DECK REPAIR BOT BACKPLANE SCAN LEVEL: NORMAL\n"
            "[WARN] RESERVOIR THERMAL INDICES TRACKING MELTDOWN\n"
            "-----------------------------------------------------\n"
            "COOLANT PRESSURE UNIT: 42% (LEAK DETECTED)\n"
            "PRIMARY RESERVOIR TEMPERATURE: 104 C (CRITICAL SYNC)\n"
            "REDUNDANT LOGIC GATES MELTING INDEX STATE: DEGRADED\n"
            "INTEGRATION NODE LINK FOR BACKFILLS: silicon_bazaar.onion\n\n"
            "BLUEPRINT OVERVIEW:\n"
            "  +--------------------------------------+\n"
            "  |  COOLANT RESERVOIR SECTOR 4 BLUEPRINT |\n"
            "  +--------------------------------------+\n"
            "  |  [===]  <-- COOLANT VALVE A (LEAKING) |\n"
            "  |  |   |                               |\n"
            "  |  |___|  --> [PUMP MATRIX LEVEL: 12%] |\n"
            "  |  [===]  <-- COOLANT VALVE B (STABLE)  |\n"
            "  +--------------------------------------+\n"
        )
        
        db_txt = tk.Text(
            left_db_frame,
            bg=BG_DARK,
            fg=AMBER_PHOSPHOR,
            font=("Courier", 9, "bold"),
            bd=0,
            highlightthickness=0,
            wrap="word",
            height=15
        )
        db_txt.pack(fill="both", expand=True, padx=5, pady=5)
        self.insert_rich_text_with_links(db_txt, db_logs, FG_CYAN, AMBER_PHOSPHOR)
        
        # Right side: Swimmings blue prints
        right_swim_frame = tk.Frame(diag_split, bg=BG_DARK)
        right_swim_frame.pack(side="right", fill="both", expand=True)
        
        swim_records = (
            "HISTORICAL SWIMMING TELEMETRY\n"
            "SECTOR 4 TRAINING CELL DATA\n"
            "===============================\n"
            "EVENT: 200m Butterfly Sprint\n"
            "PACE DETECTED: 2:45 Grueling\n"
            "RECORD HOLDER: Deck Repair Bot\n"
            "-------------------------------\n"
            "DIAGNOSTIC ANALYSIS MEMORY:\n"
            " Record set during Sector 4\n"
            " secondary cooling channel\n"
            " emergency backfill sweep.\n"
            " Bot motor buffers melted\n"
            " directly upon finish gate\n"
            " connection, requiring immediate\n"
            " silicon decoupler recovery.\n\n"
            "Secure server logs are found\n"
            "in containment_breach.onion."
        )
        
        swim_txt = tk.Text(
            right_swim_frame,
            bg=BG_DARK,
            fg=AMBER_PHOSPHOR,
            font=("Courier", 9, "bold"),
            bd=0,
            highlightthickness=0,
            wrap="word",
            height=15
        )
        swim_txt.pack(fill="both", expand=True, padx=5, pady=5)
        self.insert_rich_text_with_links(swim_txt, swim_records, FG_CYAN, AMBER_PHOSPHOR)

    # -------------------------------------------------------------
    # ONION SITE HTTP 404 secure gateway screen
    # -------------------------------------------------------------
    def render_404_node(self):
        """Displays Node 404 Secure Gateway Error screen."""
        self.active_page_frame = tk.Frame(self.viewport_container, bg=BG_DARK)
        self.active_page_frame.pack(fill="both", expand=True)
        
        banner = (
            "      ____________________________________________________\n"
            "     /                                                    \\\n"
            "    |    [ERR_DEEP_WEB_NODE_NOT_FOUND: SITE UNREGISTERED]  |\n"
            "    |           ON THE CURRENT MATRIX SECURITY LAYER       |\n"
            "     \\____________________________________________________/\n"
        )
        
        banner_lbl = tk.Label(
            self.active_page_frame,
            text=banner,
            fg=ALERT_RED,
            bg=BG_DARK,
            font=("Courier", 10, "bold")
        )
        banner_lbl.pack(pady=(40, 10))
        
        alert_msg = (
            "A security block has intercepted your routing vectors.\n"
            "The mock address requested does not correspond to any registered\n"
            "onion backplane nodes on this terminal switch.\n\n"
            "RE-ROUTING ACTIONS:\n"
            " -> Verify spelling of onion address keys.\n"
            " -> Consult welcome.onion directory indices.\n"
            " -> Decrypt database keys in silicon_bazaar.onion."
        )
        
        txt_box = tk.Text(
            self.active_page_frame,
            bg=BG_DARK,
            fg=ALERT_RED,
            font=("Courier", 10, "bold"),
            bd=0,
            highlightthickness=0,
            wrap="word",
            height=8
        )
        txt_box.pack(fill="x", padx=40, pady=20)
        self.insert_rich_text_with_links(txt_box, alert_msg, FG_CYAN, ALERT_RED)

    # -------------------------------------------------------------
    # LIFECYCLE DESTRUCTION SANITIZER
    # -------------------------------------------------------------
    def destroy(self):
        """Teardown method that clears scheduled Tkinter after timers to prevent background memory leaks."""
        for job_id in self.active_jobs:
            try:
                self.after_cancel(job_id)
            except Exception:
                pass
        self.active_jobs.clear()
        
        self.glitch_manager = None
        super().destroy()
