import os
import math
import struct
import wave
import io
import datetime
import threading
import time
import tkinter as tk
from tkinter import messagebox

# ==============================================================================
# CHIPTUNE NOTES & FREQUENCY MAPPING
# ==============================================================================
NOTE_FREQS = {
    "C3": 130.81, "C#3": 138.59, "D3": 146.83, "D#3": 155.56, "E3": 164.81, "F3": 174.61, "F#3": 185.00, "G3": 196.00, "G#3": 207.65, "A3": 220.00, "A#3": 233.08, "B3": 246.94,
    "C4": 261.63, "C#4": 277.18, "D4": 293.66, "D#4": 311.13, "E4": 329.63, "F4": 349.23, "F#4": 369.99, "G4": 392.00, "G#4": 415.30, "A4": 440.00, "A#4": 466.16, "B4": 493.88,
    "C5": 523.25
}
NOTES = list(NOTE_FREQS.keys())

# Pre-computed 15-bit LFSR pseudo-random noise sequence (65536 states)
NOISE_TABLE = []
_reg = 0x7FFF
for _ in range(65536):
    _bit = (_reg ^ (_reg >> 1)) & 1
    _reg = (_reg >> 1) | (_bit << 14)
    NOISE_TABLE.append(1.0 if (_reg & 1) else -1.0)

