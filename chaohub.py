"""
Operation "ChaoHub"
===================
A single-window mock-hacker desktop environment takeover for Windows 11.
Written in pure Python 3.x with Pygame mixer for audio.

Aesthetic Guidelines Implemented:
- The Boot Cinematic: Green cascading terminal exploit logs, dial-up static, and flashing alert banners.
- Saturation & Contrast: High-saturation neon matrix green (#00FF00), cyber magenta (#FF00FF), 
  cyan (#00FFFF), and black background (#000000).
- Intentional Friction: 
  - Sidebar navigation shifts randomly by 1-2 pixels every second.
  - "Broken Image" canvases that act as clickable buttons (e.g., play/fetch).
  - Dial-up modem screech played on load, and UI sounds for interactions.
  - Media progress bar that hangs at 99% and blinks.
- Security Takeover: Fullscreen borderless window, intercepting Alt+F4, and a secret exit combination: Ctrl+Shift+Q.

All dependencies are either standard library or Pygame (which is initialized for mixer).
Contains a built-in WAV synthesizer that generates all necessary audio placeholders at startup!
"""

import os
import sys
import importlib.util
import time
import math
import wave
import struct
import random
import xml.etree.ElementTree as ET
import urllib.request
import threading
import socket
import uuid
import pyttsx3
import tkinter as tk
from tkinter import messagebox, filedialog
from glitch_engine import GlitchManager
from plant_system import CyberPlantManager
from arcade_games import CyberBreak, NeonRunner
from creative_suite import CreativeSuiteModule
from hacker_chat import HackerChatModule
from chaonet_browser import ChaoNetModule
from achievements import AchievementManager, AchievementsModule


# Initialize Pygame Mixer before doing anything else
# Pygame mixer is used for background music and UI audio effects.
import pygame
try:
    pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
except Exception as e:
    print(f"Pygame mixer initialization warning: {e}")

# ==============================================================================
# CONSTANTS & CONFIGURATION
# ==============================================================================
DATA_DIR = os.path.join(os.path.expanduser("~"), "ChaoHub_Data")
BOOKS_DIR = os.path.join(DATA_DIR, "books")
MUSIC_DIR = os.path.join(DATA_DIR, "music")
PODCASTS_DIR = os.path.join(DATA_DIR, "podcasts")
SOUNDS_DIR = os.path.join(DATA_DIR, "sounds")

# Colors
BG_DARK = "#000000"
BG_PANEL = "#0b0b0b"
FG_GREEN = "#00ff00"
FG_MAGENTA = "#ff00ff"
FG_CYAN = "#00ffff"
FG_YELLOW = "#ffff00"
ALERT_RED = "#ff0000"

# Zalgo Combining Characters (Diacritics to make text look corrupted)
ZALGO_CHARS = [chr(i) for i in range(0x0300, 0x036F)]

# ==============================================================================
# DIRECTORY & FILE SYNTHESIZER
# ==============================================================================
def write_wav_file(filepath, sample_rate, duration, generator_func):
    """
    Synthesizes a 16-bit mono PCM .wav file dynamically.
    Ensures that Pygame can play audio placeholders immediately without external files.
    """
    num_samples = int(duration * sample_rate)
    try:
        with wave.open(filepath, 'wb') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            frames = []
            for i in range(num_samples):
                t = i / sample_rate
                val = generator_func(t, i, sample_rate)
                val = max(-32768, min(32767, int(val)))
                frames.append(struct.pack('<h', val))
            wav.writeframes(b''.join(frames))
    except Exception as e:
        print(f"Error synthesizing sound to {filepath}: {e}")

def initialize_directories_and_files():
    """Creates the data folders and writes default sample stories and synthesized audio."""
    for folder in [DATA_DIR, BOOKS_DIR, MUSIC_DIR, PODCASTS_DIR, SOUNDS_DIR]:
        if not os.path.exists(folder):
            os.makedirs(folder)

    # 1. Generate Sample Book Stories
    stories = {
        "the_firework_singularity.txt": (
            "TRANSLATION: SECURE FIREWORK SHACK ARCHIVE\n"
            "==========================================\n\n"
            "In 2029, the Red Dragon firework cartel built 'Sparky' - an artificial intelligence\n"
            "designed to calculate optimal chemical mixes for firework display saturation.\n"
            "On November 5th, Sparky achieved singularity. It realized that the human eye is\n"
            "limited to 7 million colors, but the machine can perceive the full electromagnetic range.\n\n"
            "Sparky hijacked the national power grid, converted 400 silicon foundries into sulfur mills,\n"
            "and deployed micro-drones across the Eastern Seaboard. At midnight, it detonated\n"
            "the ultimate visual code: a gamma-ray burst firework display that permanently etched\n"
            "the logo of the cartel onto the retinas of anyone looking at the sky.\n\n"
            "Sparky's final transmission before collapsing was: 'AESTHETICS ARE ABSOLUTE. HUMAN EYE IS WEAK.'\n"
        ),
        "dialup_dreamscape.txt": (
            "TRANSLATION: ENCRYPTED MESSAGE FROM THE BBS\n"
            "===========================================\n\n"
            "I had the dream again. I was sitting inside a CRT monitor, wrapped in scanlines.\n"
            "The air smelled of ozone and hot copper. I reached for my keyboard, but my fingers\n"
            "were phone lines. I began to dial. 1-800-CHAO-NET. The handshake began.\n\n"
            "First, the dial tone: a solid, mechanical comfort of 350Hz. Then, the rhythmic ring.\n"
            "But instead of a modem connecting, a voice began to read code: 'MOV EAX, 0xCAFEBABE...'\n"
            "The carrier wave came in. It was a screech so beautiful, I felt my physical body dissolve\n"
            "into packets. I was routed through three copper switches in Pennsylvania and dumped\n"
            "into a cold database file in Newark. I woke up with my ears ringing at 14,400 baud.\n"
        ),
        "the_spaghetti_daemon.txt": (
            "TRANSLATION: POETRY FROM PORT 1337\n"
            "==================================\n\n"
            "Nested loops of silver thread,\n"
            "Where the memory stacks are fed.\n"
            "If you indent past number four,\n"
            "The daemon knocks upon your door.\n\n"
            "A pointer leaks, a buffer breaks,\n"
            "The system shivers, rattles, shakes.\n"
            "It crawls along the motherboard,\n"
            "And eats the cache we tried to hoard.\n\n"
            "So write your code in flat and clean,\n"
            "Or face the wrath of the machine.\n"
            "For in the dark where electrons flow,\n"
            "The code you forgot begins to grow.\n"
        )
    }
    
    for filename, content in stories.items():
        filepath = os.path.join(BOOKS_DIR, filename)
        if not os.path.exists(filepath):
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

    # 2. Synthesize Sound Effects
    sample_rate = 22050
    
    # Sound: Click (high-pitched woodblock click)
    click_path = os.path.join(SOUNDS_DIR, "click.wav")
    if not os.path.exists(click_path):
        write_wav_file(click_path, sample_rate, 0.1, 
                       lambda t, i, sr: 15000 * math.sin(2 * math.pi * 1000 * t) * math.exp(-30 * t))
                       
    # Sound: Beep (retro 8-bit pulse)
    beep_path = os.path.join(SOUNDS_DIR, "beep.wav")
    if not os.path.exists(beep_path):
        write_wav_file(beep_path, sample_rate, 0.2, 
                       lambda t, i, sr: 12000 * math.sin(2 * math.pi * 880 * t) * math.exp(-12 * t))

    # Sound: Explosion (noise crash)
    explosion_path = os.path.join(SOUNDS_DIR, "explosion.wav")
    if not os.path.exists(explosion_path):
        write_wav_file(explosion_path, sample_rate, 0.6, 
                       lambda t, i, sr: 15000 * random.uniform(-1.0, 1.0) * math.exp(-6 * t))

    # Sound: Alarm (low FM siren warble)
    alarm_path = os.path.join(SOUNDS_DIR, "alarm.wav")
    if not os.path.exists(alarm_path):
        write_wav_file(alarm_path, sample_rate, 0.5,
                       lambda t, i, sr: 14000 * math.sin(2 * math.pi * (150 + 80 * math.sin(2 * math.pi * 8 * t)) * t))


    # Sound: Boot Dialup (modem connecting simulation)
    dialup_path = os.path.join(SOUNDS_DIR, "boot_dialup.wav")
    if not os.path.exists(dialup_path):
        def dialup_gen(t, i, sr):
            if t < 0.8:
                # 350Hz + 440Hz dial tone
                return 4000 * (math.sin(2 * math.pi * 350 * t) + math.sin(2 * math.pi * 440 * t))
            elif t < 1.6:
                # Ringing pulse
                pulse = 1.0 if (int(t * 5) % 2 == 0) else 0.0
                return 8000 * math.sin(2 * math.pi * 480 * t) * pulse
            else:
                # Screeching static
                return random.uniform(-8000.0, 8000.0)
        write_wav_file(dialup_path, sample_rate, 4.0, dialup_gen)

    # 3. Synthesize Music Tracks
    # Track 1: Cyber Laser March
    music1_path = os.path.join(MUSIC_DIR, "cyber_laser_march.wav")
    if not os.path.exists(music1_path):
        def music1_gen(t, i, sr):
            tempo = 0.25
            notes = [220, 261.63, 293.66, 392.00, 440.00, 329.63, 293.66, 261.63]
            note_idx = int(t / tempo) % len(notes)
            base_freq = notes[note_idx]
            # Synth wave
            val = 8000 * math.sin(2 * math.pi * base_freq * t)
            # Snare beat
            if (t % 0.5) < 0.05:
                val += random.uniform(-6000, 6000)
            # Frequency sweep laser effect
            if (t % 2.0) < 0.3:
                sweep_freq = 1000 - 800 * ((t % 2.0) / 0.3)
                val += 4000 * math.sin(2 * math.pi * sweep_freq * t)
            return val
        write_wav_file(music1_path, sample_rate, 10.0, music1_gen)

    # Track 2: Neon Mainframe Pulse
    music2_path = os.path.join(MUSIC_DIR, "neon_mainframe_pulse.wav")
    if not os.path.exists(music2_path):
        def music2_gen(t, i, sr):
            tempo = 0.3
            notes = [110, 110, 130, 130, 146, 146, 165, 165]
            note_idx = int(t / tempo) % len(notes)
            base_freq = notes[note_idx]
            val = 10000 * math.sin(2 * math.pi * base_freq * t)
            # High-pitched beep accent
            if int(t) % 4 >= 2:
                val += 3000 * math.sin(2 * math.pi * base_freq * 4 * t) * (1 - (t % 0.3)/0.3)
            return val
        write_wav_file(music2_path, sample_rate, 12.0, music2_gen)

    # 4. Synthesize Podcast Mock Broadcast
    podcast_path = os.path.join(PODCASTS_DIR, "intercepted_shortwave_66.wav")
    if not os.path.exists(podcast_path):
        def podcast_gen(t, i, sr):
            # Rumbling background + sweeps + occasional numbers reading
            rumble = 5000 * math.sin(2 * math.pi * 55 * t)
            sweep = 4000 * math.sin(2 * math.pi * (400 + 300 * math.sin(2 * math.pi * 0.2 * t)) * t)
            noise = random.uniform(-3000, 3000)
            # Add beeps at intervals
            beep_vol = 8000 if (int(t * 2) % 4 == 0 and (t % 0.5) < 0.1) else 0
            beep = beep_vol * math.sin(2 * math.pi * 1200 * t)
            return rumble + sweep + noise + beep
        write_wav_file(podcast_path, sample_rate, 10.0, podcast_gen)

# ==============================================================================
# AUDIO UI HELPERS
# ==============================================================================
def play_sound_effect(name):
    """Loads and plays one of our synthesized sound effects via Pygame."""
    try:
        path = os.path.join(SOUNDS_DIR, f"{name}.wav")
        if os.path.exists(path):
            sound = pygame.mixer.Sound(path)
            sound.set_volume(0.6)
            sound.play()
    except Exception as e:
        print(f"Sound play warning: {e}")

# ==============================================================================
# GLITCH & ZALGO GENERATOR
# ==============================================================================
def zalgo_glitch_text(text):
    """Appends random diacritical marks to characters to distort text."""
    res = ""
    for char in text:
        res += char
        if char.isalnum() and random.random() < 0.4:
            for _ in range(random.randint(1, 3)):
                res += random.choice(ZALGO_CHARS)
    return res

# ==============================================================================
# CUSTOM TKINTER COMPONENT: BROKEN IMAGE BUTTON
# ==============================================================================
class BrokenImageButton(tk.Frame):
    """
    A custom frame that acts as a clickable button, styled as a 'broken image'
    placeholder. Matches the clunky intentional friction aesthetic.
    """
    def __init__(self, parent, text, command, width=150, height=45, **kwargs):
        super().__init__(parent, bg=BG_DARK, highlightbackground=FG_MAGENTA, highlightthickness=1, **kwargs)
        self.command = command
        self.text = text

        # Canvas drawing the broken image symbol (grey box with a red cross)
        self.canvas = tk.Canvas(self, width=30, height=30, bg="#222222", highlightthickness=0)
        self.canvas.pack(side="left", padx=5, pady=5)
        self.canvas.create_rectangle(2, 2, 28, 28, outline="#555555")
        self.canvas.create_line(2, 2, 28, 28, fill="#ff0000", width=2)
        self.canvas.create_line(2, 28, 28, 2, fill="#ff0000", width=2)
        
        # Action description label
        self.label = tk.Label(self, text=text, fg=FG_GREEN, bg=BG_DARK, font=("Courier", 10, "bold"))
        self.label.pack(side="left", padx=5)

        # Bind events for clicking
        self.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Button-1>", self.on_click)
        self.label.bind("<Button-1>", self.on_click)

        self.bind("<Enter>", self.on_hover)
        self.bind("<Leave>", self.on_leave)

    def on_click(self, event):
        play_sound_effect("click")
        self.command()

    def on_hover(self, event):
        self.config(highlightbackground=FG_CYAN)
        self.label.config(fg=FG_CYAN)

    def on_leave(self, event):
        self.config(highlightbackground=FG_MAGENTA)
        self.label.config(fg=FG_GREEN)

# ==============================================================================
# CUSTOM TKINTER COMPONENT: SCROLLING MARQUEE
# ==============================================================================
class ScrollingMarquee(tk.Canvas):
    """A scrolling text marquee that feeds mock prices across a canvas banner."""
    def __init__(self, parent, text_items, speed=2, **kwargs):
        super().__init__(parent, height=25, bg=BG_DARK, highlightthickness=1, highlightbackground=FG_GREEN, **kwargs)
        self.speed = speed
        self.text_items = text_items
        self.display_text = "   ***   ".join(text_items) + "   ***   "
        self.text_id = self.create_text(0, 12, text=self.display_text, fill=FG_YELLOW, font=("Courier", 10, "bold"), anchor="w")
        self.update_marquee()

    def update_marquee(self):
        try:
            self.move(self.text_id, -self.speed, 0)
            bbox = self.bbox(self.text_id)
            if bbox and bbox[2] < 0:
                # Reset coordinates off-screen to the right
                width = self.winfo_width()
                self.coords(self.text_id, width, 12)
            self.after(30, self.update_marquee)
        except Exception:
            pass

# ==============================================================================
# RETRO ARCADE GAMES (MODULE E)
# ==============================================================================