# ==============================================================================
# AUDIO WAVEFORM COMPILATION MATH
# ==============================================================================
def generate_step_sound(step_data, step_duration, sample_rate=44100):
    """
    Synthesizes and mixes raw 8-bit chiptune samples for a single step.
    Combiles channels mathematically and exports standard 16-bit PCM WAV bytes in-memory.
    """
    N_s = int(sample_rate * step_duration)
    mixed_samples = [0.0] * N_s
    
    # Channel 1: Pulse (Square) Wave
    if step_data.get(1, {}).get("active", False):
        freq = step_data[1]["note_freq"]
        duty = step_data[1].get("duty", 0.25)
        for i in range(N_s):
            t = i / sample_rate
            phase = (t * freq) % 1.0
            amp = 1.0 if phase < duty else -1.0
            mixed_samples[i] += amp * 0.25
            
    # Channel 2: Triangle Wave
    if step_data.get(2, {}).get("active", False):
        freq = step_data[2]["note_freq"]
        for i in range(N_s):
            t = i / sample_rate
            phase = (t * freq) % 1.0
            if phase < 0.25:
                amp = 4.0 * phase
            elif phase < 0.75:
                amp = 2.0 - 4.0 * phase
            else:
                amp = 4.0 * phase - 4.0
            mixed_samples[i] += amp * 0.35
            
    # Channel 3: LFSR Noise
    if step_data.get(3, {}).get("active", False):
        freq = step_data[3]["note_freq"]
        for i in range(N_s):
            t = i / sample_rate
            # Sampling LFSR noise table at note-specific speed to modulate pitch
            shift_index = int(t * (freq * 15))
            amp = NOISE_TABLE[shift_index % 65536]
            mixed_samples[i] += amp * 0.20
            
    # Channel 4: PCM (Low-Bitrate Sample Modulator)
    if step_data.get(4, {}).get("active", False):
        pcm_type = step_data[4].get("pcm_type", "LASER")
        for i in range(N_s):
            t = i / sample_rate
            if pcm_type == "LASER":
                # Closed-form integration of exponential frequency sweep
                # f(t) = f0 * a^(t/D) where f0=600Hz, a=0.05
                ln_a = -2.995732273553991
                phase_val = 2.0 * math.pi * 600.0 * step_duration * ((0.05 ** (t / step_duration)) - 1.0) / ln_a
                amp = math.sin(phase_val)
                # Bit crush to 4-bit amplitude resolution (16 steps)
                amp = round(amp * 8) / 8
            else:
                # METAL CRUSH: Carrier ring modulated with LFO, crushed to 3-bit resolution (8 steps)
                carrier = math.sin(2.0 * math.pi * 440.0 * t)
                modulator = math.sin(2.0 * math.pi * 8.0 * t)
                amp = carrier * modulator
                amp = round(amp * 4) / 4
            mixed_samples[i] += amp * 0.30
            
    # Compile raw mono sample frames and clip to prevent buffer overflow
    byte_frames = []
    for s in mixed_samples:
        val = max(-1.0, min(1.0, s))
        int_val = int(val * 32767)
        byte_frames.append(struct.pack('<h', int_val))
        
    wav_io = io.BytesIO()
    with wave.open(wav_io, 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(b''.join(byte_frames))
        
    return wav_io.getvalue()

# ==============================================================================
# OBJECT-ORIENTED TRACKER PANEL COMPONENT
# ==============================================================================
class ChiptuneTrackerPanel(tk.Frame):
    def __init__(self, parent, glitch_manager=None):
        super().__init__(parent, bg="#000000")
        self.glitch_manager = glitch_manager
        
        # Playback Clock state variables
        self.is_playing = False
        self.current_step = 0
        self.bpm = 120
        self.playback_thread = None
        self.play_channel = None
        
        # Channels settings
        self.pulse_duty = 0.25
        self.pcm_type = "LASER"
        
        # State brush
        self.brush_note = tk.StringVar(value="C4")
        
        # Decoupled matrix state: 4 channels over 16 steps
        self.tracker_state = []
        for ch in range(4):
            ch_steps = []
            for step in range(16):
                ch_steps.append({
                    "active": False,
                    "note": "C4"
                })
            self.tracker_state.append(ch_steps)
            
        # Cyber-terminal styling codes
        self.BG_DARK = "#000000"
        self.BG_PANEL = "#0b0b0b"
        self.FG_GREEN = "#00ff00"
        self.FG_MAGENTA = "#ff00ff"
        self.FG_CYAN = "#00ffff"
        self.FG_YELLOW = "#ffff00"
        self.ALERT_RED = "#ff0000"
        
        self.build_ui()
        self.init_audio_system()
        
    def init_audio_system(self):
        """Pre-initializes the Pygame mixer driver for real-time playbacks."""
        try:
            import pygame
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=1024)
            # Safe channel select
            self.play_channel = pygame.mixer.Channel(1)
        except Exception as e:
            print(f"[ChiptuneTrackerPanel] Audio init warning: {e}")

    def build_ui(self):
        # Master grid settings
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0) # Header
        self.rowconfigure(1, weight=1) # Sequencer Grid
        self.rowconfigure(2, weight=0) # Control Dashboard
        self.rowconfigure(3, weight=0) # Status Banner
        
        # 1. Title Header Bar
        header_frame = tk.Frame(self, bg=self.BG_DARK)
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(5, 5))
        
        title_lbl = tk.Label(header_frame, text="CHIPTUNE TRACKER MATRIX CORE v1.0", fg=self.FG_CYAN, bg=self.BG_DARK, font=("Courier", 12, "bold"))
        title_lbl.pack(side="left")
        
        specs_lbl = tk.Label(header_frame, text="[ 44100Hz // 16-BIT // MONO PCM SYNTH ]", fg=self.FG_YELLOW, bg=self.BG_DARK, font=("Courier", 9, "bold"))
        specs_lbl.pack(side="right")
        
        # 2. Main Sequencer Canvas
        self.grid_canvas = tk.Canvas(self, width=780, height=200, bg=self.BG_DARK, highlightthickness=1, highlightbackground=self.FG_MAGENTA)
        self.grid_canvas.grid(row=1, column=0, padx=10, pady=5, sticky="n")
        self.grid_canvas.bind("<Button-1>", self.on_grid_click)
        
        # 3. Control Dashboard
        control_frame = tk.Frame(self, bg=self.BG_PANEL, highlightthickness=1, highlightbackground="#222222")
        control_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        
        for col_idx in range(4):
            control_frame.columnconfigure(col_idx, weight=1)
            
        # --- Column 1: Transport commands
        col1_frame = tk.Frame(control_frame, bg=self.BG_PANEL)
        col1_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        tk.Label(col1_frame, text="TRANSPORT COMMANDS", fg=self.FG_YELLOW, bg=self.BG_PANEL, font=("Courier", 9, "bold")).pack(anchor="w", pady=(0, 5))
        
        self.btn_play = tk.Button(col1_frame, text="[ PLAY SEQUENCE ]", command=self.start_playback,
                                  bg=self.BG_DARK, fg=self.FG_GREEN, activebackground=self.FG_GREEN, activeforeground=self.BG_DARK,
                                  font=("Courier", 9, "bold"), bd=1, relief="flat", highlightbackground=self.FG_GREEN)
        self.btn_play.pack(fill="x", pady=2)
        
        btn_stop = tk.Button(col1_frame, text="[ STOP SEQUENCE ]", command=self.stop_playback,
                             bg=self.BG_DARK, fg=self.ALERT_RED, activebackground=self.ALERT_RED, activeforeground=self.BG_DARK,
                             font=("Courier", 9, "bold"), bd=1, relief="flat", highlightbackground=self.ALERT_RED)
        btn_stop.pack(fill="x", pady=2)
        
        btn_clear = tk.Button(col1_frame, text="[ WIPE SEQUENCE ]", command=self.clear_sequence,
                              bg=self.BG_DARK, fg=self.FG_MAGENTA, activebackground=self.FG_MAGENTA, activeforeground=self.BG_DARK,
                              font=("Courier", 9, "bold"), bd=1, relief="flat", highlightbackground=self.FG_MAGENTA)
        btn_clear.pack(fill="x", pady=2)
        
        # --- Column 2: Sequencer parameter modifications
        col2_frame = tk.Frame(control_frame, bg=self.BG_PANEL)
        col2_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        tk.Label(col2_frame, text="TEMPO & BPM CONTROL", fg=self.FG_YELLOW, bg=self.BG_PANEL, font=("Courier", 9, "bold")).pack(anchor="w", pady=(0, 5))
        
        self.bpm_scale = tk.Scale(col2_frame, from_=40, to=240, orient="horizontal", bg=self.BG_PANEL, fg=self.FG_CYAN,
                                  troughcolor=self.BG_DARK, highlightthickness=0, font=("Courier", 8),
                                  activebackground=self.FG_CYAN, resolution=1)
        self.bpm_scale.set(120)
        self.bpm_scale.pack(fill="x", pady=2)
        
        # Brush note selection optionbox
        brush_frame = tk.Frame(col2_frame, bg=self.BG_PANEL)
        brush_frame.pack(fill="x", pady=5)
        tk.Label(brush_frame, text="PITCH BRUSH:", fg=self.FG_GREEN, bg=self.BG_PANEL, font=("Courier", 9, "bold")).pack(side="left")
        
        self.brush_menu = tk.OptionMenu(brush_frame, self.brush_note, *NOTES, command=self.on_brush_change)
        self.brush_menu.config(bg=self.BG_DARK, fg=self.FG_GREEN, activebackground=self.FG_GREEN, activeforeground=self.BG_DARK,
                               font=("Courier", 9, "bold"), bd=1, relief="flat", highlightthickness=0)
        self.brush_menu["menu"].config(bg=self.BG_DARK, fg=self.FG_GREEN, font=("Courier", 9, "bold"))
        self.brush_menu.pack(side="right", fill="x", expand=True, padx=(5, 0))
        
        # --- Column 3: Synthesizer Settings
        col3_frame = tk.Frame(control_frame, bg=self.BG_PANEL)
        col3_frame.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")
        
        tk.Label(col3_frame, text="SYNTH PROFILE", fg=self.FG_YELLOW, bg=self.BG_PANEL, font=("Courier", 9, "bold")).pack(anchor="w", pady=(0, 5))
        
        # Pulse duty cycle selection
        duty_frame = tk.Frame(col3_frame, bg=self.BG_PANEL)
        duty_frame.pack(fill="x", pady=2)
        tk.Label(duty_frame, text="CH1 DUTY:", fg=self.FG_MAGENTA, bg=self.BG_PANEL, font=("Courier", 8, "bold")).pack(side="left")
        
        self.duty_var = tk.StringVar(value="25%")
        self.duty_menu = tk.OptionMenu(duty_frame, self.duty_var, "12.5%", "25%", "50%", command=self.on_duty_change)
        self.duty_menu.config(bg=self.BG_DARK, fg=self.FG_MAGENTA, activebackground=self.FG_MAGENTA, activeforeground=self.BG_DARK,
                              font=("Courier", 8, "bold"), bd=1, relief="flat", highlightthickness=0)
        self.duty_menu["menu"].config(bg=self.BG_DARK, fg=self.FG_MAGENTA, font=("Courier", 8, "bold"))
        self.duty_menu.pack(side="right", fill="x", expand=True, padx=(5, 0))
        
        # PCM synth profile configuration
        pcm_frame = tk.Frame(col3_frame, bg=self.BG_PANEL)
        pcm_frame.pack(fill="x", pady=2)
        tk.Label(pcm_frame, text="CH4 TYPE:", fg=self.ALERT_RED, bg=self.BG_PANEL, font=("Courier", 8, "bold")).pack(side="left")
        
        self.pcm_var = tk.StringVar(value="LASER ZAP")
        self.pcm_menu = tk.OptionMenu(pcm_frame, self.pcm_var, "LASER ZAP", "METAL CRUSH", command=self.on_pcm_change)
        self.pcm_menu.config(bg=self.BG_DARK, fg=self.ALERT_RED, activebackground=self.ALERT_RED, activeforeground=self.BG_DARK,
                             font=("Courier", 8, "bold"), bd=1, relief="flat", highlightthickness=0)
        self.pcm_menu["menu"].config(bg=self.BG_DARK, fg=self.ALERT_RED, font=("Courier", 8, "bold"))
        self.pcm_menu.pack(side="right", fill="x", expand=True, padx=(5, 0))
        
        # --- Column 4: File compile engine
        col4_frame = tk.Frame(control_frame, bg=self.BG_PANEL)
        col4_frame.grid(row=0, column=3, padx=10, pady=10, sticky="nsew")
        
        tk.Label(col4_frame, text="COMPILE ENGINE", fg=self.FG_YELLOW, bg=self.BG_PANEL, font=("Courier", 9, "bold")).pack(anchor="w", pady=(0, 5))
        
        self.btn_export = tk.Button(col4_frame, text="[ EXPORT CHIP_AUDIO ]", command=self.export_audio_action,
                                bg=self.BG_DARK, fg=self.FG_MAGENTA, activebackground=self.FG_MAGENTA, activeforeground=self.BG_DARK,
                                font=("Courier", 9, "bold"), bd=1, relief="flat", highlightbackground=self.FG_MAGENTA, height=2)
        self.btn_export.pack(fill="both", expand=True, pady=2)
        
        # 4. Status Bar
        self.status_bar = tk.Label(self, text="[ STATUS: CORE ACTIVE // STANDBY ]", fg=self.FG_GREEN, bg=self.BG_DARK, font=("Courier", 9, "bold"))
        self.status_bar.grid(row=3, column=0, sticky="ew", pady=(5, 10))
        
        # Initialize canvas graphics
        self.draw_grid()
        
        # Glitch registry hooking
        if self.glitch_manager:
            self.glitch_manager.register_widget(self.grid_canvas, magnitude=0.18)
            self.glitch_manager.register_widget(self.btn_play, magnitude=0.2)
            self.glitch_manager.register_widget(btn_stop, magnitude=0.2)
            self.glitch_manager.register_widget(btn_clear, magnitude=0.2)
            self.glitch_manager.register_widget(self.bpm_scale, magnitude=0.15)
            self.glitch_manager.register_widget(self.brush_menu, magnitude=0.15)
            self.glitch_manager.register_widget(self.duty_menu, magnitude=0.15)
            self.glitch_manager.register_widget(self.pcm_menu, magnitude=0.15)
            self.glitch_manager.register_widget(self.btn_export, magnitude=0.22)
            self.glitch_manager.register_widget(self.status_bar, magnitude=0.15)

    def draw_grid(self):
        """Draws the 4x16 step matrices, highlighting playhead, channel, and node states."""
        self.grid_canvas.delete("all")
        
        X_OFFSET = 120
        Y_OFFSET = 20
        CELL_W = 36
        CELL_H = 36
        SPACING = 4
        
        channel_names = ["CH1: PULSE", "CH2: TRIANGLE", "CH3: NOISE", "CH4: PCM"]
        channel_colors = [self.FG_MAGENTA, self.FG_CYAN, self.FG_YELLOW, self.ALERT_RED]
        
        # Draw labels
        for r in range(4):
            y_mid = Y_OFFSET + r * (CELL_H + SPACING) + CELL_H / 2
            self.grid_canvas.create_text(
                60, y_mid,
                text=channel_names[r],
                fill=channel_colors[r],
                font=("Courier", 10, "bold")
            )
            
        # Draw cells
        for r in range(4):
            for c in range(16):
                x1 = X_OFFSET + c * (CELL_W + SPACING)
                y1 = Y_OFFSET + r * (CELL_H + SPACING)
                x2 = x1 + CELL_W
                y2 = y1 + CELL_H
                
                state = self.tracker_state[r][c]
                is_active = state["active"]
                note_name = state["note"]
                
                if is_active:
                    fill_color = channel_colors[r]
                    outline_color = "#ffffff"
                    text_color = self.BG_DARK
                    text_font = ("Courier", 8, "bold")
                else:
                    # Inactive cell background: alternating shades per beat
                    if (c // 4) % 2 == 1:
                        fill_color = "#121212"
                    else:
                        fill_color = "#070707"
                    outline_color = "#202020"
                    text_color = "#404040"
                    text_font = ("Courier", 7)
                    
                self.grid_canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=fill_color,
                    outline=outline_color,
                    width=1,
                    tags=f"cell_{r}_{c}"
                )
                
                display_text = note_name if is_active else "---"
                self.grid_canvas.create_text(
                    (x1 + x2)/2, (y1 + y2)/2,
                    text=display_text,
                    fill=text_color,
                    font=text_font,
                    tags=f"cell_{r}_{c}"
                )
                
        # Draw playhead scanning overlay column
        if self.is_playing:
            c = self.current_step
            px1 = X_OFFSET + c * (CELL_W + SPACING) - 2
            py1 = Y_OFFSET - 5
            px2 = px1 + CELL_W + 4
            py2 = Y_OFFSET + 4 * (CELL_H + SPACING) - SPACING + 5
            
            self.grid_canvas.create_rectangle(
                px1, py1, px2, py2,
                outline=self.FG_CYAN,
                width=2,
                tags="playhead"
            )

    def on_grid_click(self, event):
        """Handles canvas step clicks to toggle node activations or trigger previews."""
        x = event.x
        y = event.y
        
        X_OFFSET = 120
        Y_OFFSET = 20
        CELL_W = 36
        CELL_H = 36
        SPACING = 4
        
        if X_OFFSET <= x < X_OFFSET + 16 * (CELL_W + SPACING):
            if Y_OFFSET <= y < Y_OFFSET + 4 * (CELL_H + SPACING):
                col = (x - X_OFFSET) // (CELL_W + SPACING)
                row = (y - Y_OFFSET) // (CELL_H + SPACING)
                
                if 0 <= col < 16 and 0 <= row < 4:
                    state = self.tracker_state[row][col]
                    state["active"] = not state["active"]
                    
                    if state["active"]:
                        state["note"] = self.brush_note.get()
                        self.preview_note(row, state["note"])
                    else:
                        self.play_ui_sound("click")
                        
                    self.draw_grid()

    def on_brush_change(self, val):
        self.play_ui_sound("click")
        
    def on_duty_change(self, val):
        self.play_ui_sound("click")
        if val == "12.5%":
            self.pulse_duty = 0.125
        elif val == "25%":
            self.pulse_duty = 0.25
        else:
            self.pulse_duty = 0.5
            
    def on_pcm_change(self, val):
        self.play_ui_sound("click")
        if val == "LASER ZAP":
            self.pcm_type = "LASER"
        else:
            self.pcm_type = "METAL"

    def play_ui_sound(self, name):
        """Helper to invoke parent suite sound effect hooks."""
        try:
            from creative_suite import play_sound_effect
            play_sound_effect(name)
        except Exception:
            pass

    def preview_note(self, row, note_name):
        """Spawns an asynchronous audio thread to preview a synthesized note."""
        try:
            threading.Thread(target=self._play_preview_data, args=(row, note_name), daemon=True).start()
        except Exception:
            pass

    def _play_preview_data(self, row, note_name):
        try:
            freq = NOTE_FREQS[note_name]
            step_data = {}
            if row == 0:
                step_data[1] = {"active": True, "note_freq": freq, "duty": self.pulse_duty}
            elif row == 1:
                step_data[2] = {"active": True, "note_freq": freq}
            elif row == 2:
                step_data[3] = {"active": True, "note_freq": freq}
            elif row == 3:
                step_data[4] = {"active": True, "note_freq": freq, "pcm_type": self.pcm_type}
                
            wav_bytes = generate_step_sound(step_data, 0.15)
            
            import pygame
            import io
            if pygame.mixer.get_init():
                sound = pygame.mixer.Sound(io.BytesIO(wav_bytes))
                sound.set_volume(0.5)
                sound.play()
        except Exception:
            pass

    def clear_sequence(self):
        """Wipes sequencer memory after double confirmation dialogues."""
        self.play_ui_sound("beep")
        proceed = messagebox.askyesno("CONFIRM WIPE", "Wipe all chiptune steps in active memory?")
        if proceed:
            self.play_ui_sound("click")
            for r in range(4):
                for c in range(16):
                    self.tracker_state[r][c]["active"] = False
            self.current_step = 0
            self.draw_grid()
            self.status_bar.config(text="[ STATUS: SEQUENCE PURGED FROM CORE MEMORY ]", fg=self.FG_GREEN)
            self.after(2000, lambda: self.status_bar.config(text="[ STATUS: CORE ACTIVE // STANDBY ]", fg=self.FG_GREEN))

    def start_playback(self):
        if self.is_playing:
            return
        self.play_ui_sound("click")
        self.is_playing = True
        self.btn_play.config(bg=self.FG_GREEN, fg=self.BG_DARK, text="[ SEQUENCER RUNNING ]")
        self.status_bar.config(text="[ STATUS: SEQUENCER ACTIVE // PLAYBACK ONLINE ]", fg=self.FG_GREEN)
        
        self.playback_thread = threading.Thread(target=self.playback_loop, daemon=True)
        self.playback_thread.start()
        
    def stop_playback(self):
        if not self.is_playing:
            return
        self.play_ui_sound("click")
        self.is_playing = False
        
        # Prevent thread join deadlocks
        try:
            if self.playback_thread and self.playback_thread.is_alive():
                self.playback_thread.join(timeout=0.1)
        except Exception:
            pass
            
        self.current_step = 0
        self.btn_play.config(bg=self.BG_DARK, fg=self.FG_GREEN, text="[ PLAY SEQUENCE ]")
        self.status_bar.config(text="[ STATUS: CORE ACTIVE // STANDBY ]", fg=self.FG_GREEN)
        self.draw_grid()

    def playback_loop(self):
        """
        High-precision daemon loop generating PCM step mixes in real time.
        Executes on a background thread to safeguard GUI responsiveness.
        """
        import pygame
        import io
        
        while self.is_playing:
            try:
                bpm_val = float(self.bpm_scale.get())
            except Exception:
                bpm_val = 120.0
                
            self.bpm = bpm_val
            step_duration = 60.0 / self.bpm / 4.0
            start_time = time.time()
            
            step_idx = self.current_step
            step_data = {}
            
            # Populate step channel parameters
            if self.tracker_state[0][step_idx]["active"]:
                step_data[1] = {
                    "active": True,
                    "note_freq": NOTE_FREQS[self.tracker_state[0][step_idx]["note"]],
                    "duty": self.pulse_duty
                }
            if self.tracker_state[1][step_idx]["active"]:
                step_data[2] = {
                    "active": True,
                    "note_freq": NOTE_FREQS[self.tracker_state[1][step_idx]["note"]]
                }
            if self.tracker_state[2][step_idx]["active"]:
                step_data[3] = {
                    "active": True,
                    "note_freq": NOTE_FREQS[self.tracker_state[2][step_idx]["note"]]
                }
            if self.tracker_state[3][step_idx]["active"]:
                step_data[4] = {
                    "active": True,
                    "note_freq": NOTE_FREQS[self.tracker_state[3][step_idx]["note"]],
                    "pcm_type": self.pcm_type
                }
                
            if step_data:
                try:
                    wav_bytes = generate_step_sound(step_data, step_duration)
                    if pygame.mixer.get_init() and self.play_channel:
                        sound = pygame.mixer.Sound(io.BytesIO(wav_bytes))
                        self.play_channel.play(sound)
                except Exception as e:
                    print(f"[Playback Loop] Sound play warning: {e}")
                    
            # Safe GUI updates schedule
            self.after(0, self.draw_grid)
            
            self.current_step = (self.current_step + 1) % 16
            
            # Clock synchronization
            elapsed = time.time() - start_time
            sleep_time = step_duration - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    def export_audio_action(self):
        """Initiates async background file compilation and writes disk bytes."""
        self.play_ui_sound("click")
        self.status_bar.config(text="[ STATUS: EXPORT COMPILING... ]", fg=self.FG_YELLOW)
        self.update_idletasks()
        
        try:
            threading.Thread(target=self._compile_and_write_wav, daemon=True).start()
        except Exception as e:
            self.status_bar.config(text=f"[ ERROR: COMPILER FAULT: {str(e)[:18]} ]", fg=self.ALERT_RED)
            
    def _compile_and_write_wav(self):
        try:
            audio_dir = os.path.join(os.path.expanduser("~"), "ChaoHub_Data", "audio")
            if not os.path.exists(audio_dir):
                os.makedirs(audio_dir)
                
            sample_rate = 44100
            try:
                bpm_val = float(self.bpm_scale.get())
            except Exception:
                bpm_val = 120.0
                
            step_duration = 60.0 / bpm_val / 4.0
            N_s = int(sample_rate * step_duration)
            
            master_samples = []
            
            for step_idx in range(16):
                step_samples = [0.0] * N_s
                
                # Channel 1: Pulse
                if self.tracker_state[0][step_idx]["active"]:
                    note = self.tracker_state[0][step_idx]["note"]
                    freq = NOTE_FREQS[note]
                    duty = self.pulse_duty
                    for i in range(N_s):
                        t = i / sample_rate
                        phase = (t * freq) % 1.0
                        amp = 1.0 if phase < duty else -1.0
                        step_samples[i] += amp * 0.25
                        
                # Channel 2: Triangle
                if self.tracker_state[1][step_idx]["active"]:
                    note = self.tracker_state[1][step_idx]["note"]
                    freq = NOTE_FREQS[note]
                    for i in range(N_s):
                        t = i / sample_rate
                        phase = (t * freq) % 1.0
                        if phase < 0.25:
                            amp = 4.0 * phase
                        elif phase < 0.75:
                            amp = 2.0 - 4.0 * phase
                        else:
                            amp = 4.0 * phase - 4.0
                        step_samples[i] += amp * 0.35
                        
                # Channel 3: LFSR Noise
                if self.tracker_state[2][step_idx]["active"]:
                    note = self.tracker_state[2][step_idx]["note"]
                    freq = NOTE_FREQS[note]
                    for i in range(N_s):
                        t = i / sample_rate
                        shift_index = int(t * (freq * 15))
                        amp = NOISE_TABLE[shift_index % 65536]
                        step_samples[i] += amp * 0.20
                        
                # Channel 4: PCM
                if self.tracker_state[3][step_idx]["active"]:
                    note = self.tracker_state[3][step_idx]["note"]
                    freq = NOTE_FREQS[note]
                    pcm_type = self.pcm_type
                    for i in range(N_s):
                        t = i / sample_rate
                        if pcm_type == "LASER":
                            ln_a = -2.995732273553991
                            phase_val = 2.0 * math.pi * 600.0 * step_duration * ((0.05 ** (t / step_duration)) - 1.0) / ln_a
                            amp = math.sin(phase_val)
                            amp = round(amp * 8) / 8
                        else:
                            carrier = math.sin(2.0 * math.pi * 440.0 * t)
                            modulator = math.sin(2.0 * math.pi * 8.0 * t)
                            amp = carrier * modulator
                            amp = round(amp * 4) / 4
                        step_samples[i] += amp * 0.30
                        
                master_samples.extend(step_samples)
                
            byte_frames = []
            for s in master_samples:
                val = max(-1.0, min(1.0, s))
                int_val = int(val * 32767)
                byte_frames.append(struct.pack('<h', int_val))
                
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"TRACK_CH_{timestamp}.wav"
            filepath = os.path.join(audio_dir, filename)
            
            with wave.open(filepath, 'wb') as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(sample_rate)
                wav.writeframes(b''.join(byte_frames))
                
            self.after(0, self._flash_success_status, filepath)
            
        except Exception as e:
            self.after(0, lambda err=str(e): self.status_bar.config(
                text=f"[ ERROR: WRITE FAILURE: {err[:18]} ]", fg=self.ALERT_RED
            ))
            
    def _flash_success_status(self, filepath):
        self.play_ui_sound("beep")
        self._flash_counter = 6
        self._flash_status_tick(filepath)
        
    def _flash_status_tick(self, filepath):
        if self._flash_counter <= 0:
            self.status_bar.config(text="[ STATUS: 8-BIT EXPORT COMPLETE // DISK WRITE SUCCESSFUL ]", fg=self.FG_GREEN)
            print(f"[ChiptuneTrackerPanel] Audio exported to: {filepath}")
            self.after(4000, lambda: self.status_bar.config(text="[ STATUS: CORE ACTIVE // STANDBY ]", fg=self.FG_GREEN))
            return
            
        current_fg = self.status_bar.cget("fg")
        next_fg = self.FG_MAGENTA if current_fg == self.FG_GREEN else self.FG_GREEN
        self.status_bar.config(fg=next_fg)
        self._flash_counter -= 1
        self.after(200, self._flash_status_tick, filepath)

    def cleanup(self):
        """Guarded termination of background clocks and audio playbacks."""
        self.is_playing = False
        
        # Stop channel
        try:
            if self.play_channel and self.play_channel.get_busy():
                self.play_channel.stop()
        except Exception:
            pass
            
        # Join thread with short timeout
        try:
            if self.playback_thread and self.playback_thread.is_alive():
                self.playback_thread.join(timeout=0.2)
        except Exception:
            pass