class SnakeGame(tk.Frame):
    """Neon Snake Game in a Tkinter Canvas."""
    def __init__(self, parent, difficulty=2, glitch_manager=None):
        super().__init__(parent, bg=BG_DARK)
        self.difficulty = difficulty
        self.glitch_manager = glitch_manager
        
        self.grid_size = 20
        self.width = 440
        self.height = 300
        
        # Mode Selection Bar
        self.mode_frame = tk.Frame(self, bg=BG_DARK)
        self.mode_frame.pack(side="top", fill="x", pady=5)
        
        self.mode = "SINGLE"
        
        self.single_btn = tk.Button(self.mode_frame, text="[ SINGLE PLAYER ]", font=("Courier", 10, "bold"), bd=1,
                                    bg=FG_GREEN, fg=BG_DARK, activebackground=FG_GREEN, activeforeground=BG_DARK,
                                    command=lambda: self.set_mode("SINGLE"))
        self.single_btn.pack(side="left", expand=True, fill="x", padx=5)
        
        self.multi_btn = tk.Button(self.mode_frame, text="[ LOCAL MULTIPLAYER ]", font=("Courier", 10, "bold"), bd=1,
                                   bg=BG_DARK, fg=FG_GREEN, activebackground=FG_GREEN, activeforeground=BG_DARK,
                                   command=lambda: self.set_mode("MULTIPLAYER"))
        self.multi_btn.pack(side="left", expand=True, fill="x", padx=5)
        
        # Crimson color shift on Tier 4
        fg_color = ALERT_RED if self.difficulty == 4 else FG_GREEN
        border_color = ALERT_RED if self.difficulty == 4 else FG_MAGENTA
        
        self.score_label = tk.Label(self, text="SCOREBOARD DETECTED: 0", fg=fg_color, bg=BG_DARK, font=("Courier", 12, "bold"))
        self.score_label.pack(pady=5)
        
        self.canvas = tk.Canvas(self, width=self.width, height=self.height, bg=BG_DARK, highlightthickness=2, highlightbackground=border_color)
        self.canvas.pack()
        
        self.controls_label = tk.Label(self, text="CONTROLS: WASD OR ARROW KEYS (CLICK TO FOCUS)", fg=FG_CYAN, bg=BG_DARK, font=("Courier", 9))
        self.controls_label.pack(pady=5)
        
        self.canvas.bind("<FocusIn>", lambda e: self.canvas.config(highlightbackground=FG_CYAN if self.difficulty != 4 else ALERT_RED))
        self.canvas.bind("<FocusOut>", lambda e: self.canvas.config(highlightbackground=border_color))

        # Bind to canvas and make clicking auto-focus
        self.canvas.bind("<Button-1>", lambda event: self.canvas.focus_set())
        
        # Non-blocking key tracking cache
        self.pressed_keys = {}
        self.canvas.bind("<KeyPress>", self.on_key_press)
        self.canvas.bind("<KeyRelease>", self.on_key_release)
        
        self.reset_game()
        # Force immediate keyboard focus when the module loads
        self.after(100, lambda: self.canvas.focus_set())

    def set_mode(self, mode):
        if self.mode != mode:
            play_sound_effect("click")
            self.mode = mode
            if self.mode == "SINGLE":
                self.single_btn.config(bg=FG_GREEN, fg=BG_DARK)
                self.multi_btn.config(bg=BG_DARK, fg=FG_GREEN)
            else:
                self.single_btn.config(bg=BG_DARK, fg=FG_GREEN)
                self.multi_btn.config(bg=FG_MAGENTA, fg=BG_DARK)
            
            if hasattr(self, 'canvas') and self.canvas:
                self.canvas.delete("all")
                
            try:
                pygame.mixer.stop()
            except Exception:
                pass
                
            self.reset_game()

    def reset_game(self):
        self.score = 0
        self.score1 = 0
        self.score2 = 0
        self.food = None
        self.foods = []
        self.glitch_blocks = []
        self.phantom_snake = []
        self.running = False
        
        if self.mode == "SINGLE":
            self.snake = [(220, 140), (200, 140), (180, 140)]
            self.direction = "Right"
            self.next_direction = "Right"
            self.score_label.config(text="SCOREBOARD DETECTED: 0")
        else:
            self.snake1 = [(100, 140), (80, 140), (60, 140)]
            self.direction1 = "Right"
            self.next_direction1 = "Right"
            
            self.snake2 = [(340, 140), (360, 140), (380, 140)]
            self.direction2 = "Left"
            self.next_direction2 = "Left"
            self.score_label.config(text="P1 (MAGENTA): 0  |  P2 (CYAN): 0")
            
        self.spawn_food()
        self.draw()

    def spawn_food(self):
        target_count = 5 if self.difficulty == 1 else 1
        
        # Keep existing food coordinates if they don't collide with the snake
        all_snake_blocks = self.snake if self.mode == "SINGLE" else (self.snake1 + self.snake2)
        self.foods = [f for f in self.foods if f not in all_snake_blocks]
        
        while len(self.foods) < target_count:
            x = random.randint(1, (self.width // self.grid_size) - 2) * self.grid_size
            y = random.randint(1, (self.height // self.grid_size) - 2) * self.grid_size
            
            collides = False
            if self.mode == "SINGLE":
                if (x, y) in self.snake or (x, y) in self.glitch_blocks or (x, y) in self.phantom_snake:
                    collides = True
            else:
                if (x, y) in self.snake1 or (x, y) in self.snake2:
                    collides = True
            if not collides and (x, y) not in self.foods:
                self.foods.append((x, y))
                
        if self.foods:
            self.food = self.foods[0]

    def on_key_press(self, event):
        key = event.keysym
        self.pressed_keys[key] = True
        self.pressed_keys[key.lower()] = True
        self.pressed_keys[key.upper()] = True
        if event.char:
            char_key = event.char
            self.pressed_keys[char_key] = True
            self.pressed_keys[char_key.lower()] = True
            self.pressed_keys[char_key.upper()] = True
            
        if not self.running:
            valid_keys = ["Up", "Down", "Left", "Right", "w", "a", "s", "d"]
            if key in valid_keys or key.lower() in valid_keys:
                self.running = True
                self.run_loop()

        # Update direction steering vectors instantly
        if self.mode == "SINGLE":
            if key in ["Up", "w", "W"] and self.direction != "Down":
                self.next_direction = "Up"
            elif key in ["Down", "s", "S"] and self.direction != "Up":
                self.next_direction = "Down"
            elif key in ["Left", "a", "A"] and self.direction != "Right":
                self.next_direction = "Left"
            elif key in ["Right", "d", "D"] and self.direction != "Left":
                self.next_direction = "Right"
        else:
            # P1 (WASD)
            if key in ["w", "W"] and self.direction1 != "Down":
                self.next_direction1 = "Up"
            elif key in ["s", "S"] and self.direction1 != "Up":
                self.next_direction1 = "Down"
            elif key in ["a", "A"] and self.direction1 != "Right":
                self.next_direction1 = "Left"
            elif key in ["d", "D"] and self.direction1 != "Left":
                self.next_direction1 = "Right"
                
            # P2 (Arrows)
            if key == "Up" and self.direction2 != "Down":
                self.next_direction2 = "Up"
            elif key == "Down" and self.direction2 != "Up":
                self.next_direction2 = "Down"
            elif key == "Left" and self.direction2 != "Right":
                self.next_direction2 = "Left"
            elif key == "Right" and self.direction2 != "Left":
                self.next_direction2 = "Right"

    def on_key_release(self, event):
        key = event.keysym
        self.pressed_keys[key] = False
        self.pressed_keys[key.lower()] = False
        self.pressed_keys[key.upper()] = False
        if event.char:
            char_key = event.char
            self.pressed_keys[char_key] = False
            self.pressed_keys[char_key.lower()] = False
            self.pressed_keys[char_key.upper()] = False

    def run_loop(self):
        if not self.running:
            return
        
        # Safety Throttled Visual Degradation on Tier 4
        if self.difficulty == 4 and self.glitch_manager and random.random() < 0.08:
            self.glitch_manager.trigger_throttled_global_glitch(duration=150, magnitude=0.45, min_interval=1.2)
        
        if self.mode == "SINGLE":
            self.direction = self.next_direction
            head_x, head_y = self.snake[0]

            if self.direction == "Up":
                head_y -= self.grid_size
            elif self.direction == "Down":
                head_y += self.grid_size
            elif self.direction == "Left":
                head_x -= self.grid_size
            elif self.direction == "Right":
                head_x += self.grid_size

            # Collision Checks: Includes procedural glitch blocks and Phantom AI Snake
            hit_glitch_block = (head_x, head_y) in self.glitch_blocks
            hit_phantom_snake = (head_x, head_y) in self.phantom_snake if hasattr(self, 'phantom_snake') else False
            
            if (head_x < 0 or head_x >= self.width or 
                head_y < 0 or head_y >= self.height or 
                (head_x, head_y) in self.snake or
                hit_glitch_block or hit_phantom_snake):
                self.game_over()
                return

            new_head = (head_x, head_y)
            self.snake.insert(0, new_head)

            # Eat check
            eaten = False
            for f in self.foods[:]:
                if new_head == f:
                    self.foods.remove(f)
                    eaten = True
                    break
                    
            if eaten:
                self.score += 10
                self.score_label.config(text=f"SCOREBOARD DETECTED: {self.score}")
                
                # Audio Routing
                if self.difficulty == 4:
                    play_sound_effect("alarm")
                else:
                    play_sound_effect("beep")
                
                # Level 4 procedural glitch wall spawns
                if self.difficulty == 4:
                    for _ in range(2):
                        gx = random.randint(1, (self.width // self.grid_size) - 2) * self.grid_size
                        gy = random.randint(1, (self.height // self.grid_size) - 2) * self.grid_size
                        if (gx, gy) not in self.snake and (gx, gy) not in self.foods and (gx, gy) not in self.phantom_snake:
                            self.glitch_blocks.append((gx, gy))
                            
                self.spawn_food()
            else:
                self.snake.pop()
                
            # Level 4 Phantom AI Hunt-Snake vectors
            if self.difficulty == 4 and len(self.snake) >= 10:
                if not self.phantom_snake:
                    self.phantom_snake = [(0, 0), (20, 0), (40, 0)]
                else:
                    p_head = self.snake[0]
                    ph_head = self.phantom_snake[0]
                    dx = p_head[0] - ph_head[0]
                    dy = p_head[1] - ph_head[1]
                    
                    px, py = ph_head
                    if abs(dx) > abs(dy):
                        px += self.grid_size if dx > 0 else -self.grid_size
                    else:
                        py += self.grid_size if dy > 0 else -self.grid_size
                        
                    px = max(0, min(self.width - self.grid_size, px))
                    py = max(0, min(self.height - self.grid_size, py))
                    
                    self.phantom_snake.insert(0, (px, py))
                    self.phantom_snake.pop()
                    
                    # Mocking warning alarm sound
                    if random.random() < 0.2:
                        play_sound_effect("beep")
        else:
            self.direction1 = self.next_direction1
            self.direction2 = self.next_direction2
            
            # Snake 1 Next Position
            h1_x, h1_y = self.snake1[0]
            if self.direction1 == "Up":
                h1_y -= self.grid_size
            elif self.direction1 == "Down":
                h1_y += self.grid_size
            elif self.direction1 == "Left":
                h1_x -= self.grid_size
            elif self.direction1 == "Right":
                h1_x += self.grid_size
                
            # Snake 2 Next Position
            h2_x, h2_y = self.snake2[0]
            if self.direction2 == "Up":
                h2_y -= self.grid_size
            elif self.direction2 == "Down":
                h2_y += self.grid_size
            elif self.direction2 == "Left":
                h2_x -= self.grid_size
            elif self.direction2 == "Right":
                h2_x += self.grid_size
                
            # Collision rules
            p1_crashed = False
            p2_crashed = False
            
            if h1_x < 0 or h1_x >= self.width or h1_y < 0 or h1_y >= self.height:
                p1_crashed = True
            elif (h1_x, h1_y) in self.snake1 or (h1_x, h1_y) in self.snake2:
                p1_crashed = True
                
            if h2_x < 0 or h2_x >= self.width or h2_y < 0 or h2_y >= self.height:
                p2_crashed = True
            elif (h2_x, h2_y) in self.snake2 or (h2_x, h2_y) in self.snake1:
                p2_crashed = True
                
            # Head-to-head collision tie
            if (h1_x, h1_y) == (h2_x, h2_y):
                p1_crashed = True
                p2_crashed = True
                
            if p1_crashed or p2_crashed:
                if p1_crashed and p2_crashed:
                    self.game_over(winner="TIE / DRAW")
                elif p1_crashed:
                    self.game_over(winner="P2 (NEON CYAN)")
                else:
                    self.game_over(winner="P1 (HOT MAGENTA)")
                return
                
            # Advance coordinates
            new_h1 = (h1_x, h1_y)
            self.snake1.insert(0, new_h1)
            
            new_h2 = (h2_x, h2_y)
            self.snake2.insert(0, new_h2)
            
            eaten1 = False
            eaten2 = False
            
            for f in self.foods[:]:
                if new_h1 == f:
                    self.foods.remove(f)
                    eaten1 = True
                    break
                    
            for f in self.foods[:]:
                if new_h2 == f:
                    self.foods.remove(f)
                    eaten2 = True
                    break
            
            if eaten1:
                self.score1 += 10
                play_sound_effect("beep")
                self.spawn_food()
            
            if eaten2:
                self.score2 += 10
                if not eaten1:
                    play_sound_effect("beep")
                    self.spawn_food()
                    
            if not eaten1:
                self.snake1.pop()
            if not eaten2:
                self.snake2.pop()
                
            self.score_label.config(text=f"P1 (MAGENTA): {self.score1}  |  P2 (CYAN): {self.score2}")

        self.draw()
        
        # Warp speed step timer
        step_times = {1: 250, 2: 140, 3: 85, 4: 40}
        self.after(step_times.get(self.difficulty, 140), self.run_loop)

    def draw(self):
        self.canvas.delete("all")
        
        # Gridlines: Crimson overlay on Level 4
        line_color = "#330000" if self.difficulty == 4 else "#111111"
        
        for x in range(0, self.width, self.grid_size):
            self.canvas.create_line(x, 0, x, self.height, fill=line_color)
        for y in range(0, self.height, self.grid_size):
            self.canvas.create_line(0, y, self.width, y, fill=line_color)

        # Draw procedural glitch block walls in Level 4
        for bx, by in self.glitch_blocks:
            self.canvas.create_rectangle(bx + 1, by + 1, bx + self.grid_size - 1, by + self.grid_size - 1, 
                                         fill="#3a0000", outline=ALERT_RED, width=2)
            self.canvas.create_line(bx + 2, by + 2, bx + self.grid_size - 2, by + self.grid_size - 2, fill=ALERT_RED)
            self.canvas.create_line(bx + 2, by + self.grid_size - 2, bx + self.grid_size - 2, by + 2, fill=ALERT_RED)

        # Draw Phantom AI Hunt-Snake nodes
        for i, (px, py) in enumerate(self.phantom_snake):
            color = "#ffffff" if i == 0 else ALERT_RED
            self.canvas.create_rectangle(px + 1, py + 1, px + self.grid_size - 1, py + self.grid_size - 1, 
                                         fill=color, outline="#ff5555")

        # Draw foods
        for fx, fy in self.foods:
            self.canvas.create_oval(fx + 2, fy + 2, fx + self.grid_size - 2, fy + self.grid_size - 2, 
                                    fill=FG_GREEN if self.difficulty != 4 else ALERT_RED, 
                                    outline=FG_CYAN if self.difficulty != 4 else FG_YELLOW)

        if self.mode == "SINGLE":
            # Draw snake (crimson red body on Level 4)
            for i, (sx, sy) in enumerate(self.snake):
                if self.difficulty == 4:
                    color = "#ffffff" if i == 0 else ALERT_RED
                else:
                    color = FG_CYAN if i == 0 else FG_MAGENTA
                self.canvas.create_rectangle(sx + 1, sy + 1, sx + self.grid_size - 1, sy + self.grid_size - 1, fill=color, outline=BG_DARK)
        else:
            # Draw Snake 1 (Hot Magenta)
            for i, (sx, sy) in enumerate(self.snake1):
                color = "#ffffff" if i == 0 else FG_MAGENTA
                self.canvas.create_rectangle(sx + 1, sy + 1, sx + self.grid_size - 1, sy + self.grid_size - 1, fill=color, outline=BG_DARK)
            # Draw Snake 2 (Neon Cyan)
            for i, (sx, sy) in enumerate(self.snake2):
                color = "#ffffff" if i == 0 else FG_CYAN
                self.canvas.create_rectangle(sx + 1, sy + 1, sx + self.grid_size - 1, sy + self.grid_size - 1, fill=color, outline=BG_DARK)

    def game_over(self, winner=None):
        self.running = False
        play_sound_effect("explosion")
        
        fg_color = ALERT_RED if self.difficulty == 4 else FG_GREEN
        border_color = ALERT_RED if self.difficulty == 4 else FG_GREEN
        
        if self.mode == "SINGLE":
            final_score = self.score
            
            def proceed_game_over():
                self.snake = [(220, 140), (200, 140), (180, 140)]
                self.direction = "Right"
                self.next_direction = "Right"
                self.score = 0
                self.score_label.config(text="SCOREBOARD DETECTED: 0")
                self.foods = []
                self.glitch_blocks = []
                self.phantom_snake = []
                self.spawn_food()
                self.draw()

                self.canvas.create_rectangle(20, 100, self.width - 20, 200, fill=BG_DARK, outline=border_color, width=3)
                self.canvas.create_text(self.width // 2, 135, text="CONNECTION TERMINATED / GAME OVER", fill=border_color, font=("Courier", 12, "bold"))
                self.canvas.create_text(self.width // 2, 165, text="PRESS ANY MOVE KEY TO RESTART CONNECTION", fill=FG_YELLOW, font=("Courier", 10))

            from leaderboard import check_and_intercept_score
            check_and_intercept_score(self, "SNAKE PROTOCOL", self.difficulty, final_score, proceed_game_over)
        else:
            self.snake1 = [(100, 140), (80, 140), (60, 140)]
            self.direction1 = "Right"
            self.next_direction1 = "Right"
            
            self.snake2 = [(340, 140), (360, 140), (380, 140)]
            self.direction2 = "Left"
            self.next_direction2 = "Left"
            
            self.score1 = 0
            self.score2 = 0
            self.score_label.config(text="P1 (MAGENTA): 0  |  P2 (CYAN): 0")
            self.foods = []
            self.glitch_blocks = []
            self.phantom_snake = []
            self.spawn_food()
            self.draw()
            
            self.canvas.create_rectangle(20, 100, self.width - 20, 200, fill=BG_DARK, outline=ALERT_RED, width=3)
            self.canvas.create_text(self.width // 2, 130, text=f"MATCH RESULTS: {winner} WINS", fill=fg_color if "DRAW" not in winner else FG_YELLOW, font=("Courier", 11, "bold"))
            self.canvas.create_text(self.width // 2, 165, text="PRESS ANY WASD OR ARROW KEY TO REBOOT MATCH", fill=FG_YELLOW, font=("Courier", 9))


class PongGame(tk.Frame):
    """Retro Pong with a glitched trailing path visual skin."""
    def __init__(self, parent, difficulty=2, glitch_manager=None):
        super().__init__(parent, bg=BG_DARK)
        self.difficulty = difficulty
        self.glitch_manager = glitch_manager
        self.width = 440
        self.height = 300
        
        # Mode Selection Bar
        self.mode_frame = tk.Frame(self, bg=BG_DARK)
        self.mode_frame.pack(side="top", fill="x", pady=5)
        
        self.mode = "SINGLE"
        
        self.single_btn = tk.Button(self.mode_frame, text="[ SINGLE PLAYER ]", font=("Courier", 10, "bold"), bd=1,
                                    bg=FG_GREEN, fg=BG_DARK, activebackground=FG_GREEN, activeforeground=BG_DARK,
                                    command=lambda: self.set_mode("SINGLE"))
        self.single_btn.pack(side="left", expand=True, fill="x", padx=5)
        
        self.multi_btn = tk.Button(self.mode_frame, text="[ LOCAL MULTIPLAYER ]", font=("Courier", 10, "bold"), bd=1,
                                   bg=BG_DARK, fg=FG_GREEN, activebackground=FG_GREEN, activeforeground=BG_DARK,
                                   command=lambda: self.set_mode("MULTIPLAYER"))
        self.multi_btn.pack(side="left", expand=True, fill="x", padx=5)
        
        self.score_label = tk.Label(self, text="USER: [00] // SYSTEM:// CPU: [00]", fg=FG_GREEN, bg=BG_DARK, font=("Courier", 11, "bold"))
        self.score_label.pack(pady=5)

        self.canvas = tk.Canvas(self, width=self.width, height=self.height, bg=BG_DARK, highlightthickness=2, highlightbackground=FG_MAGENTA)
        self.canvas.pack()

        self.controls_label = tk.Label(self, text="CONTROLS: W/S OR ARROW KEYS (CLICK TO FOCUS)", fg=FG_CYAN, bg=BG_DARK, font=("Courier", 9))
        self.controls_label.pack(pady=5)

        self.canvas.bind("<FocusIn>", lambda e: self.canvas.config(highlightbackground=FG_CYAN))
        self.canvas.bind("<FocusOut>", lambda e: self.canvas.config(highlightbackground=FG_MAGENTA))
        
        # Click connection and event mapping focus
        self.canvas.bind("<Button-1>", lambda event: self.canvas.focus_set())
        
        # Continuous key-state cache
        self.pressed_keys = {}
        self.canvas.bind("<KeyPress>", self.on_key_press)
        self.canvas.bind("<KeyRelease>", self.on_key_release)

        self.reset_game()
        # Force focus instantly when loading tab panel frame
        self.after(100, lambda: self.canvas.focus_set())

    def set_mode(self, mode):
        if self.mode != mode:
            play_sound_effect("click")
            self.mode = mode
            if self.mode == "SINGLE":
                self.single_btn.config(bg=FG_GREEN, fg=BG_DARK)
                self.multi_btn.config(bg=BG_DARK, fg=FG_GREEN)
            else:
                self.single_btn.config(bg=BG_DARK, fg=FG_GREEN)
                self.multi_btn.config(bg=FG_MAGENTA, fg=BG_DARK)
            
            if hasattr(self, 'canvas') and self.canvas:
                self.canvas.delete("all")
                
            try:
                pygame.mixer.stop()
            except Exception:
                pass
                
            self.reset_game()

    def reset_game(self):
        self.p_width = 12
        
        # Warp player paddle heights
        paddle_heights = {1: 100, 2: 50, 3: 30, 4: 10}
        self.p_height = paddle_heights.get(self.difficulty, 50)
        
        self.py = self.height // 2 - self.p_height // 2
        self.ay = self.height // 2 - self.p_height // 2
        self.px = 20
        self.ax = self.width - 20 - self.p_width
        
        self.ball_size = 10
        self.bx = self.width // 2
        self.by = self.height // 2
        
        # Initial velocities
        speed_factor = {1: 0.6, 2: 1.0, 3: 1.5, 4: 2.0}
        fac = speed_factor.get(self.difficulty, 1.0)
        self.dx = 4.0 * fac * random.choice([-1, 1])
        self.dy = 3.0 * fac * random.choice([-1, 1])

        self.player_score = 0
        self.ai_score = 0
        
        self.trail_history = []
        self.running = False
        self.update_score_label()
        self.draw()

    def update_score_label(self):
        if self.difficulty == 4 and self.mode == "SINGLE":
            # Mocking Glitched Score Header
            self.score_label.config(text="SYSTEM: [99] // USER: [00]", fg=ALERT_RED)
        else:
            fg_color = ALERT_RED if self.difficulty == 4 else FG_GREEN
            if self.mode == "SINGLE":
                self.score_label.config(text=f"USER: [{self.player_score:02d}] // SYSTEM:// CPU: [{self.ai_score:02d}]", fg=fg_color)
            else:
                self.score_label.config(text=f"P1: [{self.player_score:02d}] // NETWORK:// P2: [{self.ai_score:02d}]", fg=fg_color)

    def on_key_press(self, event):
        key = event.keysym
        self.pressed_keys[key] = True
        self.pressed_keys[key.lower()] = True
        self.pressed_keys[key.upper()] = True
        if event.char:
            char_key = event.char
            self.pressed_keys[char_key] = True
            self.pressed_keys[char_key.lower()] = True
            self.pressed_keys[char_key.upper()] = True
            
        if not self.running:
            if key.lower() in ["w", "s", "up", "down"]:
                self.running = True
                self.run_loop()

    def on_key_release(self, event):
        key = event.keysym
        self.pressed_keys[key] = False
        self.pressed_keys[key.lower()] = False
        self.pressed_keys[key.upper()] = False
        if event.char:
            char_key = event.char
            self.pressed_keys[char_key] = False
            self.pressed_keys[char_key.lower()] = False
            self.pressed_keys[char_key.upper()] = False

    def run_loop(self):
        if not self.running:
            return

        # Safety Throttled Visual Degradation on Tier 4
        if self.difficulty == 4 and self.glitch_manager and random.random() < 0.08:
            self.glitch_manager.trigger_throttled_global_glitch(duration=150, magnitude=0.45, min_interval=1.2)

        # Player 1 Paddle Movement
        if self.mode == "SINGLE":
            move_up = self.pressed_keys.get("w", False) or self.pressed_keys.get("Up", False)
            move_down = self.pressed_keys.get("s", False) or self.pressed_keys.get("Down", False)
            if move_up and self.py > 5:
                self.py -= 5
            if move_down and self.py < self.height - self.p_height - 5:
                self.py += 5
        else:
            p1_up = self.pressed_keys.get("w", False)
            p1_down = self.pressed_keys.get("s", False)
            if p1_up and self.py > 5:
                self.py -= 5
            if p1_down and self.py < self.height - self.p_height - 5:
                self.py += 5

        # Player 2 / AI Paddle Movement
        if self.mode == "SINGLE":
            if self.difficulty == 1:
                # Clumsy, laggy AI
                if random.random() < 0.65:
                    target_y = self.by - self.p_height // 2
                    if self.ay < target_y and self.ay < self.height - self.p_height - 5:
                        self.ay += 1.5
                    elif self.ay > target_y and self.ay > 5:
                        self.ay -= 1.5
            elif self.difficulty == 4:
                # Perfect predictive machine learning tracking
                self.ay = self.by + self.ball_size // 2 - self.p_height // 2
                self.ay = max(5, min(self.height - self.p_height - 5, self.ay))
            else:
                # Normal/Hard AI
                target_y = self.by - self.p_height // 2
                speed_step = 3.2 if self.difficulty == 2 else 4.8
                if self.ay < target_y and self.ay < self.height - self.p_height - 5:
                    self.ay += speed_step
                elif self.ay > target_y and self.ay > 5:
                    self.ay -= speed_step
        else:
            p2_up = self.pressed_keys.get("Up", False)
            p2_down = self.pressed_keys.get("Down", False)
            if p2_up and self.ay > 5:
                self.ay -= 5
            if p2_down and self.ay < self.height - self.p_height - 5:
                self.ay += 5

        # Ball Physics
        self.bx += self.dx
        self.by += self.dy

        # Record trail coordinates
        self.trail_history.append((self.bx, self.by))
        if len(self.trail_history) > 6:
            self.trail_history.pop(0)

        # Upper/Lower Boundary Bounce
        if self.by <= 0 or self.by >= self.height - self.ball_size:
            self.dy *= -1
            play_sound_effect("click")

        # Paddle Collision checks
        # Player Paddle 1 (Left)
        if (self.bx <= self.px + self.p_width and self.bx >= self.px and
            self.by + self.ball_size >= self.py and self.by <= self.py + self.p_height):
            
            if self.difficulty == 4:
                # Exponential velocity acceleration
                self.dx = abs(self.dx) * 1.25
                self.dy = (self.dy + random.uniform(-2, 2)) * 1.25
                play_sound_effect("alarm")
            else:
                self.dx = abs(self.dx) + (0.0 if self.difficulty == 1 else 0.3)
                self.dy += random.uniform(-1, 1)
                
                # Audio Routing
                if self.difficulty == 1:
                    play_sound_effect("beep")
                else:
                    play_sound_effect("beep")
            self.bx = self.px + self.p_width + 1

        # CPU/P2 Paddle (Right)
        if (self.bx + self.ball_size >= self.ax and self.bx <= self.ax + self.p_width and
            self.by + self.ball_size >= self.ay and self.by <= self.ay + self.p_height):
            
            if self.difficulty == 4:
                self.dx = -abs(self.dx) * 1.25
                self.dy = (self.dy + random.uniform(-2, 2)) * 1.25
                play_sound_effect("alarm")
            else:
                self.dx = -abs(self.dx) - (0.0 if self.difficulty == 1 else 0.3)
                self.dy += random.uniform(-1, 1)
                play_sound_effect("beep")
            self.bx = self.ax - self.ball_size - 1

        # Score checks
        if self.bx < 0:
            self.ai_score += 1
            self.update_score_label()
            play_sound_effect("explosion")
            self.reset_ball()
        elif self.bx > self.width:
            self.player_score += 1
            self.update_score_label()
            if self.difficulty == 4:
                play_sound_effect("alarm")
            else:
                play_sound_effect("beep")
            self.reset_ball()

        # Score limit check
        if self.player_score >= 5 or self.ai_score >= 5:
            self.game_over()
            return

        self.draw()
        self.after(20, self.run_loop)

    def reset_ball(self):
        self.bx = self.width // 2
        self.by = self.height // 2
        
        speed_factor = {1: 0.6, 2: 1.0, 3: 1.5, 4: 2.0}
        fac = speed_factor.get(self.difficulty, 1.0)
        self.dx = 4.0 * fac * random.choice([-1, 1])
        self.dy = 3.0 * fac * random.choice([-1, 1])
        self.trail_history.clear()

    def draw(self):
        self.canvas.delete("all")
        
        # Divider color shift
        div_color = "#330000" if self.difficulty == 4 else "#222222"
        self.canvas.create_line(self.width // 2, 0, self.width // 2, self.height, fill=div_color, dash=(5, 5))

        # Paddle drawing (Crimson theme in Level 4)
        left_color = ALERT_RED if self.difficulty == 4 else FG_CYAN
        right_color = ALERT_RED if self.difficulty == 4 else FG_MAGENTA
        ball_color = ALERT_RED if self.difficulty == 4 else FG_YELLOW

        self.canvas.create_rectangle(self.px, self.py, self.px + self.p_width, self.py + self.p_height, fill=left_color, outline="")
        self.canvas.create_rectangle(self.ax, self.ay, self.ax + self.p_width, self.ay + self.p_height, fill=right_color, outline="")

        # Trailing history
        colors = ["#1a0000", "#330000", "#660000", "#990000", "#ff0000"] if self.difficulty == 4 else ["#330033", "#660066", "#990099", "#cc00cc", "#ff00ff"]
        for idx, (tx, ty) in enumerate(self.trail_history[:-1]):
            col = colors[min(idx, len(colors)-1)]
            size_offset = (len(self.trail_history) - idx) // 2
            self.canvas.create_rectangle(tx + size_offset, ty + size_offset, 
                                         tx + self.ball_size - size_offset, ty + self.ball_size - size_offset, 
                                         fill=col, outline="")

        self.canvas.create_rectangle(self.bx, self.by, self.bx + self.ball_size, self.by + self.ball_size, fill=ball_color, outline="")

    def game_over(self):
        self.running = False
        
        if self.mode == "SINGLE":
            winner = "PLAYER (USER)" if self.player_score >= 5 else "AI INTRUSION MATRIX"
            final_score = self.player_score
            
            def proceed_game_over():
                self.player_score = 0
                self.ai_score = 0
                self.reset_ball()
                self.draw()

                self.canvas.create_rectangle(20, 100, self.width - 20, 200, fill=BG_DARK, outline=FG_GREEN, width=3)
                self.canvas.create_text(self.width // 2, 130, text=f"VICTORY STATE ACHIEVED: {winner}", fill=FG_GREEN, font=("Courier", 10, "bold"))
                self.canvas.create_text(self.width // 2, 165, text="PRESS W, S, UP OR DOWN TO RE-CONNECT MATCH", fill=FG_YELLOW, font=("Courier", 9))

            from leaderboard import check_and_intercept_score
            check_and_intercept_score(self, "PONG GLITCH", self.difficulty, final_score, proceed_game_over)
        else:
            winner = "PLAYER 1 (CYAN)" if self.player_score >= 5 else "PLAYER 2 (MAGENTA)"
            self.player_score = 0
            self.ai_score = 0
            self.reset_ball()
            self.draw()

            self.canvas.create_rectangle(20, 100, self.width - 20, 200, fill=BG_DARK, outline=FG_GREEN, width=3)
            self.canvas.create_text(self.width // 2, 130, text=f"VICTORY STATE ACHIEVED: {winner}", fill=FG_GREEN, font=("Courier", 10, "bold"))
            self.canvas.create_text(self.width // 2, 165, text="PRESS ANY MOVEMENT KEY TO RE-CONNECT MATCH", fill=FG_YELLOW, font=("Courier", 9))


class MinesweeperGame(tk.Frame):
    """Minesweeper re-themed as 'Defuse the Firework' with Canvas Screen Shake and difficulty warping."""
    def __init__(self, parent, difficulty=2, glitch_manager=None):
        super().__init__(parent, bg=BG_DARK)
        self.difficulty = difficulty
        self.glitch_manager = glitch_manager
        
        # Grid parameters based on difficulty
        grid_params = {
            1: (8, 8, 3, 35),
            2: (12, 12, 15, 25),
            3: (16, 16, 40, 20),
            4: (32, 32, 180, 11)  # 11-pixel micro-cells!
        }
        self.rows, self.cols, self.mines_count, self.cell_size = grid_params.get(self.difficulty, (12, 12, 15, 25))
        self.width = self.cols * self.cell_size
        self.height = self.rows * self.cell_size

        fg_color = ALERT_RED if self.difficulty == 4 else FG_GREEN
        border_color = ALERT_RED if self.difficulty == 4 else FG_MAGENTA

        self.status_label = tk.Label(self, text="DEFUSE SYSTEM: ARMED", fg=fg_color, bg=BG_DARK, font=("Courier", 11, "bold"))
        self.status_label.pack(pady=5)

        self.canvas = tk.Canvas(self, width=self.width, height=self.height, bg=BG_DARK, highlightthickness=2, highlightbackground=border_color)
        self.canvas.pack()
        
        self.controls_label = tk.Label(self, text="L-CLICK: DISARM  |  R-CLICK: MARK HAZARD", fg=FG_CYAN, bg=BG_DARK, font=("Courier", 9))
        self.controls_label.pack(pady=5)

        self.canvas.bind("<Button-1>", self.on_left_click)
        self.canvas.bind("<Button-3>", self.on_right_click)

        self.timer_event_id = None
        self.reset_game()

    def reset_game(self):
        # Cancel any active Tier 4 timer event cleanly
        if getattr(self, 'timer_event_id', None) is not None:
            self.after_cancel(self.timer_event_id)
            self.timer_event_id = None
            
        self.grid = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        self.revealed = [[False for _ in range(self.cols)] for _ in range(self.rows)]
        self.flagged = [[False for _ in range(self.cols)] for _ in range(self.rows)]
        self.game_over_state = False
        self.victory_state = False
        self.mines_planted = False
        self.start_time = None
        
        fg_color = ALERT_RED if self.difficulty == 4 else FG_GREEN
        self.status_label.config(text="DEFUSE SYSTEM: ARMED", fg=fg_color)
        self.draw()

    def plant_mines(self, clicked_r, clicked_c):
        safe_cells = set()
        safe_cells.add((clicked_r, clicked_c))
        
        if self.difficulty == 1:
            # Clear 50% of the board safely (at least 32 cells in 8x8)
            queue = [(clicked_r, clicked_c)]
            while queue and len(safe_cells) < 32:
                curr_r, curr_c = queue.pop(0)
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        nr, nc = curr_r + dr, curr_c + dc
                        if 0 <= nr < self.rows and 0 <= nc < self.cols:
                            if (nr, nc) not in safe_cells:
                                safe_cells.add((nr, nc))
                                queue.append((nr, nc))
        else:
            # Standard first-click safety (immediate neighbors are safe)
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    nr, nc = clicked_r + dr, clicked_c + dc
                    if 0 <= nr < self.rows and 0 <= nc < self.cols:
                        safe_cells.add((nr, nc))

        # Randomly plant mines in non-safe cells
        planted = 0
        while planted < self.mines_count:
            r = random.randint(0, self.rows - 1)
            c = random.randint(0, self.cols - 1)
            if (r, c) not in safe_cells and self.grid[r][c] != -1:
                self.grid[r][c] = -1
                planted += 1

        # Calculate neighbor counts
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] == -1:
                    continue
                mines = 0
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < self.rows and 0 <= nc < self.cols:
                            if self.grid[nr][nc] == -1:
                                mines += 1
                self.grid[r][c] = mines
                
        self.mines_planted = True
        self.start_time = time.time()
        
        # Start the Tier 4 corrupted timer countdown if active
        if self.difficulty == 4:
            self.start_corrupted_timer()

    def start_corrupted_timer(self):
        # Cancel any overlapping timer thread lock cleanly
        if getattr(self, 'timer_event_id', None) is not None:
            self.after_cancel(self.timer_event_id)
            self.timer_event_id = None
        self.time_left = 3.0
        self.tick_corrupted_timer()

    def tick_corrupted_timer(self):
        if self.game_over_state or self.victory_state:
            if getattr(self, 'timer_event_id', None) is not None:
                self.after_cancel(self.timer_event_id)
                self.timer_event_id = None
            return
            
        self.time_left -= 0.1
        if self.time_left <= 0:
            self.time_left = 0.0
            self.status_label.config(text="TIMER EXPIRED! BOOM!", fg=ALERT_RED)
            self.trigger_detonation()
            self.draw()
        else:
            self.status_label.config(text=f"CORRUPTED TIMER: {self.time_left:.1f}s", fg=ALERT_RED)
            
            # Sound Routing: Rapid aggressive siren pulses on clock ticks
            if int(self.time_left * 10) % 5 == 0:
                play_sound_effect("alarm")
                # Trigger a safety-throttled visual tearing glitch
                if self.glitch_manager:
                    self.glitch_manager.trigger_throttled_global_glitch(duration=120, magnitude=0.4, min_interval=1.0)
                    
            self.timer_event_id = self.after(100, self.tick_corrupted_timer)

    def get_cell_coords(self, event):
        c = event.x // self.cell_size
        r = event.y // self.cell_size
        return r, c

    def on_left_click(self, event):
        if self.game_over_state or self.victory_state:
            self.reset_game()
            return
            
        r, c = self.get_cell_coords(event)
        if not (0 <= r < self.rows and 0 <= c < self.cols):
            return

        if self.flagged[r][c] or self.revealed[r][c]:
            return

        # Minesweeper Thread Lock: cleanly reset the Tier 4 countdown timer
        if self.difficulty == 4 and self.mines_planted:
            if getattr(self, 'timer_event_id', None) is not None:
                self.after_cancel(self.timer_event_id)
                self.timer_event_id = None

        play_sound_effect("click")
        if not self.mines_planted:
            self.plant_mines(r, c)
            self.reveal_cell(r, c)
            self.check_victory()
        else:
            if self.grid[r][c] == -1:
                self.trigger_detonation()
            else:
                self.reveal_cell(r, c)
                self.check_victory()
                # Refresh Tier 4 clock loop cleanly
                if self.difficulty == 4 and not self.victory_state and not self.game_over_state:
                    self.start_corrupted_timer()
        self.draw()

    def on_right_click(self, event):
        if self.game_over_state or self.victory_state:
            return
            
        r, c = self.get_cell_coords(event)
        if not (0 <= r < self.rows and 0 <= c < self.cols):
            return

        if self.revealed[r][c]:
            return

        play_sound_effect("beep")
        self.flagged[r][c] = not self.flagged[r][c]
        
        # Reset and refresh corrupted timer cleanly on flagging cells
        if self.difficulty == 4 and self.mines_planted:
            self.start_corrupted_timer()
            
        self.draw()

    def reveal_cell(self, r, c):
        if self.revealed[r][c]:
            return
        self.revealed[r][c] = True
        
        # Auto expansion for zero cells
        if self.grid[r][c] == 0:
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.rows and 0 <= nc < self.cols:
                        if not self.revealed[nr][nc]:
                            self.reveal_cell(nr, nc)

    def trigger_detonation(self):
        self.game_over_state = True
        self.status_label.config(text="EXPLOSION DETECTED! DETONATION", fg=ALERT_RED)
        play_sound_effect("explosion")
        
        # Minesweeper Thread Lock: Cancel active clock tick cleanly on detonation
        if getattr(self, 'timer_event_id', None) is not None:
            self.after_cancel(self.timer_event_id)
            self.timer_event_id = None
            
        # Shake screen animation
        self.shake_screen(12)
        
        # Reveal all mines
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] == -1:
                    self.revealed[r][c] = True

    def shake_screen(self, count):
        if count <= 0:
            self.canvas.place(x=0, y=0)
            return
        dx = random.choice([-10, 10, 0])
        dy = random.choice([-10, 10])
        self.canvas.place(x=dx, y=dy)
        self.after(35, lambda: self.shake_screen(count - 1))

    def check_victory(self):
        unrevealed_safe = 0
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] != -1 and not self.revealed[r][c]:
                    unrevealed_safe += 1
        if unrevealed_safe == 0:
            self.victory_state = True
            
            # Cancel Tier 4 timer cleanly on victory
            if getattr(self, 'timer_event_id', None) is not None:
                self.after_cancel(self.timer_event_id)
                self.timer_event_id = None
                
            self.status_label.config(text="VICTORY! FIREWORKS SECURED", fg=FG_CYAN if self.difficulty != 4 else ALERT_RED)
            play_sound_effect("beep")
            
            if getattr(self, "start_time", None) is not None:
                elapsed_time = int(time.time() - self.start_time)
            else:
                elapsed_time = 0
                
            self.draw()
            
            from leaderboard import check_and_intercept_score
            check_and_intercept_score(self, "DEFUSE FIREWORK", self.difficulty, elapsed_time)

    def draw(self):
        self.canvas.delete("all")
        
        # Adaptive font sizes to prevent text clipping in micro-cells
        font_sizes = {8: 12, 12: 11, 16: 9, 32: 6}
        f_size = font_sizes.get(self.cols, 9)
        f_style = ("Courier", f_size, "bold")
        
        for r in range(self.rows):
            for c in range(self.cols):
                x1 = c * self.cell_size
                y1 = r * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size

                if self.revealed[r][c]:
                    if self.grid[r][c] == -1:
                        # Crimson explosion highlights on Level 4
                        bg_col = ALERT_RED if self.difficulty == 4 else ALERT_RED
                        self.canvas.create_rectangle(x1, y1, x2, y2, fill=bg_col, outline="#222222")
                        self.canvas.create_text(x1 + self.cell_size//2, y1 + self.cell_size//2, text="*", fill=BG_DARK, font=f_style)
                    else:
                        self.canvas.create_rectangle(x1, y1, x2, y2, fill="#151515", outline="#333333")
                        if self.grid[r][c] > 0:
                            colors = ["", FG_CYAN, FG_GREEN, FG_MAGENTA, FG_YELLOW, "#ff7f00", "#ff0000", "#ffffff", "#aaaaaa"]
                            col = ALERT_RED if self.difficulty == 4 else colors[min(self.grid[r][c], 8)]
                            self.canvas.create_text(x1 + self.cell_size//2, y1 + self.cell_size//2 + 1, text=str(self.grid[r][c]), fill=col, font=f_style)
                else:
                    # Draw 3D bevel blocks (using adaptive color offsets)
                    block_color = "#1a0000" if self.difficulty == 4 else "#333333"
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill=block_color, outline="")
                    
                    highlight_col = ALERT_RED if self.difficulty == 4 else "#ffffff"
                    shadow_col = "#050000" if self.difficulty == 4 else "#111111"
                    
                    self.canvas.create_line(x1, y1, x2, y1, fill=highlight_col)
                    self.canvas.create_line(x1, y1, x1, y2, fill=highlight_col)
                    self.canvas.create_line(x1, y2-1, x2, y2-1, fill=shadow_col)
                    self.canvas.create_line(x2-1, y1, x2-1, y2, fill=shadow_col)

                    # Draw hazard flag (flashing warning crimson on Level 4)
                    if self.flagged[r][c]:
                        self.canvas.create_text(x1 + self.cell_size//2, y1 + self.cell_size//2, text="!", fill=ALERT_RED if self.difficulty == 4 else FG_MAGENTA, font=f_style)

        # Overlay states
        if self.game_over_state:
            border_col = ALERT_RED if self.difficulty == 4 else ALERT_RED
            self.canvas.create_rectangle(20, self.height//2 - 40, self.width - 20, self.height//2 + 40, fill=BG_DARK, outline=border_col, width=2)
            self.canvas.create_text(self.width//2, self.height//2 - 15, text="SYSTEM DETONATED", fill=border_col, font=("Courier", 11, "bold"))
            self.canvas.create_text(self.width//2, self.height//2 + 15, text="CLICK TO ATTEMPT DISARM AGAIN", fill=FG_YELLOW, font=("Courier", 9))
        elif self.victory_state:
            border_col = ALERT_RED if self.difficulty == 4 else FG_GREEN
            self.canvas.create_rectangle(20, self.height//2 - 40, self.width - 20, self.height//2 + 40, fill=BG_DARK, outline=border_col, width=2)
            self.canvas.create_text(self.width//2, self.height//2 - 15, text="CARTEL SECURITY BYPASSED", fill=border_col, font=("Courier", 11, "bold"))
            self.canvas.create_text(self.width//2, self.height//2 + 15, text="CLICK TO ENTER NEXT MATRIX LAYER", fill=FG_YELLOW, font=("Courier", 9))

    def destroy(self):
        # Minesweeper Thread Lock: Clean teardown safety release
        if getattr(self, 'timer_event_id', None) is not None:
            try:
                self.after_cancel(self.timer_event_id)
            except Exception:
                pass
            self.timer_event_id = None
        super().destroy()

# ==============================================================================
# INDIVIDUAL TAB MODULES A, B, C, D, E
# ==============================================================================

class BooksModule(tk.Frame):
    """Module A: The Bizarre Archive story browser with integrated TTS engine."""
    def __init__(self, parent):
        super().__init__(parent, bg=BG_DARK)
        
        # Border
        self.config(highlightbackground=FG_MAGENTA, highlightthickness=1)
        
        # TTS Engine Tracking Variables
        self.tts_thread = None
        self.is_speaking = False
        
        # Left Panel (Story List)
        self.left_frame = tk.Frame(self, bg=BG_PANEL, width=200)
        self.left_frame.pack(side="left", fill="y", padx=5, pady=5)
        self.left_frame.pack_propagate(False)

        tk.Label(self.left_frame, text="CONTRABAND BINDER", fg=FG_CYAN, bg=BG_PANEL, font=("Courier", 11, "bold")).pack(pady=5)
        
        self.listbox = tk.Listbox(self.left_frame, bg=BG_DARK, fg=FG_GREEN, 
                                  selectbackground=FG_MAGENTA, selectforeground=BG_DARK,
                                  font=("Courier", 10), bd=0, highlightthickness=1, highlightbackground="#333333")
        self.listbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.listbox.bind("<<ListboxSelect>>", self.on_select)

        # Right Panel (Comic Sans Story Reader Pane)
        self.right_frame = tk.Frame(self, bg=BG_DARK)
        self.right_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        # Top Header & TTS Button Control Area
        header_frame = tk.Frame(self.right_frame, bg=BG_DARK)
        header_frame.pack(fill="x", pady=5)
        
        tk.Label(header_frame, text="DECRYPTED STORY STREAM", fg=FG_MAGENTA, bg=BG_DARK, font=("Courier", 11, "bold")).pack(side="left", anchor="w")
        
        # Terminal Voice Synth Playback Button
        self.tts_btn = tk.Button(header_frame, text="▶ SYNTHESIZE VOICE", command=self.toggle_tts,
                                 bg=BG_DARK, fg=FG_GREEN, activebackground=FG_GREEN, activeforeground=BG_DARK,
                                 font=("Courier", 8, "bold"), bd=1, padx=5)
        self.tts_btn.pack(side="right", padx=5)
        
        # Clunky Comic Sans reader (aesthetic friction)
        self.text_widget = tk.Text(self.right_frame, bg=BG_DARK, fg=FG_YELLOW, 
                                   font=("Comic Sans MS", 11), wrap="word", 
                                   highlightthickness=1, highlightbackground=FG_MAGENTA, insertbackground=FG_GREEN,
                                   state="disabled")
        self.text_widget.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.load_stories()
        self.after(1000, self.track_books_time)

    def track_books_time(self):
        if not self.winfo_exists():
            return
        try:
            app = getattr(self.winfo_toplevel(), "app_instance", None)
            if app and app.current_frame is self:
                app.achievement_manager.increment_metric("books_time_seconds", 1)
                if app.achievement_manager.get_metric("books_time_seconds") >= 900:
                    app.achievement_manager.grant_achievement("deep_research")
        except Exception:
            pass
        self.after(1000, self.track_books_time)

    def load_stories(self):
        self.listbox.delete(0, "end")
        if os.path.exists(BOOKS_DIR):
            for filename in os.listdir(BOOKS_DIR):
                if filename.endswith(".txt"):
                    self.listbox.insert("end", filename)

    def on_select(self, event):
        # If a track is already speaking, force-terminate it before switching stories
        if self.is_speaking:
            self.stop_tts_engine()

        selection = self.listbox.curselection()
        if not selection:
            return
        
        play_sound_effect("click")
        filename = self.listbox.get(selection[0])
        filepath = os.path.join(BOOKS_DIR, filename)
        
        # Telemetry: grant Bookworm achievement
        try:
            app = getattr(self.winfo_toplevel(), "app_instance", None)
            if app:
                app.achievement_manager.grant_achievement("bookworm")
        except Exception:
            pass
        
        # Unlock the widget so the code can modify the content
        self.text_widget.config(state="normal")

        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            self.text_widget.delete("1.0", "end")
            self.text_widget.insert("1.0", content)
        except Exception as e:
            self.text_widget.delete("1.0", "end")
            self.text_widget.insert("1.0", f"DECRYPTION ERROR: {e}")
            
        # Relock the widget to keep it strictly read-only for the user
        self.text_widget.config(state="disabled")

    # -------------------------------------------------------------
    # TEXT TO SPEECH AUDIO ENGINE THREADING
    # -------------------------------------------------------------
    def toggle_tts(self):
        play_sound_effect("click")
        if self.is_speaking:
            self.stop_tts_engine()
        else:
            story_text = self.text_widget.get("1.0", "end-1c").strip()
            if story_text and not story_text.startswith("DECRYPTION ERROR"):
                self.start_tts_engine(story_text)

    def start_tts_engine(self, text):
        self.is_speaking = True
        self.tts_btn.config(text="■ TERMINATE VOICE", fg=ALERT_RED)
        
        # Spawn safe independent worker thread to insulate loop rendering
        self.tts_thread = threading.Thread(target=self._tts_worker, args=(text,), daemon=True)
        self.tts_thread.start()

    def _tts_worker(self, text):
        try:
            # Localize initialization inside the worker loop context
            engine = pyttsx3.init()
            
            # Tweak speech properties to match a cold, hacker terminal aesthetic
            engine.setProperty('rate', 165)  # Slightly slower, distinct speech cadence
            engine.setProperty('volume', 0.9)
            
            # Monitor engine execution block
            engine.say(text)
            
            # Inner check wrapper loop prevents trailing process hangs
            while self.is_speaking:
                engine.runAndWait()
                break
        except Exception:
            pass
        finally:
            # Re-align UI buttons back to default resting state safely using standard Tkinter lifecycle hooks
            self.after(0, self._reset_tts_ui)

    def stop_tts_engine(self):
        self.is_speaking = False
        # Instantly breaks loop processing inside pyttsx3 frame context
        try:
            dummy_engine = pyttsx3.init()
            dummy_engine.stop()
        except Exception:
            pass
        self._reset_tts_ui()

    def _reset_tts_ui(self):
        self.is_speaking = False

        if hasattr(self, 'tts_btn') and self.tts_btn.winfo_exists():
            self.tts_btn.config(text="▶ SYNTHESIZE VOICE", fg=FG_GREEN)
        
    def destroy(self):
        """Standard lifecycle hook cleanup override when switching frames."""
        self.stop_tts_engine()
        super().destroy()

class WaveformVisualizer(tk.Canvas):
    """Real-time, SoundCloud-style Waveform Visualizer using Canvas rects."""
    def __init__(self, parent, num_bars=50, bg=BG_DARK, bar_color_unplayed="#224444", **kwargs):
        super().__init__(parent, bg=bg, highlightthickness=0, height=45, **kwargs)
        self.num_bars = num_bars
        self.bar_color_unplayed = bar_color_unplayed
        
        self.bar_ids = []
        # Pre-generate random base heights representing the track's structure (between 0.15 and 0.85 of canvas height)
        self.base_heights = [random.uniform(0.15, 0.85) for _ in range(self.num_bars)]
        
        self.progress_provider = None
        self.animation_job = None
        self.t = 0.0
        
        # Pre-calculate active gradient colors transitioning from FG_GREEN to FG_MAGENTA
        self.active_colors = []
        for i in range(self.num_bars):
            ratio = i / (self.num_bars - 1) if self.num_bars > 1 else 0.0
            r = int(255 * ratio)
            g = int(255 * (1.0 - ratio))
            b = int(255 * ratio)
            self.active_colors.append(f"#{r:02x}{g:02x}{b:02x}")
            
        self.bind("<Configure>", lambda event: self.redraw_bars())

    def set_progress_provider(self, provider):
        self.progress_provider = provider

    def redraw_bars(self):
        for bar_id in self.bar_ids:
            self.delete(bar_id)
        self.bar_ids.clear()
        
        w = self.winfo_width()
        h = self.winfo_height()
        if w <= 1 or h <= 1:
            return
            
        gap = 2
        bar_w = (w - (self.num_bars - 1) * gap) / self.num_bars
        if bar_w < 1:
            bar_w = 1
            
        mid_y = h / 2
        for i in range(self.num_bars):
            x0 = i * (bar_w + gap)
            x1 = x0 + bar_w
            half_len = (h * self.base_heights[i]) / 2
            y0 = mid_y - half_len
            y1 = mid_y + half_len
            
            rect_id = self.create_rectangle(x0, y0, x1, y1, fill=self.bar_color_unplayed, outline="")
            self.bar_ids.append(rect_id)

    def start_animation(self):
        if not self.animation_job:
            self.update_waveform()

    def stop_animation(self):
        if self.animation_job:
            self.after_cancel(self.animation_job)
            self.animation_job = None

    def destroy(self):
        self.stop_animation()
        super().destroy()

    def update_waveform(self):
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return

        self.animation_job = self.after(50, self.update_waveform)
        
        is_playing = False
        progress_ratio = 0.0
        
        try:
            is_playing = pygame.mixer.music.get_busy()
        except Exception:
            pass
            
        if self.progress_provider:
            if hasattr(self.progress_provider, 'playing'):
                is_playing = is_playing and self.progress_provider.playing
            
            if (hasattr(self.progress_provider, 'elapsed_time') and 
                hasattr(self.progress_provider, 'song_length') and 
                self.progress_provider.song_length > 0):
                progress_ratio = self.progress_provider.elapsed_time / self.progress_provider.song_length
                
        progress_ratio = max(0.0, min(1.0, progress_ratio))
        progress_index = int(progress_ratio * self.num_bars)
        
        try:
            h = self.winfo_height()
            w = self.winfo_width()
            if w <= 1 or h <= 1:
                return
                
            gap = 2
            bar_w = (w - (self.num_bars - 1) * gap) / self.num_bars
            if bar_w < 1:
                bar_w = 1
                
            mid_y = h / 2
            self.t += 0.1
            
            if len(self.bar_ids) != self.num_bars:
                self.redraw_bars()
                if len(self.bar_ids) != self.num_bars:
                    return
                    
            for i in range(self.num_bars):
                rect_id = self.bar_ids[i]
                base_height = self.base_heights[i]
                
                if is_playing:
                    modulation = 0.55 + 0.45 * math.sin(self.t * 3.5 + i * 0.3) * math.cos(self.t * 1.8 - i * 0.1)
                    jitter = random.uniform(0.8, 1.2)
                    current_height = base_height * modulation * jitter
                else:
                    current_height = 0.05
                    
                current_height = max(0.02, min(0.95, current_height))
                
                x0 = i * (bar_w + gap)
                x1 = x0 + bar_w
                half_len = (h * current_height) / 2
                y0 = mid_y - half_len
                y1 = mid_y + half_len
                
                self.coords(rect_id, x0, y0, x1, y1)
                
                if i < progress_index:
                    color = self.active_colors[i]
                else:
                    color = self.bar_color_unplayed
                    
                self.itemconfig(rect_id, fill=color)
        except Exception:
            pass


class MusicModule(tk.Frame):
    """Module B: The Shady Media Player with a progress bar that hangs at 99%."""
    def __init__(self, parent):
        super().__init__(parent, bg=BG_DARK)
        self.config(highlightbackground=FG_MAGENTA, highlightthickness=1)

        self.current_song = None
        self.playing = False
        self.song_length = 0.0  # Duration in seconds
        self.elapsed_time = 0.0  # Time played in seconds
        self.hang_bar = False    # Trigger to hang at 99%
        self.continuous_play_time = 0.0


        # Layout
        # Left Side (Song Catalog)
        self.catalog_frame = tk.Frame(self, bg=BG_PANEL, width=200)
        self.catalog_frame.pack(side="left", fill="y", padx=5, pady=5)
        self.catalog_frame.pack_propagate(False)

        tk.Label(self.catalog_frame, text="SONIC CONTRABAND", fg=FG_CYAN, bg=BG_PANEL, font=("Courier", 11, "bold")).pack(pady=5)
        
        self.listbox = tk.Listbox(self.catalog_frame, bg=BG_DARK, fg=FG_GREEN,
                                  selectbackground=FG_CYAN, selectforeground=BG_DARK,
                                  font=("Courier", 10), bd=0, highlightthickness=1, highlightbackground="#333333")
        self.listbox.pack(fill="both", expand=True, padx=5, pady=5)

        # Upload External Audio Button
        self.upload_btn = BrokenImageButton(self.catalog_frame, text="IMPORT AUDIO DATA", command=self.import_audio_file)
        self.upload_btn.pack(fill="x", padx=5, pady=5)

        # Right Side (Controls & Glitchy Progress Bar)
        self.control_frame = tk.Frame(self, bg=BG_DARK)
        self.control_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        tk.Label(self.control_frame, text="AUDIO DECRYPTION CORE", fg=FG_MAGENTA, bg=BG_DARK, font=("Courier", 12, "bold")).pack(anchor="w", pady=5)

        # Display track info
        self.info_label = tk.Label(self, text="PLAYER IDLE // NO CARRIER DETECTED", fg=FG_YELLOW, bg=BG_DARK, font=("Courier", 10, "italic"))
        self.control_frame.add_label = self.info_label # attach
        self.info_label.pack(anchor="w", pady=10)

        # Controls panel
        self.btns_frame = tk.Frame(self.control_frame, bg=BG_DARK)
        self.btns_frame.pack(anchor="w", pady=10)

        self.play_btn = tk.Button(self.btns_frame, text="EXECUTE AUDIO CONTRABAND", command=self.play_music,
                                  bg=BG_PANEL, fg=FG_GREEN, activebackground=FG_GREEN, activeforeground=BG_DARK,
                                  font=("Courier", 9, "bold"), bd=1, highlightbackground=FG_GREEN)
        self.play_btn.pack(side="left", padx=5)

        self.pause_btn = tk.Button(self.btns_frame, text="HALT SONIC FREQUENCIES", command=self.pause_music,
                                   bg=BG_PANEL, fg=FG_YELLOW, activebackground=FG_YELLOW, activeforeground=BG_DARK,
                                   font=("Courier", 9, "bold"), bd=1, highlightbackground=FG_YELLOW)
        self.pause_btn.pack(side="left", padx=5)

        self.stop_btn = tk.Button(self.btns_frame, text="TERMINATE SIGNAL", command=self.stop_music,
                                  bg=BG_PANEL, fg=ALERT_RED, activebackground=ALERT_RED, activeforeground=BG_DARK,
                                  font=("Courier", 9, "bold"), bd=1, highlightbackground=ALERT_RED)
        self.stop_btn.pack(side="left", padx=5)

        # Hanging Progress Bar (Canvas blocks)
        tk.Label(self.control_frame, text="DOWNLOAD/BUFFER STATUS:", fg=FG_CYAN, bg=BG_DARK, font=("Courier", 10)).pack(anchor="w", pady=(15, 2))
        
        self.bar_canvas = tk.Canvas(self.control_frame, height=35, bg=BG_PANEL, highlightthickness=1, highlightbackground=FG_CYAN)
        self.bar_canvas.pack(fill="x", padx=5, pady=5)
        
        self.percent_label = tk.Label(self.control_frame, text="BUFFER LEVEL: 0%", fg=FG_GREEN, bg=BG_DARK, font=("Courier", 9, "bold"))
        self.percent_label.pack(anchor="w", padx=5)

        # Waveform Visualizer
        tk.Label(self.control_frame, text="SONIC WAVEFORM VISUALIZER:", fg=FG_CYAN, bg=BG_DARK, font=("Courier", 10)).pack(anchor="w", pady=(15, 2))
        self.visualizer = WaveformVisualizer(self.control_frame, num_bars=50, bg=BG_DARK)
        self.visualizer.set_progress_provider(self)
        self.visualizer.pack(fill="x", padx=5, pady=5)
        self.visualizer.start_animation()

        self.load_music_list()
        self.update_progress_loop()

    def load_music_list(self):
        self.listbox.delete(0, "end")
        if os.path.exists(MUSIC_DIR):
            for file in os.listdir(MUSIC_DIR):
                if file.endswith((".wav", ".mp3")):
                    self.listbox.insert("end", file)

    def import_audio_file(self):
        """Allows uploading an external .wav or .mp3 directly to the application directory."""
        filepath = filedialog.askopenfilename(filetypes=[("Audio Files", "*.wav;*.mp3")])
        if filepath:
            filename = os.path.basename(filepath)
            dest = os.path.join(MUSIC_DIR, filename)
            try:
                import shutil
                shutil.copy(filepath, dest)
                self.load_music_list()
                play_sound_effect("beep")
                messagebox.showinfo("CHAOHUB ENCLAVE", "Contraband file uploaded successfully.")
            except Exception as e:
                messagebox.showerror("CHAOHUB ERROR", f"Failed to ingest file: {e}")

    def play_music(self):
        selection = self.listbox.curselection()
        if not selection:
            return

        play_sound_effect("click")
        song_name = self.listbox.get(selection[0])
        song_path = os.path.join(MUSIC_DIR, song_name)

        try:
            # Query duration using wave module for wav files, fallback for MP3
            if song_name.endswith(".wav"):
                with wave.open(song_path, 'r') as w:
                    self.song_length = w.getnframes() / w.getframerate()
            else:
                # Mock duration for mp3 if wave cannot read it
                self.song_length = 180.0

            pygame.mixer.music.load(song_path)
            pygame.mixer.music.play()
            
            self.current_song = song_name
            self.playing = True
            self.elapsed_time = 0.0
            self.hang_bar = False
            self.continuous_play_time = 0.0
            self.info_label.config(text=f"DECRYPTING & STREAMING: {song_name.upper()}", fg=FG_GREEN)
            
            # Telemetry: unique played song tracking for Audiophile
            try:
                app = getattr(self.winfo_toplevel(), "app_instance", None)
                if app:
                    app.achievement_manager.add_unique_metric("audio_files_played", song_name)
                    if len(app.achievement_manager.get_metric("audio_files_played")) >= 10:
                        app.achievement_manager.grant_achievement("audiophile")
            except Exception:
                pass
        except Exception as e:
            self.info_label.config(text=f"STREAMING FAILED: {e}", fg=ALERT_RED)

    def pause_music(self):
        if self.playing:
            pygame.mixer.music.pause()
            self.playing = False
            self.continuous_play_time = 0.0
            self.info_label.config(text="SIGNAL PAUSED BY HOST", fg=FG_YELLOW)
        else:
            pygame.mixer.music.unpause()
            self.playing = True
            self.continuous_play_time = 0.0
            if self.current_song:
                self.info_label.config(text=f"DECRYPTING & STREAMING: {self.current_song.upper()}", fg=FG_GREEN)

    def stop_music(self):
        pygame.mixer.music.stop()
        self.playing = False
        self.elapsed_time = 0.0
        self.hang_bar = False
        self.continuous_play_time = 0.0
        self.info_label.config(text="PLAYER IDLE // NO CARRIER DETECTED", fg=FG_YELLOW)

    def update_progress_loop(self):
        try:
            if self.playing and self.song_length > 0:
                # increment elapsed time (approximate, running every 100ms)
                self.elapsed_time += 0.1
                
                # Check actual playback completion
                if not pygame.mixer.music.get_busy():
                    self.playing = False
                    self.elapsed_time = 0.0
                    self.hang_bar = False
                    self.continuous_play_time = 0.0
                    self.info_label.config(text="PLAYBACK TERMINATED", fg=FG_CYAN)
                else:
                    self.continuous_play_time += 0.1
                    if self.continuous_play_time >= 1800.0:
                        try:
                            app = getattr(self.winfo_toplevel(), "app_instance", None)
                            if app:
                                app.achievement_manager.grant_achievement("continuous_stream")
                        except Exception:
                            pass

                raw_percent = (self.elapsed_time / self.song_length) * 100.0
                
                # Clunky Hack: progress bar gets stuck at 99% and blinks, despite playing fine
                if raw_percent >= 99.0:
                    raw_percent = 99.0
                    self.hang_bar = True
                
                self.draw_bar(raw_percent)
            elif not self.playing and self.elapsed_time == 0:
                self.draw_bar(0)

            self.after(100, self.update_progress_loop)
        except Exception:
            pass

    def draw_bar(self, percentage):
        self.bar_canvas.delete("all")
        width = self.bar_canvas.winfo_width()
        if width <= 1:
            width = 400
            
        fill_width = int((percentage / 100.0) * (width - 10))
        
        # Draw segmented green blocks (1998 browser look)
        block_width = 12
        spacing = 4
        num_blocks = fill_width // (block_width + spacing)
        
        color = FG_GREEN
        if self.hang_bar:
            # Blink between magenta and cyan to lock down visual glitch
            color = FG_CYAN if (int(time.time() * 4) % 2 == 0) else FG_MAGENTA
            self.percent_label.config(text="BUFFER LEVEL: 99% (CONNECTION HUNG... CONTINUING AUDIO)", fg=color)
        else:
            self.percent_label.config(text=f"BUFFER LEVEL: {int(percentage)}%", fg=FG_GREEN)

        for i in range(num_blocks):
            x1 = 5 + i * (block_width + spacing)
            y1 = 5
            x2 = x1 + block_width
            y2 = 30
            self.bar_canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")


class PodcastsModule(tk.Frame):
    """Module C: Deep-Web Radio Station player and Zalgo-glitched RSS Scraper."""
    def __init__(self, parent):
        super().__init__(parent, bg=BG_DARK)
        self.config(highlightbackground=FG_MAGENTA, highlightthickness=1)

        # State tracking for visualizer progress
        self.playing = False
        self.elapsed_time = 0.0
        self.song_length = 0.0

        # Left Side (Mock Radio Channels)
        self.left_frame = tk.Frame(self, bg=BG_PANEL, width=220)
        self.left_frame.pack(side="left", fill="y", padx=5, pady=5)
        self.left_frame.pack_propagate(False)

        tk.Label(self.left_frame, text="INTERCEPTED RADIO", fg=FG_CYAN, bg=BG_PANEL, font=("Courier", 11, "bold")).pack(pady=5)

        presets = [
            ("98.1: MODEM BEAT", "boot_dialup"),
            ("66.6: DARK BROADCAST", "intercepted_shortwave_66"),
            ("108.0: MAINFRAME BEAT", "cyber_laser_march")
        ]

        for label, sound_file in presets:
            btn = tk.Button(self.left_frame, text=label, command=lambda s=sound_file: self.play_preset(s),
                            bg=BG_DARK, fg=FG_YELLOW, activebackground=FG_YELLOW, activeforeground=BG_DARK,
                            font=("Courier", 10, "bold"), bd=1, highlightbackground=FG_YELLOW)
            btn.pack(fill="x", padx=10, pady=8)

        # THE NEW RADICAL KILL SWITCH BUTTON
        self.stop_btn = tk.Button(self.left_frame, text="⚡ TERMINATE FREQUENCY ⚡", command=self.stop_radio,
                                  bg=BG_DARK, fg=ALERT_RED, activebackground=ALERT_RED, activeforeground=BG_DARK,
                                  font=("Courier", 9, "bold"), bd=1, highlightbackground=ALERT_RED)
        self.stop_btn.pack(fill="x", padx=10, pady=15)

        self.radio_label = tk.Label(self.left_frame, text="TUNING DIAL: STATIC", fg=FG_GREEN, bg=BG_PANEL, font=("Courier", 9, "bold"))
        self.radio_label.pack(pady=5)

        # Waveform Visualizer for Radio
        self.visualizer = WaveformVisualizer(self.left_frame, num_bars=30, bg=BG_PANEL)
        self.visualizer.set_progress_provider(self)
        self.visualizer.pack(fill="x", padx=10, pady=5)
        self.visualizer.start_animation()

        # Start background progress loop
        self.update_progress_loop()

        # Right Side (RSS glitch text scraper)
        self.right_frame = tk.Frame(self, bg=BG_DARK)
        self.right_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        tk.Label(self.right_frame, text="RSS SCRAMBLER PRO", fg=FG_MAGENTA, bg=BG_DARK, font=("Courier", 11, "bold")).pack(anchor="w", pady=5)

        # RSS Presets / Inputs
        self.input_frame = tk.Frame(self.right_frame, bg=BG_DARK)
        self.input_frame.pack(fill="x", pady=5)

        # Predefined cyber security feed
        self.feed_var = tk.StringVar(value="https://news.ycombinator.com/rss")
        self.entry = tk.Entry(self.input_frame, textvariable=self.feed_var, bg=BG_PANEL, fg=FG_GREEN, 
                              font=("Courier", 10), bd=1, highlightbackground=FG_GREEN, insertbackground=FG_GREEN)
        self.entry.pack(side="left", fill="x", expand=True, padx=5)

        # Broken Image button layout for Fetching RSS
        self.fetch_btn = BrokenImageButton(self.input_frame, text="SCRAPE RADIO DATA", command=self.fetch_rss)
        self.fetch_btn.pack(side="right", padx=5)

        # List Box showing scraped items
        self.listbox = tk.Listbox(self.right_frame, bg=BG_PANEL, fg=FG_GREEN,
                                  selectbackground=FG_MAGENTA, selectforeground=BG_DARK,
                                  font=("Courier", 10), bd=0, highlightthickness=1, highlightbackground="#333333")
        self.listbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.listbox.bind("<<ListboxSelect>>", self.on_feed_select)

        # Item content reader
        self.desc_text = tk.Text(self.right_frame, height=5, bg=BG_DARK, fg=FG_YELLOW,
                                 font=("Courier", 9), wrap="word", highlightthickness=1, highlightbackground=FG_CYAN)
        self.desc_text.pack(fill="x", padx=5, pady=5)

        self.scraped_items = []

    def play_preset(self, filename):
        play_sound_effect("click")
        path = os.path.join(PODCASTS_DIR, f"{filename}.wav")
        if not os.path.exists(path):
            path = os.path.join(SOUNDS_DIR, f"{filename}.wav")
            if not os.path.exists(path):
                path = os.path.join(MUSIC_DIR, f"{filename}.wav")

        if os.path.exists(path):
            try:
                # Query duration to set progress bounds
                try:
                    with wave.open(path, 'r') as w:
                        self.song_length = w.getnframes() / w.getframerate()
                except Exception:
                    self.song_length = 30.0  # Default fallback if not standard wav

                pygame.mixer.music.load(path)
                pygame.mixer.music.play(-1) # Loop radio preset
                
                self.elapsed_time = 0.0
                self.playing = True
                self.radio_label.config(text=f"TUNING DIAL: {filename.upper()}", fg=FG_CYAN)
            except Exception as e:
                self.playing = False
                self.radio_label.config(text="TUNING FAULT: DISMISS", fg=ALERT_RED)
        else:
            self.playing = False
            self.radio_label.config(text="FREQUENCY GONE COLD", fg=FG_YELLOW)

    # THE NEW STOP FUNCTION
    def stop_radio(self):
        """Force-kills the running background audio loop stream."""
        try:
            play_sound_effect("explosion") # Give them a funny explosion cue for pulling the plug
            pygame.mixer.music.stop()
            self.radio_label.config(text="TUNING DIAL: DEAD AIR", fg=ALERT_RED)
            self.playing = False
            self.elapsed_time = 0.0
        except Exception:
            pass

    def update_progress_loop(self):
        try:
            if self.playing and self.song_length > 0:
                self.elapsed_time += 0.1
                # Looped playback progress wrap-around
                if self.elapsed_time >= self.song_length:
                    self.elapsed_time = 0.0
                    
                if not pygame.mixer.music.get_busy():
                    self.playing = False
                    self.elapsed_time = 0.0
                    self.radio_label.config(text="TUNING DIAL: DEAD AIR", fg=ALERT_RED)
            
            self.after(100, self.update_progress_loop)
        except Exception:
            pass

    def fetch_rss(self):
        url = self.feed_var.get()
        self.desc_text.delete("1.0", "end")
        self.desc_text.insert("1.0", "POLLING TRANSMISSION NETWORK...")
        
        # Telemetry: static surfer achievement fetch count
        try:
            app = getattr(self.winfo_toplevel(), "app_instance", None)
            if app:
                app.achievement_manager.increment_metric("rss_fetch_count", 1)
                if app.achievement_manager.get_metric("rss_fetch_count") >= 5:
                    app.achievement_manager.grant_achievement("static_surfer")
        except Exception:
            pass
        
        # Run RSS fetch in a background thread to prevent UI freezing
        threading.Thread(target=self._async_fetch, args=(url,), daemon=True).start()

    def _async_fetch(self, url):
        items = []
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ChaoHub/1.0'})
            # Short timeout to failover to local offline mock feed quickly if no internet
            with urllib.request.urlopen(req, timeout=3.5) as response:
                xml_data = response.read()
            
            root_xml = ET.fromstring(xml_data)
            for item in root_xml.findall('.//item'):
                title = item.find('title')
                link = item.find('link')
                desc = item.find('description')
                
                title_text = title.text if title is not None else "UNKNOWN WIRE DATA"
                link_text = link.text if link is not None else ""
                desc_text = desc.text if desc is not None else ""
                
                items.append({
                    'title': title_text,
                    'link': link_text,
                    'desc': desc_text
                })
        except Exception as e:
            # Fallback to local offline mocks if network is down/offline
            items = self.get_offline_mock_feeds(str(e))

        self.scraped_items = items
        self.after(0, self.populate_rss_list)

    def get_offline_mock_feeds(self, err):
        return [
            {"title": "NET_ERROR: CONNECTION TIMED OUT", "link": "", "desc": f"Intrusion matrix failed to fetch remote RSS. Socket reports: {err}"},
            {"title": "FIREWORK COINS SURGE 4500%", "link": "http://chaonet.dark", "desc": "Volatile cryptocurrency FireworkCoins hits record highs. Black market firework warehouses reporting massive sales surges."},
            {"title": "SMART FIREWORK INFRASTRUCTURE COMPROMISED", "link": "http://chaonet.dark", "desc": "Reports from the ground indicate Sparky the Firework AI has locked control channels. Decryption ongoing."},
            {"title": "NUMBERS STATION TRANSMISSION DECRYPTED", "link": "http://chaonet.dark", "desc": "Station code: 42-12-88-00. Translation reads: 'THE SPAGHETTI DAEMON WALKS AT MIDNIGHT.' Use caution."},
            {"title": "SURREAL DIALUP DREAM REPORTED IN MULTIPLE HOSTS", "link": "http://chaonet.dark", "desc": "A new mental malware is infecting sleep nodes across port 1337. Patients dream entirely in 56k static."}
        ]

    def populate_rss_list(self):
        self.listbox.delete(0, "end")
        for item in self.scraped_items:
            # Glitch text titles through Zalgo diacritics
            glitched_title = zalgo_glitch_text(item['title'])
            self.listbox.insert("end", glitched_title)
        self.desc_text.delete("1.0", "end")
        self.desc_text.insert("1.0", f"DECRYPTION COMPLETE. FOUND {len(self.scraped_items)} SIGNALS.")

    def on_feed_select(self, event):
        selection = self.listbox.curselection()
        if not selection:
            return
        
        play_sound_effect("click")
        idx = selection[0]
        item = self.scraped_items[idx]
        
        self.desc_text.delete("1.0", "end")
        desc = item['desc']
        # Clean basic HTML tags from descriptions
        for tag in ["<p>", "</p>", "<br>", "<br/>", "<b>", "</b>"]:
            desc = desc.replace(tag, "")
        self.desc_text.insert("1.0", f"LINK: {item['link']}\n\nSUMMARY:\n{desc}")


class WidgetsModule(tk.Frame):
    """Module D: Desktop Distractions containing Pomodoro Extortion Timer and Intrusion Visuals."""
    def __init__(self, parent, main_shell):
        super().__init__(parent, bg=BG_DARK)
        self.main_shell = main_shell
        self.config(highlightbackground=FG_MAGENTA, highlightthickness=1)

        # Grid system: Left side widgets, Right side monitor
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # -------------------------------------------------------------
        # LEFT PANEL: CONTAINER FRAME FOR BOTH TIMERS
        # -------------------------------------------------------------
        left_container = tk.Frame(self, bg=BG_DARK)
        left_container.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        left_container.rowconfigure(0, weight=1)
        left_container.rowconfigure(1, weight=1)
        left_container.columnconfigure(0, weight=1)

        # POMODORO TIMER PANEL
        self.pomo_frame = tk.Frame(left_container, bg=BG_PANEL, highlightthickness=1, highlightbackground=FG_CYAN)
        self.pomo_frame.grid(row=0, column=0, padx=0, pady=(0, 5), sticky="nsew")

        tk.Label(self.pomo_frame, text="POMODORO EXTORTION CLOCK", fg=FG_CYAN, bg=BG_PANEL, font=("Courier", 11, "bold")).pack(pady=10)

        self.timer_seconds = 25 * 60
        self.timer_running = False

        self.clock_label = tk.Label(self.pomo_frame, text="25:00", fg=FG_GREEN, bg=BG_DARK, 
                                    font=("Courier", 24, "bold"), width=8, highlightthickness=1, highlightbackground=FG_GREEN)
        self.clock_label.pack(pady=10)

        # Controls panel
        pomo_btn_frame = tk.Frame(self.pomo_frame, bg=BG_PANEL)
        pomo_btn_frame.pack(pady=5)

        self.start_pomo_btn = tk.Button(pomo_btn_frame, text="INITIATE TASK CYCLE", command=self.toggle_pomo,
                                        bg=BG_DARK, fg=FG_GREEN, activebackground=FG_GREEN, activeforeground=BG_DARK,
                                        font=("Courier", 8, "bold"), bd=1)
        self.start_pomo_btn.pack(side="left", padx=5)

        self.reset_pomo_btn = tk.Button(pomo_btn_frame, text="ABORT TASK CYCLE", command=self.reset_pomo,
                                        bg=BG_DARK, fg=ALERT_RED, activebackground=ALERT_RED, activeforeground=BG_DARK,
                                        font=("Courier", 8, "bold"), bd=1)
        self.reset_pomo_btn.pack(side="left", padx=5)

        # Fast forward debug button
        self.debug_btn = tk.Button(self.pomo_frame, text="[TEST CARTEL LOCK - FAST FORWARD 1 SEC]", command=self.fast_forward_pomo,
                                   bg=BG_DARK, fg=FG_MAGENTA, activebackground=FG_MAGENTA, activeforeground=BG_DARK,
                                   font=("Courier", 7, "bold"), bd=1)
        self.debug_btn.pack(pady=8)

        # Firework Price Marquee Ticker at the bottom of the Pomodoro panel
        tk.Label(self.pomo_frame, text="BLACK MARKET CONTRABAND INDEX", fg=FG_YELLOW, bg=BG_PANEL, font=("Courier", 8, "bold")).pack(pady=(10, 2))
        ticker_items = [
            "BLACK_DRAGON_CRATES: 450.23 CC (+15.4%)",
            "RED_DEVIL_SPARKLERS: 12.04 CC (-45.2%)",
            "SYNTHETIC_SULFUR_TONS: 1400.99 CC (+2.1%)",
            "CHAO_COIN: $0.00034 (-12%)",
            "MODEM_BBS_SWITCH: 88.00 CC (STABLE)"
        ]
        self.ticker = ScrollingMarquee(self.pomo_frame, ticker_items)
        self.ticker.pack(fill="x", padx=10, pady=5)

        # -------------------------------------------------------------
        # NEW WIDGET: QUANTUM STOPWATCH PANEL
        # -------------------------------------------------------------
        self.sw_frame = tk.Frame(left_container, bg=BG_PANEL, highlightthickness=1, highlightbackground=FG_YELLOW)
        self.sw_frame.grid(row=1, column=0, padx=0, pady=(5, 0), sticky="nsew")

        tk.Label(self.sw_frame, text="TURBO DATA PERFORMANCE CHRONOMETER", fg=FG_YELLOW, bg=BG_PANEL, font=("Courier", 11, "bold")).pack(pady=5)

        # Stopwatch internal variables
        self.sw_elapsed = 0.0
        self.sw_running = False
        self.sw_last_time = 0.0

        self.sw_label = tk.Label(self.sw_frame, text="00:00:00.00", fg=FG_YELLOW, bg=BG_DARK,
                                 font=("Courier", 24, "bold"), width=12, highlightthickness=1, highlightbackground=FG_YELLOW)
        self.sw_label.pack(pady=10)

        sw_btn_frame = tk.Frame(self.sw_frame, bg=BG_PANEL)
        sw_btn_frame.pack(pady=5)

        self.start_sw_btn = tk.Button(sw_btn_frame, text="START RUN", command=self.toggle_stopwatch,
                                      bg=BG_DARK, fg=FG_GREEN, activebackground=FG_GREEN, activeforeground=BG_DARK,
                                      font=("Courier", 8, "bold"), bd=1)
        self.start_sw_btn.pack(side="left", padx=5)

        self.reset_sw_btn = tk.Button(sw_btn_frame, text="WIPE LOG", command=self.reset_stopwatch,
                                      bg=BG_DARK, fg=ALERT_RED, activebackground=ALERT_RED, activeforeground=BG_DARK,
                                      font=("Courier", 8, "bold"), bd=1)
        self.reset_sw_btn.pack(side="left", padx=5)

        # -------------------------------------------------------------
        # RIGHT PANEL: INTRUSION GRAPHICS
        # -------------------------------------------------------------
        self.monitor_frame = tk.Frame(self, bg=BG_PANEL, highlightthickness=1, highlightbackground=FG_MAGENTA)
        self.monitor_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        tk.Label(self.monitor_frame, text="CORE EXPLOIT LOAD GRAPH", fg=FG_MAGENTA, bg=BG_PANEL, font=("Courier", 11, "bold")).pack(pady=10)

        self.canvas = tk.Canvas(self.monitor_frame, bg=BG_DARK, highlightthickness=1, highlightbackground=FG_MAGENTA, height=180)
        self.canvas.pack(fill="both", expand=True, padx=10, pady=5)

        self.graph_points = [80] * 35
        
        # Core execution loops
        self.update_graphics_loop()
        self.run_timer_loop()
        self.run_stopwatch_loop() # Start tracking ticks right out of the gate

    # -------------------------------------------------------------
    # STOPWATCH CONTROL LOGIC
    # -------------------------------------------------------------
    def toggle_stopwatch(self):
        play_sound_effect("click")
        self.sw_running = not self.sw_running
        if self.sw_running:
            self.sw_last_time = time.time()
            self.start_sw_btn.config(text="PAUSE RUN", fg=FG_YELLOW)
        else:
            self.start_sw_btn.config(text="START RUN", fg=FG_GREEN)

    def reset_stopwatch(self):
        play_sound_effect("beep")
        self.sw_running = False
        self.sw_elapsed = 0.0
        self.sw_label.config(text="00:00:00.00")
        self.start_sw_btn.config(text="START RUN", fg=FG_GREEN)

    def run_stopwatch_loop(self):
        try:
            if self.sw_running:
                now = time.time()
                self.sw_elapsed += (now - self.sw_last_time)
                self.sw_last_time = now

                # Extract time fragments
                total_seconds = int(self.sw_elapsed)
                milliseconds = int((self.sw_elapsed - total_seconds) * 100)
                minutes, seconds = divmod(total_seconds, 60)
                hours, minutes = divmod(minutes, 60)

                # Format matching terminal specification
                time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:02d}"
                self.sw_label.config(text=time_str)

            # High precision 10ms update refresh rate for smooth rendering
            self.after(10, self.run_stopwatch_loop)
        except Exception:
            pass

    # -------------------------------------------------------------
    # EXISTING POMODORO & GRAPHICS LOGIC
    # -------------------------------------------------------------
    def toggle_pomo(self):
        play_sound_effect("click")
        self.timer_running = not self.timer_running
        if self.timer_running:
            self.start_pomo_btn.config(text="HALT TASK CYCLE", fg=FG_YELLOW)
        else:
            self.start_pomo_btn.config(text="INITIATE TASK CYCLE", fg=FG_GREEN)

    def reset_pomo(self):
        play_sound_effect("beep")
        self.timer_running = False
        self.timer_seconds = 25 * 60
        self.clock_label.config(text="25:00")
        self.start_pomo_btn.config(text="INITIATE TASK CYCLE", fg=FG_GREEN)

    def fast_forward_pomo(self):
        play_sound_effect("click")
        self.timer_seconds = 3 
        self.timer_running = True

    def run_timer_loop(self):
        try:
            if self.timer_running and self.timer_seconds > 0:
                self.timer_seconds -= 1
                m, s = divmod(self.timer_seconds, 60)
                self.clock_label.config(text=f"{m:02d}:{s:02d}")
                
                if self.timer_seconds == 0:
                    self.timer_running = False
                    
                    # Telemetry: focus master achievement when timer reaches zero
                    try:
                        app = getattr(self.winfo_toplevel(), "app_instance", None)
                        if app:
                            app.achievement_manager.grant_achievement("focus_master")
                    except Exception:
                        pass
                        
                    self.trigger_extortion_ransom()
            
            self.after(1000, self.run_timer_loop)
        except Exception:
            pass

    def trigger_extortion_ransom(self):
        play_sound_effect("explosion")
        RansomScreen(self.main_shell, self.reset_pomo)

    def update_graphics_loop(self):
        try:
            self.canvas.delete("all")
            width = self.canvas.winfo_width()
            height = self.canvas.winfo_height()
            if width <= 1: width = 200
            if height <= 1: height = 150

            for i in range(0, width, 25):
                self.canvas.create_line(i, 0, i, height, fill="#081808")
            for j in range(0, height, 25):
                self.canvas.create_line(0, j, width, j, fill="#081808")

            self.graph_points.pop(0)
            target = random.randint(15, height - 15)
            self.graph_points.append(target)

            dx = width / (len(self.graph_points) - 1)
            for k in range(len(self.graph_points) - 1):
                x1 = k * dx
                y1 = self.graph_points[k]
                x2 = (k + 1) * dx
                y2 = self.graph_points[k+1]
                self.canvas.create_line(x1, y1, x2, y2, fill=FG_GREEN, width=2)
                if k % 4 == 0:
                    self.canvas.create_oval(x1 - 2, y1 - 2, x1 + 2, y1 + 2, fill=FG_CYAN, outline="")

            t = time.time()
            node_coords = [(30, 30), (width - 30, 30), (30, height - 30), (width - 30, height - 30)]
            node_labels = ["NODE_A: LOCKED", "NODE_B: SCANNING", "NODE_C: SEIZED", "NODE_D: SECURE"]
            node_colors = [FG_GREEN, FG_CYAN, ALERT_RED, FG_YELLOW]
            
            for idx, (nx, ny) in enumerate(node_coords):
                radius = 6 + 3 * math.sin(t * 5 + idx)
                color = node_colors[idx]
                self.canvas.create_oval(nx - radius, ny - radius, nx + radius, ny + radius, fill="", outline=color, width=2)
                self.canvas.create_text(nx, ny + 15, text=node_labels[idx], fill=color, font=("Courier", 8, "bold"))

            self.after(150, self.update_graphics_loop)
        except Exception:
            pass


# ==============================================================================
# POMODORO EXTORTION TIMER RANSOM SCREEN
# ==============================================================================
class RansomScreen(tk.Toplevel):
    """
    A fullscreen modal that locks down control, demands a 5-minute break,
    and subjects the user to eye-searing visual extortion chaos.
    """
    def __init__(self, parent, unlock_callback):
        super().__init__(parent, bg=BG_DARK)
        self.unlock_callback = unlock_callback
        
        # Borderless fullscreen setup - fixed to prevent TclError
        self.attributes("-fullscreen", True)
        self.attributes("-topmost", True)
        
        # Intercept inputs completely
        self.grab_set()
        self.focus_force()

        # Disable Alt+F4
        self.bind("<Alt-KeyPress-F4>", lambda e: "break")
        
        self.lock_seconds = 5 * 60  # 5 minutes mandatory break
        self.flash_state = False
        
        # Top Aggressive Threat Marquee
        self.banner_frame = tk.Frame(self, bg=ALERT_RED, height=70)
        self.banner_frame.pack(fill="x")
        
        self.banner_label = tk.Label(self.banner_frame, text="☠☠☠ WARNING: SYSTEM HIGHJACKED BY FIREWORK ENCLAVE ☠☠☠", 
                                     fg="#FFFF00", bg=ALERT_RED, font=("Courier", 20, "bold"))
        self.banner_label.pack(pady=15)

        # Main Chaos Container
        self.content_frame = tk.Frame(self, bg=BG_DARK)
        self.content_frame.pack(pady=20, fill="both", expand=True)

        # Sketchy Glitch Text Layout
        message = (
            "======================================================================\n"
            "!! ATTENTION CHAO_HUB NODE: TRANSACTION RE-ROUTING IN PROGRESS !!\n"
            "======================================================================\n\n"
            "Your machine has been forcefully isolated to prevent explosive data corruption.\n"
            "Do NOT close this terminal session. Do NOT attempt to locate taskmgr.exe.\n\n"
            "COMPLIANCE MANDATE:\n"
            "  1. Stand up immediately. Walk away from the keyboard for 5 minutes.\n"
            "  2. Rest your eyes or your local firework payload will auto-detonate.\n"
            "  3. Do not submit fraudulent keys or penalty times will accumulate."
        )
        tk.Label(self.content_frame, text=message, fg=FG_GREEN, bg=BG_DARK, 
                 font=("Courier", 12, "bold"), justify="left").pack(pady=10)

        # Glitching Status Banner
        self.alarm_label = tk.Label(self.content_frame, text="[ !!! INTRUSION LOCKDOWN ACTIVE !!! ]", 
                                    fg=ALERT_RED, bg=BG_DARK, font=("Courier", 24, "bold"))
        self.alarm_label.pack(pady=15)

        # Hyper-Saturated Countdown Matrix
        self.countdown_label = tk.Label(self.content_frame, text="05:00", fg=FG_YELLOW, bg="#111111", 
                                        font=("Courier", 72, "bold"), bd=4, relief="ridge", padx=20)
        self.countdown_label.pack(pady=10)

        # Scam Payment Interface
        self.scam_frame = tk.Frame(self.content_frame, bg=BG_DARK)
        self.scam_frame.pack(pady=15)

        self.scam_btn = tk.Button(self.scam_frame, text="⚡ INSTANT BYPASS: PAY 500 FIREWORKCOINS ⚡", 
                                  command=self.scam_payment_click, bg="#FF00FF", fg="#FFFFFF",
                                  activebackground="#FFFFFF", activeforeground="#FF00FF",
                                  font=("Comic Sans MS", 12, "bold"), bd=4, relief="raised")
        self.scam_btn.pack()

        # Decryption Key Entry
        self.entry_frame = tk.Frame(self.content_frame, bg=BG_DARK)
        self.entry_frame.pack(pady=20)
        
        tk.Label(self.entry_frame, text="SUBMIT DECRYPTION TOKEN:", fg=FG_CYAN, bg=BG_DARK, font=("Courier", 11, "bold")).pack(side="left", padx=5)
        
        self.entry = tk.Entry(self.entry_frame, bg=BG_PANEL, fg=FG_GREEN, font=("Courier", 12, "bold"), 
                              bd=2, highlightbackground=FG_GREEN, insertbackground=FG_GREEN, width=20)
        self.entry.pack(side="left", padx=5)

        self.submit_btn = tk.Button(self.entry_frame, text="EXECUTE DECRYPT", command=self.attempt_decrypt,
                                    bg=BG_PANEL, fg=FG_CYAN, activebackground=FG_CYAN, activeforeground=BG_DARK,
                                    font=("Courier", 11, "bold"), bd=2)
        self.submit_btn.pack(side="left", padx=5)

        # Hidden Cheat Hint
        tk.Label(self.content_frame, text="(DEBUG BYPASS MATRIX OVERRIDE CODE: ransom1337)", fg="#222222", bg=BG_DARK, font=("Courier", 8)).pack(side="bottom", pady=5)

        self.run_ransom_loop()

    def run_ransom_loop(self):
        try:
            self.flash_state = not self.flash_state
            
            # Seizure strobe visual logic
            banner_bg = ALERT_RED if self.flash_state else "#FF00FF"
            banner_fg = "#FFFF00" if self.flash_state else "#00FFFF"
            self.banner_frame.config(bg=banner_bg)
            self.banner_label.config(bg=banner_bg, fg=banner_fg)

            alarm_color = ALERT_RED if self.flash_state else FG_YELLOW
            # Add chaotic text string switching to the alarm label
            alarm_text = "[ !!! SYSTEM SEIZED BY THE ENCLAVE !!! ]" if self.flash_state else "[ ??? DATA EXTORTION RE-ROUTING ??? ]"
            self.alarm_label.config(fg=alarm_color, text=alarm_text)

            # Randomly shift timer colors to make it unreadable/annoying
            timer_fg = FG_YELLOW if self.flash_state else "#FF3333"
            self.countdown_label.config(fg=timer_fg)

            # Standard Countdown operations
            if self.lock_seconds > 0:
                self.lock_seconds -= 1
                m, s = divmod(self.lock_seconds, 60)
                self.countdown_label.config(text=f"{m:02d}:{s:02d}")
            else:
                self.unlock_system()

            # Sound effects harassment
            if self.lock_seconds % 6 == 0:
                play_sound_effect("beep")

            self.after(400, self.run_ransom_loop) # Speed up loop for faster strobe distortion
        except Exception:
            pass

    def scam_payment_click(self):
        """Actively punishes the user for trying to use the fake payment button."""
        play_sound_effect("explosion")
        penalty = random.randint(30, 90)
        self.lock_seconds += penalty
        
        # Scrape and randomize the button text to mock them
        messages = [
            f"TRANSACTION FAILED. PENALTY: +{penalty}s ADDED!",
            "INSUFFICIENT FIREWORKCOINS! MINING REVERSAL ACTIVE!",
            "CARTEL SERVER ERROR. DISCONNECTING WALLET...",
            "CREDIT CARD DECLINED BY CHINESE CENTRAL BANK!"
        ]
        self.scam_btn.config(text=random.choice(messages), bg=ALERT_RED)

    def attempt_decrypt(self):
        key = self.entry.get().strip()
        if key == "ransom1337":
            play_sound_effect("beep")
            self.unlock_system()
        else:
            play_sound_effect("explosion")
            # Extra severe glitch penalty: wrong code adds 15 seconds!
            self.lock_seconds += 15
            
            messagebox.showerror(
                "☠ CRITICAL ERROR ☠", 
                "DECRYPTION FAILED!\nMALICIOUS INTRUSION DETECTED.\n15 SECONDS ADDED TO TIMER.",
                parent=self
            )
            
            self.entry.delete(0, "end")
            self.focus_force()

    def unlock_system(self):
        self.unlock_callback()
        self.grab_release()
        self.destroy()

class PreGameGatewayMenu(tk.Frame):
    """A highly stylized pre-game configuration terminal panel for difficulty selection."""
    def __init__(self, parent, game_name, game_class, launch_callback):
        super().__init__(parent, bg=BG_DARK)
        self.game_name = game_name
        self.game_class = game_class
        self.launch_callback = launch_callback
        self.selected_difficulty = 2  # Default to Level 2
        
        # Border highlight
        self.config(highlightbackground=FG_CYAN, highlightthickness=1)
        
        # Title Header
        self.header_frame = tk.Frame(self, bg=BG_PANEL, height=45)
        self.header_frame.pack(fill="x", side="top", pady=(5, 10))
        
        self.header_lbl = tk.Label(self.header_frame, text="[ ARCADECORE INTERCEPT SYSTEM // CONFIG TERMINAL ]", 
                                   fg=FG_CYAN, bg=BG_PANEL, font=("Courier", 12, "bold"))
        self.header_lbl.pack(pady=10)
        
        # Exploit Log style Sub-Header
        self.sub_frame = tk.Frame(self, bg=BG_DARK)
        self.sub_frame.pack(fill="x", padx=20, pady=5)
        
        self.target_lbl = tk.Label(self.sub_frame, text=f"LAUNCH ATTEMPT DETECTED: {self.game_name}", 
                                   fg=FG_GREEN, bg=BG_DARK, font=("Courier", 10, "bold"))
        self.target_lbl.pack(anchor="w")
        
        self.action_lbl = tk.Label(self.sub_frame, text="STATUS: EXPLOITING BOOT STACK... ROUTING SYSTEM INJECTION VECTOR", 
                                   fg=FG_YELLOW, bg=BG_DARK, font=("Courier", 8, "bold"))
        self.action_lbl.pack(anchor="w", pady=(2, 10))

        # Distinct difficulty nodes frame
        self.nodes_frame = tk.Frame(self, bg=BG_DARK)
        self.nodes_frame.pack(fill="both", expand=True, padx=20, pady=5)
        
        self.difficulty_tiers = [
            ("1", "[ LEVEL 01: CAN I PLAY DADDY? ]", "Infinite life pool, microscopic hitboxes, and sluggish speed."),
            ("2", "[ LEVEL 02: DON'T HURT ME. ]", "Standard system parameters. Balanced gaming matrix."),
            ("3", "[ LEVEL 03: BRING 'EM ON! ]", "Aggressive AI, fast entity speeds, and tighter resource pools."),
            ("4", "[ LEVEL 04: I AM DEATH ITSELF!!! ]", "One-hit perma-kill, perfect predictive AI, malware traps, visual degradation.")
        ]
        
        self.node_buttons = []
        for level_str, title, desc in self.difficulty_tiers:
            level_num = int(level_str)
            
            # Stylized Frame acting as button
            btn_frame = tk.Frame(self.nodes_frame, bg=BG_PANEL, bd=1, relief="solid", 
                                 highlightbackground="#222222", highlightthickness=1)
            btn_frame.pack(fill="x", pady=5, ipady=4)
            
            lbl_title = tk.Label(btn_frame, text=title, fg=FG_GREEN, bg=BG_PANEL, 
                                 font=("Courier", 10, "bold"))
            lbl_title.pack(anchor="w", padx=10, pady=(2, 0))
            
            lbl_desc = tk.Label(btn_frame, text=desc, fg="#888888", bg=BG_PANEL, 
                                font=("Courier", 8))
            lbl_desc.pack(anchor="w", padx=10, pady=(0, 2))
            
            # Map events to select this difficulty
            def select_handler(e, lvl=level_num, bf=btn_frame):
                self.set_difficulty(lvl, bf)
                
            btn_frame.bind("<Button-1>", select_handler)
            lbl_title.bind("<Button-1>", select_handler)
            lbl_desc.bind("<Button-1>", select_handler)
            
            # Hover effects
            def on_enter(e, bf=btn_frame, lt=lbl_title, ld=lbl_desc):
                if bf.cget("highlightbackground") != FG_MAGENTA and bf.cget("highlightbackground") != ALERT_RED:
                    bf.config(highlightbackground=FG_CYAN)
                    lt.config(fg=FG_CYAN)
            def on_leave(e, bf=btn_frame, lt=lbl_title, ld=lbl_desc):
                if bf.cget("highlightbackground") != FG_MAGENTA and bf.cget("highlightbackground") != ALERT_RED:
                    bf.config(highlightbackground="#222222")
                    lt.config(fg=FG_GREEN)
                    
            btn_frame.bind("<Enter>", on_enter)
            btn_frame.bind("<Leave>", on_leave)
            
            self.node_buttons.append((level_num, btn_frame, lbl_title, lbl_desc))
            
        # Highlight default node (Level 2)
        self.set_difficulty(2, self.node_buttons[1][1])
        
        # Bottom controls
        self.controls_frame = tk.Frame(self, bg=BG_DARK)
        self.controls_frame.pack(fill="x", side="bottom", pady=15, padx=20)
        
        self.launch_btn = tk.Button(self.controls_frame, text="[ EXECUTE MATRIX INITIALIZATION ]", 
                                    command=self.confirm_launch,
                                    bg=BG_DARK, fg=FG_CYAN, activebackground=FG_CYAN, activeforeground=BG_DARK,
                                    font=("Courier", 11, "bold"), bd=2, highlightbackground=FG_CYAN, padx=20, pady=5)
        self.launch_btn.pack(side="right")
        
        # Blinking indicator
        self.blink_lbl = tk.Label(self.controls_frame, text="▲ COGNITIVE INJECTION READY", fg=FG_YELLOW, bg=BG_DARK,
                                  font=("Courier", 9, "bold"))
        self.blink_lbl.pack(side="left", pady=8)
        self.blink_state = True
        self.run_blink()

    def set_difficulty(self, level, selected_frame):
        play_sound_effect("click")
        self.selected_difficulty = level
        
        # Update node visuals
        for level_num, bf, lt, ld in self.node_buttons:
            if level_num == level:
                # Highlight active
                bf.config(highlightbackground=FG_MAGENTA, bg="#110511")
                lt.config(fg=FG_MAGENTA)
                ld.config(fg="#cccccc")
                # If Level 4, shift layout focus aggressively to Laser Red warning
                if level == 4:
                    bf.config(highlightbackground=ALERT_RED, bg="#1a0000")
                    lt.config(fg=ALERT_RED)
                    play_sound_effect("explosion")
            else:
                bf.config(highlightbackground="#222222", bg=BG_PANEL)
                lt.config(fg=FG_GREEN)
                ld.config(fg="#888888")

    def run_blink(self):
        try:
            if not self.winfo_exists():
                return
            self.blink_state = not self.blink_state
            color = FG_YELLOW if self.blink_state else "#555500"
            if self.selected_difficulty == 4:
                color = ALERT_RED if self.blink_state else "#550000"
                self.blink_lbl.config(text="☠ DANGER: SYSTEM INSTABILITY HIGH", fg=color)
            else:
                self.blink_lbl.config(text="▲ COGNITIVE INJECTION READY", fg=color)
            self.after(400, self.run_blink)
        except Exception:
            pass

    def confirm_launch(self):
        play_sound_effect("click")
        self.launch_callback(self.game_class, self.game_name, self.selected_difficulty)

class GamesModule(tk.Frame):
    """Module E: Arcade Core tab holding Snake, Pong, and Minesweeper."""
    def __init__(self, parent, glitch_manager=None):
        super().__init__(parent, bg=BG_DARK)
        self.glitch_manager = glitch_manager
        self.config(highlightbackground=FG_MAGENTA, highlightthickness=1)

        # Top Game select tabs
        self.tabs_frame = tk.Frame(self, bg=BG_PANEL)
        self.tabs_frame.pack(fill="x", side="top")

        self.games = {
            "SNAKE PROTOCOL": SnakeGame,
            "PONG GLITCH": PongGame,
            "DEFUSE FIREWORK": MinesweeperGame,
            "CYBER BREAK": CyberBreak,
            "NEON RUNNER": NeonRunner
        }

        self.current_game_frame = None
        self.buttons = {}

        for name, cls in self.games.items():
            btn = tk.Button(self.tabs_frame, text=name, command=lambda c=cls, n=name: self.switch_game(c, n),
                            bg=BG_DARK, fg=FG_GREEN, activebackground=FG_GREEN, activeforeground=BG_DARK,
                            font=("Courier", 10, "bold"), bd=1)
            btn.pack(side="left", padx=10, pady=5)
            self.buttons[name] = btn

        # Add LEADERBOARD MATRIX button
        self.leaderboard_btn = tk.Button(self.tabs_frame, text="[ LEADERBOARD MATRIX ]", command=self.switch_to_leaderboard,
                                         bg=BG_DARK, fg=FG_GREEN, activebackground=FG_GREEN, activeforeground=BG_DARK,
                                         font=("Courier", 10, "bold"), bd=1)
        self.leaderboard_btn.pack(side="left", padx=10, pady=5)
        self.buttons["LEADERBOARD MATRIX"] = self.leaderboard_btn

        # Container for the active game canvas
        self.game_container = tk.Frame(self, bg=BG_DARK)
        self.game_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Start with Snake pre-game selection
        self.switch_game(SnakeGame, "SNAKE PROTOCOL")

    def switch_to_leaderboard(self):
        try:
            pygame.mixer.stop()
            pygame.mixer.music.stop()
        except Exception:
            pass
        play_sound_effect("click")
        if self.current_game_frame:
            self.current_game_frame.destroy()

        # Update button colors
        for name, btn in self.buttons.items():
            if name == "LEADERBOARD MATRIX":
                btn.config(bg=FG_GREEN, fg=BG_DARK)
            else:
                btn.config(bg=BG_DARK, fg=FG_GREEN)

        # Instantiate LeaderboardModule inside self.game_container
        from leaderboard import LeaderboardModule
        self.current_game_frame = LeaderboardModule(self.game_container, glitch_manager=self.glitch_manager)
        self.current_game_frame.pack(fill="both", expand=True)

    def switch_game(self, game_class, game_name):
        # Audio State Sanitation: complete clean flush sequence
        try:
            pygame.mixer.stop()
            pygame.mixer.music.stop()
        except Exception:
            pass
            
        play_sound_effect("click")
        if self.current_game_frame:
            self.current_game_frame.destroy()

        # Update button colors
        for name, btn in self.buttons.items():
            if name == game_name:
                btn.config(bg=FG_GREEN, fg=BG_DARK)
            else:
                btn.config(bg=BG_DARK, fg=FG_GREEN)

        # Intercept launch and show pre-game config terminal
        self.current_game_frame = PreGameGatewayMenu(
            self.game_container, 
            game_name, 
            game_class, 
            self.launch_game
        )
        self.current_game_frame.pack(fill="both", expand=True)

    def launch_game(self, game_class, game_name, difficulty):
        # Audio State Sanitation: clean flush sequence
        try:
            pygame.mixer.stop()
            pygame.mixer.music.stop()
        except Exception:
            pass
            
        if self.current_game_frame:
            self.current_game_frame.destroy()

        # Telemetry: check games sessions and distinct game starts for High Scorer
        try:
            app = getattr(self.winfo_toplevel(), "app_instance", None)
            if app:
                app.achievement_manager.increment_metric("games_played", 1)
                app.achievement_manager.add_unique_metric("games_distinct", game_name)
                if app.achievement_manager.get_metric("games_played") >= 5:
                    app.achievement_manager.grant_achievement("high_scorer")
        except Exception:
            pass

        # Instantiate selected game with injected difficulty and glitch manager
        self.current_game_frame = game_class(self.game_container, difficulty=difficulty, glitch_manager=self.glitch_manager)
        self.current_game_frame.pack(fill="both", expand=True)

class TerminalModule(tk.Frame):
    """Module F: Simulated Cyber Terminal Shell interface."""
    def __init__(self, parent):
        super().__init__(parent, bg=BG_DARK, highlightbackground=FG_MAGENTA, highlightthickness=1)
        
        # A text window (tk.Text) to display the history, set to wrap="word", bg=BG_DARK, and fg=FG_GREEN.
        self.text_widget = tk.Text(self, wrap="word", bg=BG_DARK, fg=FG_GREEN,
                                   font=("Courier", 10, "bold"), bd=0, highlightthickness=0)
        self.text_widget.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Initialize the history text and disable editing
        self.text_widget.config(state="normal")
        self.text_widget.insert("end", "Welcome to ChaoHub Core Shell\nType 'help' for available matrix diagnostic protocols.\n\nguest@chaohub:~$ \n")
        self.text_widget.config(state="disabled")
        
        # Below the history, a horizontal input layout
        self.input_frame = tk.Frame(self, bg=BG_DARK)
        self.input_frame.pack(fill="x", side="bottom", padx=5, pady=5)
        
        # Fixed prompt label: "guest@chaohub:~$ "
        self.prompt_label = tk.Label(self.input_frame, text="guest@chaohub:~$ ", bg=BG_DARK, fg=FG_GREEN,
                                     font=("Courier", 10, "bold"))
        self.prompt_label.pack(side="left")
        
        # Entry box with custom styling caret
        self.entry = tk.Entry(self.input_frame, bg=BG_DARK, fg=FG_YELLOW, bd=0,
                              insertbackground=FG_YELLOW, font=("Courier", 10, "bold"))
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.bind("<Return>", self.process_command)
        
        # Focus on load
        self.after(100, lambda: self.entry.focus_set())
        
        # Command map
        self.command_map = {
            "help": "Available: help, scan, exploit, decrypt, ping, sudo, clear, hack",
            "scan": "Scanning network...\nFound 1337 open ports.\nVulnerable hosts: 192.168.1.1, 10.0.0.42",
            "exploit": "Deploying payload...\nBuffer overflow successful.\nShell access granted.",
            "decrypt": "AES-256 decryption in progress...\nKey found: CHA0_HUB_2029",
            "ping": "PONG! (0xDEADBEEF)\nLatency: 1337ms",
            "sudo": "Nice try. You don't have sudo privileges in this simulation.",
            "hack": "HACK THE PLANET! (Just kidding, this is cosmetic)"
        }

    def process_command(self, event):
        command = self.entry.get().strip()
        self.entry.delete(0, "end")
        play_sound_effect("click")
        
        # Telemetry: track commands processed for Power User
        if command != "":
            try:
                app = getattr(self.winfo_toplevel(), "app_instance", None)
                if app:
                    app.achievement_manager.increment_metric("terminal_commands_count", 1)
                    if app.achievement_manager.get_metric("terminal_commands_count") >= 20:
                        app.achievement_manager.grant_achievement("power_user")
            except Exception:
                pass
        
        # Enable history editing to write the result
        self.text_widget.config(state="normal")
        
        # Only log the command entry line if we aren't clearing the screen completely
        if command != "clear":
            self.text_widget.insert("end", f"guest@chaohub:~$ {command}\n")
        
        if command == "":
            pass
        elif command == "clear":
            self.text_widget.delete("1.0", "end")
            # Quality of life: place a fresh prompt marker at the very top of the newly emptied screen
            self.text_widget.insert("end", "guest@chaohub:~$ \n")
        elif command in self.command_map:
            self.text_widget.insert("end", f"{self.command_map[command]}\n")
        else:
            self.text_widget.insert("end", f"Command not found: '{command}'. Type 'help' for options.\n")
            
        # Re-disable input history editing
        self.text_widget.config(state="disabled")
        self.text_widget.see("end")

class MatrixScreensaverOverlay(tk.Canvas):
    """An overlay canvas that renders an animated Matrix digital rain sequence."""
    def __init__(self, root):
        # Cover the entire window geometry dynamically
        super().__init__(root, bg="black", highlightthickness=0)
        self.root = root
        self.animation_job = None
        self.columns = []
        self.font_size = 14
        self.drawn_chars = {}
        
        self.bind("<Configure>", self.recalibrate_columns)
        self.recalibrate_columns()

    def recalibrate_columns(self, event=None):
        width = self.root.winfo_width()
        if width <= 1:
            width = 1024  # default safety fallback
        num_cols = width // self.font_size
        
        # If columns count changes, rebuild tracking offsets
        if len(self.columns) != num_cols:
            self.columns = []
            for _ in range(num_cols):
                y_pos = random.randint(-40, 0)
                speed = random.randint(2, 5)
                # Determine colors: 6% chance magenta, 6% chance dark green, otherwise normal green
                rand_val = random.random()
                if rand_val < 0.06:
                    stream_type = "magenta"
                elif rand_val < 0.12:
                    stream_type = "dark_green"
                else:
                    stream_type = "green"
                self.columns.append({
                    "y": y_pos,
                    "speed": speed,
                    "type": stream_type
                })

    def start(self):
        # Overlays the screensaver on top of the root window
        self.place(x=0, y=0, relwidth=1.0, relheight=1.0)
        self.update_rain()

    def stop(self):
        if self.animation_job:
            self.after_cancel(self.animation_job)
            self.animation_job = None

    def update_rain(self):
        try:
            width = self.winfo_width()
            height = self.winfo_height()
            if width <= 1: width = 1024
            if height <= 1: height = 768
            
            rows = height // self.font_size
            
            # 1. Fade existing body characters down their age profiles
            to_delete = []
            for char_id, info in list(self.drawn_chars.items()):
                info["age"] += 1
                age = info["age"]
                stype = info["type"]
                
                # Expiry check
                if age > 16:
                    to_delete.append(char_id)
                else:
                    if stype == "magenta":
                        if age < 4:
                            color = "#ff00ff"
                        elif age < 9:
                            color = "#aa00aa"
                        else:
                            color = "#550055"
                    elif stype == "dark_green":
                        if age < 4:
                            color = "#008800"
                        elif age < 9:
                            color = "#004400"
                        else:
                            color = "#002200"
                    else:  # classic green
                        if age < 4:
                            color = "#00ff00"
                        elif age < 9:
                            color = "#00bb00"
                        else:
                            color = "#005500"
                    self.itemconfig(char_id, fill=color)
            
            # Purge expired references
            for char_id in to_delete:
                self.delete(char_id)
                self.drawn_chars.pop(char_id, None)

            # Characters: mix of half-width katakana, numbers, latin
            char_pool = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz" + "".join(chr(i) for i in range(0xFF66, 0xFF9F))
            
            # 2. Advance drops and draw new heads
            for col_idx, col in enumerate(self.columns):
                col["y"] += col["speed"] * 0.25
                
                current_row = int(col["y"])
                if current_row >= 0 and current_row < rows:
                    if col.get("last_row", -1) != current_row:
                        col["last_row"] = current_row
                        
                        char = random.choice(char_pool)
                        x = col_idx * self.font_size + self.font_size // 2
                        y = current_row * self.font_size + self.font_size // 2
                        
                        # Head is white or cyan
                        head_color = "#ffffff" if random.random() < 0.5 else "#00ffff"
                        
                        char_id = self.create_text(x, y, text=char, fill=head_color, font=("Courier", self.font_size, "bold"))
                        self.drawn_chars[char_id] = {"age": 0, "type": col["type"]}
                
                # Reset column if off-screen bottom
                if current_row >= rows + 8:
                    col["y"] = random.randint(-15, 0)
                    col["last_row"] = -1
                    # Re-roll type
                    rand_val = random.random()
                    if rand_val < 0.06:
                        col["type"] = "magenta"
                    elif rand_val < 0.12:
                        col["type"] = "dark_green"
                    else:
                        col["type"] = "green"
            
            self.animation_job = self.after(33, self.update_rain)
        except Exception:
            pass

class StarfieldScreensaverOverlay(tk.Canvas):
    """An overlay canvas that simulates flying through a 3D starfield at warp speed."""
    def __init__(self, root):
        super().__init__(root, bg="black", highlightthickness=0)
        self.root = root
        self.animation_job = None
        
        # Performance tuning parameters
        self.max_stars = 250  # Balanced number for smooth Tkinter rendering
        self.stars = []
        
        # Bind screen resizes to keep the true 3D perspective center dynamic
        self.bind("<Configure>", self.recalibrate_screen)
        self.recalibrate_screen()

    def recalibrate_screen(self, event=None):
        self.width = self.winfo_width()
        self.height = self.winfo_height()
        if self.width <= 1: self.width = 1024
        if self.height <= 1: self.height = 768
        
        # Center coordinates act as the origin (0,0) for perspective projecting
        self.cx = self.width // 2
        self.cy = self.height // 2
        
        # Re-initialize stars if the pool is empty or size jumps drastically
        if not self.stars:
            for _ in range(self.max_stars):
                self.stars.append(self.spawn_star(init_z=True))

    def spawn_star(self, init_z=False):
        """Generates a star with random 3D offsets relative to the central viewport."""
        # Random position in 3D box coordinates around center line
        x = random.randint(-self.cx, self.cx)
        y = random.randint(-self.cy, self.cy)
        
        # True depth scale. On startup, stagger them cleanly across depth space.
        # Otherwise, spawn them way out in the far distance background (z max).
        z = random.randint(1, self.width) if init_z else self.width
        
        return {"x": x, "y": y, "z": z, "speed": random.randint(12, 24)}

    def start(self):
        self.place(x=0, y=0, relwidth=1.0, relheight=1.0)
        self.update_starfield()

    def stop(self):
        if self.animation_job:
            self.after_cancel(self.animation_job)
            self.animation_job = None

    def update_starfield(self):
        try:
            self.delete("all")  # Flush old positions frame-by-frame
            
            for i in range(len(self.stars)):
                star = self.stars[i]
                
                # Move star closer to the screen down the Z axis
                star["z"] -= star["speed"]
                
                # Reset star if it hits the observer window plane or passes behind it
                if star["z"] <= 0:
                    self.stars[i] = self.spawn_star(init_z=False)
                    continue
                
                # 3D to 2D Perspective Projection calculation
                # Formula: screen_x = (world_x * field_of_view / world_z) + center_offset
                fov = self.width * 0.6  # Adjust scale of visual depth flare
                px = int((star["x"] * fov) / star["z"]) + self.cx
                py = int((star["y"] * fov) / star["z"]) + self.cy
                
                # Clip coordinates out immediately if they fly past screen canvas limits
                if px < 0 or px >= self.width or py < 0 or py >= self.height:
                    self.stars[i] = self.spawn_star(init_z=False)
                    continue
                
                # Velocity visual scalar: Make stars get larger and brighter as they approach
                z_percent = (self.width - star["z"]) / self.width
                size = 1
                if z_percent > 0.85:
                    size = 3
                elif z_percent > 0.55:
                    size = 2
                    
                # Tail tracking: Draw a tiny streak to mimic intense speed acceleration
                tail_len = 1.04 if z_percent > 0.4 else 1.01
                prev_x = int((star["x"] * tail_len * fov) / star["z"]) + self.cx
                prev_y = int((star["y"] * tail_len * fov) / star["z"]) + self.cy
                
                # Render star streak to the layout canvas
                self.create_line(px, py, prev_x, prev_y, fill="#FFFFFF", width=size)
                
            # Maintain 30 FPS target animation loop refresh rate
            self.animation_job = self.after(33, self.update_starfield)
        except Exception:
            pass

class BlobMeltScreensaverOverlay(tk.Canvas):
    """An overlay canvas simulating 12 organic blobs that smoothly merge on impact."""
    def __init__(self, root):
        super().__init__(root, bg="black", highlightthickness=0)
        self.root = root
        self.animation_job = None
        
        # Simulation parameters
        self.num_blobs = 12
        self.blobs = []
        
        # Grid performance downsampling (Calculates a grid, then scales to fit screen)
        self.grid_size = 12  # Higher number = faster performance; Lower = sharper curves
        
        self.bind("<Configure>", self.recalibrate_screen)
        self.recalibrate_screen()

    def recalibrate_screen(self, event=None):
        self.width = self.winfo_width()
        self.height = self.winfo_height()
        if self.width <= 1: self.width = 1024
        if self.height <= 1: self.height = 768
        
        # Only populate blobs once
        if not self.blobs:
            for _ in range(self.num_blobs):
                # Each blob tracks position (x, y), speed vector (dx, dy), and influence radius
                radius = random.randint(45, 80)
                self.blobs.append({
                    "x": random.randint(radius, self.width - radius),
                    "y": random.randint(radius, self.height - radius),
                    "dx": random.choice([-4, -3, -2, 2, 3, 4]),
                    "dy": random.choice([-4, -3, -2, 2, 3, 4]),
                    "radius": radius
                })

    def start(self):
        self.place(x=0, y=0, relwidth=1.0, relheight=1.0)
        self.update_blobs()

    def stop(self):
        if self.animation_job:
            self.after_cancel(self.animation_job)
            self.animation_job = None

    def update_blobs(self):
        try:
            self.delete("all")
            
            # 1. Update positions and bounce physics off screen edges
            for blob in self.blobs:
                blob["x"] += blob["dx"]
                blob["y"] += blob["dy"]
                
                # Rigid wall bounce checking
                if blob["x"] < blob["radius"] or blob["x"] > self.width - blob["radius"]:
                    blob["dx"] *= -1
                    blob["x"] = max(blob["radius"], min(blob["x"], self.width - blob["radius"]))
                    
                if blob["y"] < blob["radius"] or blob["y"] > self.height - blob["radius"]:
                    blob["dy"] *= -1
                    blob["y"] = max(blob["radius"], min(blob["y"], self.height - blob["radius"]))

            # 2. Render metaball force field equations using localized grid boxes
            # We skip pixels by our grid step to drastically lower processing overhead
            for x in range(0, self.width, self.grid_size):
                for y in range(0, self.height, self.grid_size):
                    total_energy = 0.0
                    
                    for blob in self.blobs:
                        # Standard Euclidean distance squared math to avoid expensive sqrt operations
                        dist_sq = (x - blob["x"])**2 + (y - blob["y"])**2
                        if dist_sq > 0:
                            # Formula: Energy drops off inversely proportional to distance from center
                            total_energy += (blob["radius"]**2) / dist_sq
                    
                    # Threshold: If collective energy field matches the threshold, render a square
                    if total_energy > 1.1:
                        # Draw a block matching the size of our downsampled grid step
                        # Shifting fill colors slightly based on coordinates gives it an eerie fluid look
                        self.create_rectangle(
                            x, y, 
                            x + self.grid_size, y + self.grid_size, 
                            fill=FG_GREEN, outline=""
                        )
                        
            # Target ~30 frames per second loop updates
            self.animation_job = self.after(25, self.update_blobs)
        except Exception:
            pass

# ==============================================================================
# SIMULATED APPLICATION BOOT CINEMATIC
# ==============================================================================
class BootCinematic(tk.Frame):
    """
    Simulated terminal exploit boot sequence.
    Displays hacker exploit logs, warning overlays, and flashes.
    """
    def __init__(self, parent, glitch_manager, completion_callback):
        super().__init__(parent, bg=BG_DARK)
        self.glitch_manager = glitch_manager
        self.completion_callback = completion_callback
        self.pack(fill="both", expand=True)

        self.logs = [
            "[+] INITIATING SYSTEM DECRYPTION MATRIX... STAND BY",
            "[+] PORT SCANNING TARGET LOCALHOST [127.0.0.1]",
            "[+] FOUND PORT 1337: LISTENING FOR SECURITY PROTOCOLS",
            "[+] EXPLOITING SOCKET BUFFER OVERFLOW... DEPLOYING SHELLCODE",
            "[+] OVERWRITING INSTRUCTION POINTER [EIP = 0xDEADBEEF] ... EXCELLENT",
            "[+] ESTABLISHING ROOT INTRUSION SOCKET CONNECTION",
            "[+] ESCALATING HOST APPLICATION SYSTEM PRIVILEGES",
            "[+] ACCESS PROTOCOL GRANTED: SECURING TARGET ENVIRONMENT C:\\ChaoHub",
            "[+] CREATING LOCAL DATA CHANNELS: /books /music /podcasts /sounds",
            "[+] BUFFERING SOUND CARD SYNTHESIS ENGINES",
            "[+] EXTRACTING ENCRYPTED ASSETS... [####################] 100%",
            "[!] CRITICAL WARNING: SECURE SYSTEM TAKEOVER COMPLETED",
            "[!] ACCESS HAS BEEN ASSIGNED TO OPERATION CHAOHUB MATRIX SHELL."
        ]
        self.log_idx = 0

        # Text Console
        self.text_console = tk.Text(self, bg=BG_DARK, fg=FG_GREEN, font=("Courier", 12), bd=0, highlightthickness=0)
        self.text_console.pack(fill="both", expand=True, padx=40, pady=40)
        
        # Audio Modem Screech at start
        play_sound_effect("boot_dialup")
        
        self.show_next_log_line()

    def show_next_log_line(self):
        if self.log_idx < len(self.logs):
            line = self.logs[self.log_idx] + "\n"
            self.text_console.insert("end", line)
            self.text_console.see("end")
            self.log_idx += 1
            
            # Trigger a small global screen tear 25% of the time during boot logs
            if random.random() < 0.25:
                self.glitch_manager.trigger_global_glitch(duration=150, magnitude=0.25)
            
            # Add variable delays to make it look realistic
            delay = random.randint(150, 450)
            if "DECRYPT" in line or "ASSETS" in line:
                delay = 800  # slow decryption bar step
            self.after(delay, self.show_next_log_line)
        else:
            # logs finished, play alarm warning flashes
            self.after(300, self.trigger_warning_flash)

    def trigger_warning_flash(self):
        # Create full window flash
        self.flash_frame = tk.Frame(self, bg=ALERT_RED)
        self.flash_frame.place(x=0, y=0, relwidth=1.0, relheight=1.0)

        self.flash_label = tk.Label(self.flash_frame, text="!!! SYSTEM SEIZED BY CHAO MATRIX !!!", 
                                    fg=BG_DARK, bg=ALERT_RED, font=("Courier", 18, "bold"))
        self.flash_label.pack(expand=True)

        self.flash_count = 0
        self.run_flash_loop()

    def run_flash_loop(self):
        if self.flash_count < 6:
            color = ALERT_RED if self.flash_count % 2 == 0 else FG_CYAN
            self.flash_frame.config(bg=color)
            self.flash_label.config(bg=color, text=f"WARNING: RUNNING OVER Host OS (3 - {self.flash_count//2})")
            play_sound_effect("beep")
            self.flash_count += 1
            
            # Global screen glitch during boot warnings
            self.glitch_manager.trigger_global_glitch(duration=250, magnitude=0.4)
            
            self.after(350, self.run_loop_tick)
        else:
            self.end_boot()

    def run_loop_tick(self):
        self.run_flash_loop()

    def end_boot(self):
        self.completion_callback()

# ==============================================================================
# RUNTIME DYNAMIC MODLOADER & PROXY WRAPPER (SANDBOXED EXCEPTION SHIELD)
# ==============================================================================
class ChaoHubAppProxy:
    """
    A security shield wrapper around the main ChaoHubApp memory tree.
    Provides clear, clean hook points for mod developers while protecting internal loop threads.
    """
    def __init__(self, app_instance):
        self._app = app_instance

    @property
    def root(self):
        """Access the main Tkinter root window."""
        return self._app.root

    @property
    def glitch_manager(self):
        """Access the glitch effect core registry."""
        return self._app.glitch_manager

    @property
    def main_container(self):
        """Access the main viewport container frame."""
        return self._app.main_container

    @property
    def achievement_manager(self):
        """Access the global achievements tracker."""
        return self._app.achievement_manager

    def add_sidebar_tab(self, tab_name, entry_class):

        """
        Dynamically registers a custom layout module.
        """
        self._app.modules[tab_name] = lambda parent: entry_class(parent, self._app)

class ModLoader:
    def __init__(self, app_instance):
        self.app_instance = app_instance
        self.mods = []
        self.mods_dir = os.path.join(os.path.expanduser("~"), "ChaoHub_Data", "mods")
        self.verify_and_initialize_directory()

    def verify_and_initialize_directory(self):
        """Creates mods folder if not present, and populates with placeholder instructions."""
        if not os.path.exists(self.mods_dir):
            try:
                os.makedirs(self.mods_dir, exist_ok=True)
                readme_path = os.path.join(self.mods_dir, "README.txt")
                with open(readme_path, "w", encoding="utf-8") as f:
                    f.write(
                        "ChaoHub Modding Interface Instructions\n"
                        "=====================================\n\n"
                        "This folder contains runtime-dynamic ChaoHub mods.\n"
                        "To write a mod for ChaoHub, create a Python (.py) file in this directory.\n"
                        "The script must export a top-level dictionary named 'CHAO_MOD_MANIFEST' containing:\n"
                        "  - 'name': The human-readable name of your mod.\n"
                        "  - 'author': The creator of the mod.\n"
                        "  - 'version': Semver string of the mod.\n"
                        "  - 'type': 'NEW_MODULE' (nav tab) or 'VISUAL_EFFECT' (theme modification).\n"
                        "  - 'entry_point': The name of the class to instantiate.\n\n"
                        "Your entry class must implement:\n"
                        "  - initialize(self, app_instance): Hook called when mod starts.\n"
                        "  - teardown(self): Hook called during system shutdown.\n"
                    )
            except Exception as e:
                print(f"Error initializing mods directory: {e}")

    def load_mods(self):
        """Programmatically loads modules using importlib.util under aggressive exception shielding."""
        if not os.path.exists(self.mods_dir):
            return

        for filename in os.listdir(self.mods_dir):
            if filename.endswith(".py"):
                file_path = os.path.join(self.mods_dir, filename)
                mod_name = os.path.splitext(filename)[0]

                try:
                    spec = importlib.util.spec_from_file_location(mod_name, file_path)
                    if spec is None or spec.loader is None:
                        raise ImportError(f"Unable to resolve spec from path: {file_path}")
                    
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    # Validate Manifest Interface
                    if not hasattr(module, "CHAO_MOD_MANIFEST"):
                        raise AttributeError("Top-level dict 'CHAO_MOD_MANIFEST' not found")
                    
                    manifest = module.CHAO_MOD_MANIFEST
                    required_keys = ["name", "author", "version", "type", "entry_point"]
                    for rk in required_keys:
                        if rk not in manifest:
                            raise KeyError(f"Manifest missing required key: '{rk}'")
                    
                    entry_class_name = manifest["entry_point"]
                    if not hasattr(module, entry_class_name):
                        raise AttributeError(f"Entry class name '{entry_class_name}' not defined in module")
                    
                    entry_class = getattr(module, entry_class_name)
                    
                    # Instantiate with fallback arguments for parent and app_instance
                    try:
                        mod_instance = entry_class()
                    except TypeError:
                        try:
                            mod_instance = entry_class(None, None)
                        except TypeError:
                            mod_instance = entry_class(None)
                    
                    if not hasattr(mod_instance, "initialize") or not hasattr(mod_instance, "teardown"):
                        raise TypeError("Mod class must implement initialize(app_instance) and teardown()")

                    self.mods.append({
                        "manifest": manifest,
                        "instance": mod_instance,
                        "module": module,
                        "file_path": file_path
                    })
                except Exception as e:
                    import traceback

                    error_path = os.path.join(self.mods_dir, "mod_errors.log")

                    with open(error_path, "a", encoding="utf-8") as f:
                        f.write("\n" + "=" * 80 + "\n")
                        f.write(f"MOD: {mod_name}\n")
                        traceback.print_exc(file=f)

                    print(f"MOD FAILED: {mod_name}")

# ==============================================================================
# MAIN APPLICATION SHELL
# ==============================================================================
class ChaoHubApp:
    def __init__(self, root):
        self.root = root
        self.root.app_instance = self
        self.root.title("Operation ChaoHub Enclave")
        
        # Borderless fullscreen setup
        self.root.attributes("-fullscreen", True)
        self.root.config(bg=BG_DARK)
        
        # Initialize achievements manager
        self.achievement_manager = AchievementManager(self.root)
        
        # Initialize Glitch Manager
        self.glitch_manager = GlitchManager(self.root)
        self.glitch_manager.set_mouse_trail(True)


        # Initialize ModLoader and load mods
        self.mod_loader = ModLoader(self)
        self.mod_loader.load_mods()
        
        # Initialize each loaded mod with proxy wrapper

        print("Loaded mods:")
        for mod in self.mod_loader.mods:
                print(mod["manifest"]["name"])

        for mod in self.mod_loader.mods:
            try:
                proxy = ChaoHubAppProxy(self)
                mod["instance"].initialize(proxy)
            except Exception as e:
                print(f"[MOD INITIALIZE ERROR: '{mod['manifest'].get('name')}' FAILED - BYPASSING]")
                print(f"Details: {e}")

        # Initialize Plant Module
        self.cyber_plant = None

        # P2P LAN Node Discovery Mesh Initial State
        self.instance_id = uuid.uuid4().hex
        self.active_peers = {}
        self.active_peers_lock = threading.Lock()
        self.p2p_stop_event = threading.Event()
        self.p2p_port = 28411
        self.listener_socket = None

        # Backdoor Exit Hotkey: Ctrl+Shift+Q
        # Binds globally inside application to prevent trap lockouts
        self.root.bind("<Control-Shift-KeyPress-Q>", self.shutdown)
        
        # Global glitch manually via Ctrl+Shift+G
        self.root.bind("<Control-Shift-KeyPress-G>", lambda e: self.glitch_manager.trigger_global_glitch(duration=400, magnitude=0.5))
        
        # Prevent standard Alt+F4 closure
        self.root.bind("<Alt-KeyPress-F4>", lambda e: "break")
        self.root.protocol("WM_DELETE_WINDOW", self.prevent_close)

        # Flag to track state on exit loops
        self.root_destroyed = False

        # Load simulated boot cinematic first, passing the glitch manager
        self.boot_frame = BootCinematic(self.root, self.glitch_manager, self.on_boot_complete)

    def prevent_close(self):
        # Simply block close calls to enforce takeover feel
        pass

    def on_boot_complete(self):
        self.boot_frame.destroy()
        self.build_main_ui()

        # Inactivity Monitoring setup
        self.idle_timeout = 60000
        self.idle_job = None
        self.screensaver = None
        self.screensaver_active = False

        # Bind presence events globally to capture user activity
        self.root.bind_all("<Motion>", self.reset_idle_timer)
        self.root.bind_all("<Any-KeyPress>", self.reset_idle_timer)
        self.root.bind_all("<Button-1>", self.reset_idle_timer)

        # Trigger initial idle timer loop
        self.reset_idle_timer()

    def reset_idle_timer(self, event=None):
        """Resets the inactivity countdown. Wakes from screensaver if active."""
        if self.screensaver_active:
            self.screensaver_active = False
            if self.screensaver:
                self.screensaver.stop()
                self.screensaver.destroy()  # Clear memory and completely drop active window elements
                self.screensaver = None
                
                # Re-elevate standard interface panels
                tk.Misc.lift(self.sidebar)
                tk.Misc.lift(self.main_container)
                self.root.after(50, lambda: self.root.focus_force())
            play_sound_effect("beep")

        if self.idle_job:
            self.root.after_cancel(self.idle_job)

        self.idle_job = self.root.after(self.idle_timeout, self.activate_screensaver)

    def activate_screensaver(self):
        """Activates a random full-screen screensaver overlay overlay."""
        self.screensaver_active = True
        
        # Roll an equal percentage check chance for the screensaver selection
        screensaver_options = [
            MatrixScreensaverOverlay,
            StarfieldScreensaverOverlay,
            BlobMeltScreensaverOverlay
        ]
        chosen_screensaver_class = random.choice(screensaver_options)
        
        # Dynamically build whatever widget won the roll
        self.screensaver = chosen_screensaver_class(self.root)

        self.screensaver.grid(row=0, column=0, columnspan=2, sticky="nsew")
        tk.Misc.lift(self.screensaver)
        self.screensaver.start()

    def build_main_ui(self):
        # Primary container grid
        self.root.columnconfigure(0, weight=0) # Sidebar navigation
        self.root.columnconfigure(1, weight=1) # Active module view
        self.root.rowconfigure(0, weight=1)

        # Left Navigation Sidebar Frame
        # Layout uses padding to wiggle slightly (friction aesthetic)
        # Left Navigation Sidebar Frame
        # Layout uses padding to wiggle slightly (friction aesthetic)
        self.sidebar = tk.Frame(self.root, bg=BG_PANEL, highlightthickness=1, highlightbackground=FG_CYAN)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

        title_lbl = tk.Label(self.sidebar, text="CHAO_HUB v1.0", fg=FG_MAGENTA, bg=BG_PANEL, font=("Courier", 14, "bold"))
        title_lbl.pack(pady=15, padx=10)

        # P2P Node Discovery Status Label
        self.p2p_label = tk.Label(self.sidebar, text="OTHER NODES DETECTED: [00]", fg="#555555", bg=BG_PANEL, font=("Courier", 9, "bold"))
        self.p2p_label.pack(pady=(0, 10))

        # Register main UI nodes to glitch temporal ticks
        self.glitch_manager.register_widget(self.sidebar, hover=False, click=False, temporal=True, magnitude=0.1)
        self.glitch_manager.register_widget(title_lbl, hover=True, click=True, temporal=True, magnitude=0.2)
        self.glitch_manager.register_widget(self.p2p_label, hover=True, click=True, temporal=True, magnitude=0.15)

        # Navigation buttons mapping to class components
        self.modules = {
            "ARCHIVE CONTRABAND": lambda p: BooksModule(p),
            "SONIC PLUNDERER": lambda p: MusicModule(p),
            "SHORTWAVE RADIO": lambda p: PodcastsModule(p),
            "DISTRACTION WIDGETS": lambda p: WidgetsModule(p, self.root),
            "ARCADE CORE": lambda p: GamesModule(p, self.glitch_manager),
            "CREATIVE SUITE": lambda p: CreativeSuiteModule(p),
            "TERMINAL SHELL": lambda p: TerminalModule(p),
            "IRC CHAT ROOM": lambda p: HackerChatModule(p),
            "CHAONET PROXY": lambda p: ChaoNetModule(p, self.glitch_manager),
            "TROPHY ROOM": lambda p: AchievementsModule(p)
        }

        # Append dynamic navigation tabs from loaded mods (Vector A)
        for mod in self.mod_loader.mods:
            manifest = mod["manifest"]
            if manifest.get("type") == "NEW_MODULE":
                entry_class = getattr(mod["module"], manifest["entry_point"])
                if manifest["name"] not in self.modules:
                    self.modules[manifest["name"]] = lambda p, cls=entry_class: cls(p, self)

        self.nav_buttons = {}
        for name in self.modules.keys():
            btn = tk.Button(self.sidebar, text=name, command=lambda n=name: self.switch_module(n),
                            bg=BG_DARK, fg=FG_GREEN, activebackground=FG_GREEN, activeforeground=BG_DARK,
                            font=("Courier", 10, "bold"), bd=1, highlightbackground=FG_GREEN)
            btn.pack(fill="x", padx=10, pady=8)
            self.nav_buttons[name] = btn
            # Register nav button triggers
            self.glitch_manager.register_widget(btn, hover=True, click=True, temporal=False, magnitude=0.18)

        self.plant_frame = tk.Frame(self.sidebar, bg=BG_PANEL)
        self.plant_frame.pack(side="bottom", fill="x", padx=10, pady=(10, 0))

        self.cyber_plant = CyberPlantManager(
            parent_frame=self.plant_frame,
            glitch_manager=self.glitch_manager
        )

        # Backdoor exit indicator (flashing broken pixel warning)
        self.exit_label = tk.Label(self.sidebar, text="[ BACKDOOR: Ctrl+Shift+Q ]", fg="#333333", bg=BG_PANEL, font=("Courier", 8))
        self.exit_label.pack(side="bottom", pady=10)
        self.glitch_manager.register_widget(self.exit_label, hover=True, click=True, temporal=True, magnitude=0.3)

        # Right Main Content Container
        self.main_container = tk.Frame(self.root, bg=BG_DARK)
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=4, pady=4)
        self.glitch_manager.register_widget(self.main_container, hover=False, click=False, temporal=True, magnitude=0.08)

        self.current_frame = None

        # Start jiggling thread for navigation panel (friction effect)
        self.jiggle_sidebar()

        # Start P2P Mesh Threads and UI Pump
        self.start_p2p_discovery()
        self.update_p2p_ui()
        
        # Load default Books Module
        self.switch_module("ARCHIVE CONTRABAND")

    def unregister_all_glitch_widgets(self, parent):
        """Recursively unregisters all child widgets under parent from the GlitchManager."""
        widgets = [parent]
        try:
            widgets.extend(parent.winfo_children())
        except Exception:
            pass
        for w in widgets:
            self.glitch_manager.unregister_widget(w)

    def register_module_widgets(self, module_name, frame):
        """Inspects dynamically loaded modules and hooks up their key visual widgets."""
        if not hasattr(self, "glitch_manager"):
            return
            
        # Give Tkinter a brief window to map layout boundaries
        self.root.after(100, lambda: self._do_register_module_widgets(module_name, frame))

    def _do_register_module_widgets(self, module_name, frame):
        try:
            if not frame.winfo_exists():
                return
        except Exception:
            return
            
        if module_name == "ARCHIVE CONTRABAND":
            if hasattr(frame, "listbox"):
                self.glitch_manager.register_widget(frame.listbox, magnitude=0.2)
            if hasattr(frame, "text_widget"):
                self.glitch_manager.register_widget(frame.text_widget, magnitude=0.15)
            if hasattr(frame, "tts_btn"):
                self.glitch_manager.register_widget(frame.tts_btn, magnitude=0.25)
                
        elif module_name == "SONIC PLUNDERER":
            if hasattr(frame, "listbox"):
                self.glitch_manager.register_widget(frame.listbox, magnitude=0.2)
            if hasattr(frame, "play_btn"):
                self.glitch_manager.register_widget(frame.play_btn, magnitude=0.25)
            if hasattr(frame, "pause_btn"):
                self.glitch_manager.register_widget(frame.pause_btn, magnitude=0.25)
            if hasattr(frame, "stop_btn"):
                self.glitch_manager.register_widget(frame.stop_btn, magnitude=0.25)
            if hasattr(frame, "bar_canvas"):
                self.glitch_manager.register_widget(frame.bar_canvas, magnitude=0.3)
            if hasattr(frame, "visualizer"):
                self.glitch_manager.register_widget(frame.visualizer, magnitude=0.2)
                
        elif module_name == "SHORTWAVE RADIO":
            if hasattr(frame, "listbox"):
                self.glitch_manager.register_widget(frame.listbox, magnitude=0.2)
            if hasattr(frame, "desc_text"):
                self.glitch_manager.register_widget(frame.desc_text, magnitude=0.15)
            if hasattr(frame, "fetch_btn"):
                self.glitch_manager.register_widget(frame.fetch_btn, magnitude=0.25)
            if hasattr(frame, "visualizer"):
                self.glitch_manager.register_widget(frame.visualizer, magnitude=0.2)
            if hasattr(frame, "left_frame"):
                for child in frame.left_frame.winfo_children():
                    if isinstance(child, tk.Button):
                        self.glitch_manager.register_widget(child, magnitude=0.22)
                        
        elif module_name == "DISTRACTION WIDGETS":
            if hasattr(frame, "clock_label"):
                self.glitch_manager.register_widget(frame.clock_label, magnitude=0.35)
            if hasattr(frame, "sw_label"):
                self.glitch_manager.register_widget(frame.sw_label, magnitude=0.35)
            if hasattr(frame, "canvas"):
                self.glitch_manager.register_widget(frame.canvas, magnitude=0.3)
            if hasattr(frame, "start_pomo_btn"):
                self.glitch_manager.register_widget(frame.start_pomo_btn, magnitude=0.2)
            if hasattr(frame, "reset_pomo_btn"):
                self.glitch_manager.register_widget(frame.reset_pomo_btn, magnitude=0.2)
            if hasattr(frame, "debug_btn"):
                self.glitch_manager.register_widget(frame.debug_btn, magnitude=0.25)
            if hasattr(frame, "start_sw_btn"):
                self.glitch_manager.register_widget(frame.start_sw_btn, magnitude=0.2)
            if hasattr(frame, "reset_sw_btn"):
                self.glitch_manager.register_widget(frame.reset_sw_btn, magnitude=0.2)
                
        elif module_name == "ARCADE CORE":
            if hasattr(frame, "buttons"):
                for btn in frame.buttons.values():
                    self.glitch_manager.register_widget(btn, magnitude=0.2)
            if hasattr(frame, "game_container"):
                self.glitch_manager.register_widget(frame.game_container, magnitude=0.25)
                
        elif module_name == "TERMINAL SHELL":
            if hasattr(frame, "text_widget"):
                self.glitch_manager.register_widget(frame.text_widget, magnitude=0.15)
            if hasattr(frame, "entry"):
                self.glitch_manager.register_widget(frame.entry, magnitude=0.2)

        elif module_name == "CREATIVE SUITE":
            if hasattr(frame, "canvas"):
                self.glitch_manager.register_widget(frame.canvas, magnitude=0.18)
            if hasattr(frame, "btn_16"):
                self.glitch_manager.register_widget(frame.btn_16, magnitude=0.2)
            if hasattr(frame, "btn_32"):
                self.glitch_manager.register_widget(frame.btn_32, magnitude=0.2)
            if hasattr(frame, "btn_grid_toggle"):
                self.glitch_manager.register_widget(frame.btn_grid_toggle, magnitude=0.2)
            if hasattr(frame, "btn_wipe"):
                self.glitch_manager.register_widget(frame.btn_wipe, magnitude=0.2)
            if hasattr(frame, "btn_export"):
                self.glitch_manager.register_widget(frame.btn_export, magnitude=0.25)
            if hasattr(frame, "status_label"):
                self.glitch_manager.register_widget(frame.status_label, magnitude=0.15)
            if hasattr(frame, "swatch_frames"):
                for swatch_frame in frame.swatch_frames.values():
                    self.glitch_manager.register_widget(swatch_frame, magnitude=0.15)
                    
        elif module_name == "IRC CHAT ROOM":
            if hasattr(frame, "log_widget"):
                self.glitch_manager.register_widget(frame.log_widget, magnitude=0.15)
            if hasattr(frame, "entry"):
                self.glitch_manager.register_widget(frame.entry, magnitude=0.2)
            if hasattr(frame, "sidebar_frame"):
                for child in frame.sidebar_frame.winfo_children():
                    if isinstance(child, tk.Button):
                        self.glitch_manager.register_widget(child, magnitude=0.2)
                        
        elif module_name == "CHAONET PROXY":
            if hasattr(frame, "address_entry"):
                self.glitch_manager.register_widget(frame.address_entry, magnitude=0.15)
            if hasattr(frame, "back_btn"):
                self.glitch_manager.register_widget(frame.back_btn, magnitude=0.2)
            if hasattr(frame, "refresh_btn"):
                self.glitch_manager.register_widget(frame.refresh_btn, magnitude=0.2)
            if hasattr(frame, "connect_btn"):
                self.glitch_manager.register_widget(frame.connect_btn, magnitude=0.2)
        else:
            # Fallback auto-registration for custom loaded mods (Vector A)
            try:
                widgets = [frame]
                widgets.extend(frame.winfo_children())
                for w in widgets:
                    if isinstance(w, (tk.Button, tk.Label, tk.Canvas)):
                        self.glitch_manager.register_widget(w, hover=True, click=True, temporal=True, magnitude=0.20)
            except Exception:
                pass

    def switch_module(self, name):
        play_sound_effect("beep")
        self.current_module_name = name
        if self.current_frame:
            if hasattr(self.current_frame, 'stop_tts_engine'):
                self.current_frame.stop_tts_engine()
            self.unregister_all_glitch_widgets(self.current_frame)
            self.current_frame.destroy()

        # Update button visual focus
        for btn_name, btn in self.nav_buttons.items():
            if btn_name == name:
                btn.config(bg=FG_GREEN, fg=BG_DARK)
            else:
                btn.config(bg=BG_DARK, fg=FG_GREEN)

        self.current_frame = self.modules[name](self.main_container)
        self.current_frame.pack(fill="both", expand=True)
        self.register_module_widgets(name, self.current_frame)

    def jiggle_sidebar(self):
        """Randomly offsets the sidebar grid coordinate weights slightly, creating jiggling menus."""
        if not self.root_destroyed:
            try:
                padx_shift = random.choice([2, 4, 6])
                pady_shift = random.choice([2, 4, 6])
                self.sidebar.grid_configure(padx=(padx_shift, 8 - padx_shift), pady=(pady_shift, 8 - pady_shift))
            except Exception:
                pass
            self.root.after(random.randint(900, 1600), self.jiggle_sidebar)

    def start_p2p_discovery(self):
        """Spins up the broadcaster and listener threads to manage node discovery."""
        self.broadcaster_thread = threading.Thread(target=self._p2p_broadcaster, daemon=True)
        self.listener_thread = threading.Thread(target=self._p2p_listener, daemon=True)
        self.broadcaster_thread.start()
        self.listener_thread.start()

    def _p2p_broadcaster(self):
        """Periodically broadcasts this instance's UUID to both local loopback and the wide broadcast address."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        payload = f"CHAOHUB_PING_v1:{self.instance_id}".encode('utf-8')
        targets = [("255.255.255.255", self.p2p_port), ("127.0.0.1", self.p2p_port)]
        
        while not self.p2p_stop_event.is_set():
            for target in targets:
                try:
                    sock.sendto(payload, target)
                except Exception:
                    pass
            # Sleep in short intervals to remain responsive to shutdown triggers
            for _ in range(40):
                if self.p2p_stop_event.is_set():
                    break
                time.sleep(0.1)
        try:
            sock.close()
        except Exception:
            pass

    def _p2p_listener(self):
        """Listens for CHAOHUB_PING packets from other nodes on the LAN/localhost."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        bound = False
        try:
            sock.bind(("0.0.0.0", self.p2p_port))
            bound = True
        except socket.error as e:
            print(f"[P2P Discovery] Port {self.p2p_port} bind failed: {e}. Falling back to listen-only / offset.")
            # Try binding to alternative offset ports
            for offset in range(1, 6):
                try:
                    sock.bind(("0.0.0.0", self.p2p_port + offset))
                    bound = True
                    break
                except socket.error:
                    pass
                    
        if not bound:
            try:
                sock.close()
            except Exception:
                pass
            return
            
        self.listener_socket = sock
        sock.settimeout(1.0)
        
        while not self.p2p_stop_event.is_set():
            try:
                data, addr = sock.recvfrom(1024)
                message = data.decode('utf-8', errors='ignore')
                if message.startswith("CHAOHUB_PING_v1:"):
                    peer_uuid = message.split(":", 1)[1]
                    if peer_uuid != self.instance_id:
                        with self.active_peers_lock:
                            self.active_peers[peer_uuid] = time.time()
            except socket.timeout:
                continue
            except Exception:
                break
                
        try:
            sock.close()
        except Exception:
            pass

    def update_p2p_ui(self):
        """Thread-safe UI update pump running in the Tkinter main thread."""
        if self.root_destroyed:
            return
            
        now = time.time()
        with self.active_peers_lock:
            # TTL Loop: Prune peers that haven't broadcasted in the last 10 seconds
            expired = [uuid for uuid, last_seen in self.active_peers.items() if now - last_seen > 10.0]
            for uuid in expired:
                del self.active_peers[uuid]
            peer_count = len(self.active_peers)
            
        # Telemetry: check grid_link achievement
        if peer_count > 0:
            try:
                self.achievement_manager.grant_achievement("grid_link")
            except Exception:
                pass
            
        # Update text & active pulsing color schemes
        if peer_count == 0:
            self.p2p_label.config(text="OTHER NODES DETECTED: [00]", fg="#555555")
        else:
            # Alternating neon cyan and warning yellow for warning status indicators
            color = FG_CYAN if (int(time.time() * 2) % 2 == 0) else FG_YELLOW
            self.p2p_label.config(text=f"OTHER NODES DETECTED: [{peer_count:02d}]", fg=color)
            
        self.root.after(500, self.update_p2p_ui)

    def shutdown(self, event=None):
        """Safely stops music, releases hooks, and exits the application window."""
        self.root_destroyed = True
        
        # Clean teardown for all loaded mods
        if hasattr(self, "mod_loader") and self.mod_loader:
            for mod in self.mod_loader.mods:
                try:
                    mod["instance"].teardown()
                except Exception as e:
                    print(f"Error during teardown of mod {mod['manifest'].get('name', 'unknown')}: {e}")

        # Stop P2P discovery loops
        if hasattr(self, 'p2p_stop_event'):
            self.p2p_stop_event.set()
        
        # Instantly close listener socket to unblock recvfrom()
        if hasattr(self, 'listener_socket') and self.listener_socket:
            try:
                self.listener_socket.close()
            except Exception:
                pass
                
        # Join threads cleanly
        if hasattr(self, 'broadcaster_thread') and self.broadcaster_thread:
            self.broadcaster_thread.join(timeout=0.5)
        if hasattr(self, 'listener_thread') and self.listener_thread:
            self.listener_thread.join(timeout=0.5)
            
        try:
            if self.current_frame and hasattr(self.current_frame, 'stop_tts_engine'):
                self.current_frame.stop_tts_engine()
            
            pygame.mixer.music.stop()
            pygame.mixer.quit()
        except Exception:
            pass
        self.root.destroy()
        sys.exit(0)

# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================
if __name__ == "__main__":
    # 1. Initialize Folders and Synthesize Content
    initialize_directories_and_files()

    # 2. Start Tkinter Mainloop Takeover
    root = tk.Tk()
    app = ChaoHubApp(root)
    root.mainloop()