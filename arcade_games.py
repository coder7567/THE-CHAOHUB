import os
import sys
import math
import time
import random
import traceback
import tkinter as tk
from PIL import Image, ImageTk

# Initialize Pygame and font safely
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame

try:
    pygame.font.init()
except Exception as e:
    print(f"Pygame font init warning: {e}", file=sys.stderr)

# Clean terminal sound bridge
def trigger_sound(name):
    try:
        from chaohub import play_sound_effect
        play_sound_effect(name)
    except Exception:
        pass

# ==============================================================================
# BASE PYGAME FRAME BRIDGING TKINTER CANVAS
# ==============================================================================
class PygameGameFrame(tk.Frame):
    def __init__(self, parent, width=600, height=400, difficulty=2, glitch_manager=None):
        super().__init__(parent, bg="#000000")
        self.width = width
        self.height = height
        self.difficulty = difficulty
        self.glitch_manager = glitch_manager
        
        # Mode Selection Bar
        self.mode_frame = tk.Frame(self, bg="#000000")
        self.mode_frame.pack(side="top", fill="x", pady=5)
        
        self.mode = "SINGLE"
        
        self.single_btn = tk.Button(self.mode_frame, text="[ SINGLE PLAYER ]", font=("Courier", 10, "bold"), bd=1,
                                    bg="#00ff00", fg="#000000", activebackground="#00ff00", activeforeground="#000000",
                                    command=lambda: self.set_mode("SINGLE"))
        self.single_btn.pack(side="left", expand=True, fill="x", padx=5)
        
        self.multi_btn = tk.Button(self.mode_frame, text="[ LOCAL MULTIPLAYER ]", font=("Courier", 10, "bold"), bd=1,
                                   bg="#000000", fg="#00ff00", activebackground="#00ff00", activeforeground="#000000",
                                   command=lambda: self.set_mode("MULTIPLAYER"))
        self.multi_btn.pack(side="left", expand=True, fill="x", padx=5)
        
        # UI Container
        self.canvas = tk.Canvas(self, width=self.width, height=self.height, bg="#000000", highlightthickness=1, highlightbackground="#ff00ff")
        self.canvas.pack(expand=True, pady=10)
        
        # Offscreen Pygame surface
        self.pygame_surface = pygame.Surface((self.width, self.height))
        self.clock = pygame.time.Clock()
        
        # Non-blocking key states
        self.keys = {}
        self.pressed_keys = {}
        
        # Pre-allocated image item for GC throttling
        self.photo = None
        self.image_item_id = self.canvas.create_image(0, 0, anchor="nw")
        
        # Binds
        self.canvas.bind("<FocusIn>", self.on_focus_in)
        self.canvas.bind("<FocusOut>", self.on_focus_out)
        self.canvas.bind("<Button-1>", lambda event: self.canvas.focus_set())
        self.canvas.bind("<KeyPress>", self.on_key_press)
        self.canvas.bind("<KeyRelease>", self.on_key_release)
        
        self.running = True
        self.error_state = False
        self.error_message = ""
        
        # Start game logic
        self.reset_game()
        self.run_loop()
        
        # Grab focus instantly on creation
        self.after(100, self.canvas.focus_set)

    def set_mode(self, mode):
        if self.mode != mode:
            trigger_sound("click")
            self.mode = mode
            if self.mode == "SINGLE":
                self.single_btn.config(bg="#00ff00", fg="#000000")
                self.multi_btn.config(bg="#000000", fg="#00ff00")
            else:
                self.single_btn.config(bg="#000000", fg="#00ff00")
                self.multi_btn.config(bg="#ff00ff", fg="#000000")
            
            if hasattr(self, 'canvas') and self.canvas:
                self.canvas.delete("all")
                # Re-create the image item so that render_to_canvas can update it
                self.image_item_id = self.canvas.create_image(0, 0, anchor="nw")
                
            try:
                pygame.mixer.stop()
            except Exception:
                pass
                
            self.reset_game()

    def on_focus_in(self, event):
        self.canvas.config(highlightbackground="#00ffff")

    def on_focus_out(self, event):
        self.canvas.config(highlightbackground="#ff00ff")

    def on_key_press(self, event):
        key = event.keysym
        self.keys[key] = True
        self.pressed_keys[key] = True
        self.pressed_keys[key.lower()] = True
        self.pressed_keys[key.upper()] = True
        if event.char:
            char_key = event.char
            self.pressed_keys[char_key] = True
            self.pressed_keys[char_key.lower()] = True
            self.pressed_keys[char_key.upper()] = True
        self.handle_single_key(key)

    def on_key_release(self, event):
        key = event.keysym
        self.keys[key] = False
        self.pressed_keys[key] = False
        self.pressed_keys[key.lower()] = False
        self.pressed_keys[key.upper()] = False
        if event.char:
            char_key = event.char
            self.pressed_keys[char_key] = False
            self.pressed_keys[char_key.lower()] = False
            self.pressed_keys[char_key.upper()] = False

    def handle_single_key(self, key):
        """Override for discrete keystroke events (e.g. menus or single snaps)."""
        pass

    def reset_game(self):
        pass

    def update(self, dt):
        pass

    def draw(self, surface):
        pass

    def render_to_canvas(self):
        try:
            # Convert surface to raw RGBA bytes
            try:
                data = pygame.image.tostring(self.pygame_surface, "RGBA")
            except AttributeError:
                data = pygame.image.tobytes(self.pygame_surface, "RGBA")
                
            img = Image.frombytes("RGBA", (self.width, self.height), data)
            
            # Persistent PhotoImage update
            self.photo = ImageTk.PhotoImage(img)
            
            # Diagnostic Logging
            item_type = self.canvas.type(self.image_item_id)
            if item_type is None:
                if not hasattr(self, '_diagnostic_logged') or not self._diagnostic_logged:
                    print(f"\n[ArcadeCore DIAGNOSTIC] Failure Detected!", file=sys.stderr)
                    print(f"  - canvas.find_all() output: {self.canvas.find_all()}", file=sys.stderr)
                    print(f"  - self.image_item_id value: {self.image_item_id}", file=sys.stderr)
                    print(f"  - Reason: The image item ID {self.image_item_id} was deleted from the canvas (probably by canvas.delete('all')).", file=sys.stderr)
                    print(f"  - Consequence: canvas.itemconfig() fails silently as a no-op.", file=sys.stderr)
                    self._diagnostic_logged = True
            else:
                self._diagnostic_logged = False

            self.canvas.itemconfig(self.image_item_id, image=self.photo)
        except Exception as e:
            print(f"[ArcadeCore] Rendering failed: {e}", file=sys.stderr)

    def run_loop(self):
        if not self.running:
            return
            
        try:
            # Precison 60 FPS lock using Pygame clock
            dt_ms = self.clock.tick(60)
            dt = dt_ms / 1000.0
            dt = min(dt, 0.1)  # Cap step size to avoid warp speed anomalies
            
            if not self.error_state:
                self.update(dt)
                self.draw(self.pygame_surface)
            else:
                self.draw_error_screen(self.pygame_surface)
                
            self.render_to_canvas()
            
        except Exception as e:
            print(f"[ArcadeCore] Exception caught in frame loop: {e}", file=sys.stderr)
            traceback.print_exc()
            self.error_state = True
            self.error_message = f"RUNTIME FAULT: {str(e)[:40]}..."
            
        if self.running:
            self.after(1, self.run_loop)

    def draw_error_screen(self, surface):
        surface.fill((0, 0, 0))
        
        # Scanlines
        for y in range(0, self.height, 4):
            pygame.draw.line(surface, (15, 0, 15), (0, y), (self.width, y))
            
        font = pygame.font.SysFont("Courier", 18, bold=True)
        
        # Alert frame
        pygame.draw.rect(surface, (255, 0, 0), (50, 80, self.width - 100, 240), 2)
        
        title = font.render("☠ CORE INTRUSION EXCEPTION ☠", True, (255, 0, 0))
        surface.blit(title, (self.width // 2 - title.get_width() // 2, 110))
        
        msg = font.render(self.error_message.upper(), True, (255, 255, 255))
        surface.blit(msg, (self.width // 2 - msg.get_width() // 2, 160))
        
        prompt = font.render("PRESS 'R' TO REBOOT SEGMENT", True, (255, 255, 0))
        surface.blit(prompt, (self.width // 2 - prompt.get_width() // 2, 220))
        
        exit_prompt = font.render("PRESS 'ESC' TO TERMINATE PROGRAM", True, (0, 255, 255))
        surface.blit(exit_prompt, (self.width // 2 - exit_prompt.get_width() // 2, 260))

        if self.keys.get("r") or self.keys.get("R") or self.pressed_keys.get("r") or self.pressed_keys.get("R"):
            self.error_state = False
            self.reset_game()
        elif self.keys.get("Escape") or self.pressed_keys.get("Escape"):
            self.return_to_main_menu()

    def return_to_main_menu(self):
        self.running = False
        try:
            import __main__
            if hasattr(__main__, 'app') and __main__.app:
                __main__.app.switch_module("ARCHIVE CONTRABAND")
        except Exception as e:
            print(f"[ArcadeCore] Navigation escape failed: {e}", file=sys.stderr)

    def destroy(self):
        self.running = False
        super().destroy()


# ==============================================================================
# ENTITIES FOR CYBER BLOCK BREAKER
# ==============================================================================
class CyberBall:
    def __init__(self, x, y, dx, dy, radius=6):
        self.x = float(x)
        self.y = float(y)
        self.dx = float(dx)
        self.dy = float(dy)
        self.radius = radius
        self.is_caught = False
        self.offset_x = 0.0

class CyberBlock:
    def __init__(self, x, y, w, h, color, health, score_val):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = color
        self.health = health
        self.max_health = health
        self.score_val = score_val

class CyberPowerUp:
    def __init__(self, x, y, p_type, speed=130):
        self.x = float(x)
        self.y = float(y)
        self.type = p_type  # "EXPAND", "MULTI", "LASER", "STICKY"
        self.speed = speed
        self.width = 24
        self.height = 14

class CyberLaser:
    def __init__(self, x, y, speed=380):
        self.x = float(x)
        self.y = float(y)
        self.speed = speed
        self.width = 4
        self.height = 10

class CyberHazard:
    def __init__(self, x, y, speed=180):
        self.x = float(x)
        self.y = float(y)
        self.speed = speed
        self.width = 6
        self.height = 14


# ==============================================================================
# GAME 1: CYBER BLOCK BREAKER (CyberBreak)
# ==============================================================================
class CyberBreak(PygameGameFrame):
    def reset_game(self):
        self.score = 0
        self.high_score = 0
        self.lives = 3
        self.game_state = "MENU"  # "MENU", "PLAYING", "GAMEOVER", "VICTORY"
        self.score_submitted = False
        
        # Warp base paddle width based on difficulty
        paddle_widths = {1: 180, 2: 90, 3: 50, 4: 25}
        self.base_paddle_width = paddle_widths.get(self.difficulty, 90)
        self.paddle_width = self.base_paddle_width
        self.paddle_height = 10
        self.paddle_x = self.width // 2
        self.paddle_y = 360
        self.paddle_speed = 450.0
        
        # Player 2 Paddle for Multiplayer
        self.paddle_x_2 = self.width // 2
        self.paddle_y_2 = 340
        self.paddle_width_2 = self.base_paddle_width
        
        self.balls = []
        self.blocks = []
        self.powerups = []
        self.lasers = []
        self.hazards = [] # Falling red blasters (laser fire debris)
        
        # State timers
        self.expand_timer = 0.0
        self.laser_timer = 0.0
        self.sticky_timer = 0.0
        self.is_sticky = False
        self.laser_cooldown = 0.0
        self.controls_inverted_timer = 0.0
        
        # Level 1 Magnetic always-on support
        if self.difficulty == 1:
            self.is_sticky = True
            self.sticky_timer = 99999.0
            
        # Particles
        self.particles = []
        
        self.build_grid()
        self.spawn_initial_ball()

    def build_grid(self):
        self.blocks.clear()
        rows = 5
        cols = 8
        margin_x = 22
        margin_y = 60
        block_w = 68
        block_h = 16
        gap_x = 4
        gap_y = 6
        
        # Scale block health based on difficulty
        hp_multiplier = {1: 1, 2: 1, 3: 1, 4: 2}
        hpm = hp_multiplier.get(self.difficulty, 1)
        
        row_configs = [
            ((255, 255, 0), min(4, 3 * hpm), 50),   # Yellow
            ((255, 0, 255), min(4, 2 * hpm), 40),   # Magenta
            ((0, 255, 255), min(4, 2 * hpm), 30),   # Cyan
            ((0, 255, 0), 1 * hpm, 20),     # Matrix Green
            ((0, 255, 255), 1 * hpm, 10)    # Cyan
        ]
        
        for r in range(rows):
            color, hp, score = row_configs[r]
            if self.difficulty == 1:
                hp = 1
            for c in range(cols):
                bx = margin_x + c * (block_w + gap_x)
                by = margin_y + r * (block_h + gap_y)
                self.blocks.append(CyberBlock(bx, by, block_w, block_h, color, hp, score))

    def spawn_initial_ball(self):
        self.balls.clear()
        ball = CyberBall(self.paddle_x, self.paddle_y - 15, 200, -220)
        ball.is_caught = True
        ball.offset_x = 0.0
        ball.caught_paddle = 1
        self.balls.append(ball)

    def handle_single_key(self, key):
        if self.game_state == "MENU":
            if key in ["s", "S"]:
                self.game_state = "PLAYING"
                trigger_sound("click")
        elif self.game_state in ["GAMEOVER", "VICTORY"]:
            if key in ["r", "R"]:
                self.reset_game()
                self.game_state = "PLAYING"
                trigger_sound("click")
            elif key == "Escape":
                self.return_to_main_menu()
        elif self.game_state == "PLAYING":
            if key == "Escape":
                self.return_to_main_menu()

    def spawn_debris(self, x, y, color, count=10):
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(50, 150)
            self.particles.append({
                "x": float(x),
                "y": float(y),
                "dx": speed * math.cos(angle),
                "dy": speed * math.sin(angle),
                "life": 0.4,
                "color": color
            })

    def update(self, dt):
        if self.game_state != "PLAYING":
            return
            
        # Throttled visual glitch trigger on Tier 4
        if self.difficulty == 4 and self.glitch_manager and random.random() < 0.08:
            self.glitch_manager.trigger_throttled_global_glitch(duration=150, magnitude=0.45, min_interval=1.2)
            
        # Update particles
        retained_particles = []
        for p in self.particles:
            p["x"] += p["dx"] * dt
            p["y"] += p["dy"] * dt
            p["life"] -= dt
            if p["life"] > 0:
                retained_particles.append(p)
        self.particles = retained_particles
            
        # Paddle movement based on mode
        left_pressed = self.pressed_keys.get("Left") or self.pressed_keys.get("a") or self.pressed_keys.get("A")
        right_pressed = self.pressed_keys.get("Right") or self.pressed_keys.get("d") or self.pressed_keys.get("D")
        
        # Malware trap control inversion
        if self.controls_inverted_timer > 0:
            left_pressed, right_pressed = right_pressed, left_pressed
            self.controls_inverted_timer -= dt
            
        if self.mode == "SINGLE":
            if left_pressed:
                self.paddle_x -= self.paddle_speed * dt
            if right_pressed:
                self.paddle_x += self.paddle_speed * dt
        else:
            # Multiplayer stacked defenses
            # Player 1 uses A/D keys
            p1_left = self.pressed_keys.get("a") or self.pressed_keys.get("A")
            p1_right = self.pressed_keys.get("d") or self.pressed_keys.get("D")
            if self.controls_inverted_timer > 0:
                p1_left, p1_right = p1_right, p1_left
                
            if p1_left:
                self.paddle_x -= self.paddle_speed * dt
            if p1_right:
                self.paddle_x += self.paddle_speed * dt
                
            # Player 2 uses Left/Right Arrow keys
            p2_left = self.pressed_keys.get("Left")
            p2_right = self.pressed_keys.get("Right")
            if self.controls_inverted_timer > 0:
                p2_left, p2_right = p2_right, p2_left
                
            if p2_left:
                self.paddle_x_2 -= self.paddle_speed * dt
            if p2_right:
                self.paddle_x_2 += self.paddle_speed * dt
            
        # Constrain Paddle 1
        half_w = self.paddle_width / 2
        if self.paddle_x - half_w < 10:
            self.paddle_x = 10 + half_w
        if self.paddle_x + half_w > self.width - 10:
            self.paddle_x = self.width - 10 - half_w
            
        # Constrain Paddle 2 (Multiplayer)
        if self.mode == "MULTIPLAYER":
            half_w_2 = self.paddle_width_2 / 2
            if self.paddle_x_2 - half_w_2 < 10:
                self.paddle_x_2 = 10 + half_w_2
            if self.paddle_x_2 + half_w_2 > self.width - 10:
                self.paddle_x_2 = self.width - 10 - half_w_2
            
        # Power-up state timers
        if self.expand_timer > 0:
            self.expand_timer -= dt
            self.paddle_width = int(self.base_paddle_width * 1.5)
            self.paddle_width_2 = int(self.base_paddle_width * 1.5)
        else:
            self.paddle_width = self.base_paddle_width
            self.paddle_width_2 = self.base_paddle_width
            
        if self.laser_timer > 0:
            self.laser_timer -= dt
            # Fire P1 blasters on Spacebar or W
            p1_fire = self.pressed_keys.get("space") or self.pressed_keys.get("w") or self.pressed_keys.get("W")
            # Fire P2 blasters on Up Arrow
            p2_fire = self.pressed_keys.get("Up")
            
            if (p1_fire or (self.mode == "MULTIPLAYER" and p2_fire)) and self.laser_cooldown <= 0:
                left_gun = self.paddle_x - half_w + 5
                right_gun = self.paddle_x + half_w - 5
                self.lasers.append(CyberLaser(left_gun, self.paddle_y))
                self.lasers.append(CyberLaser(right_gun, self.paddle_y))
                
                if self.mode == "MULTIPLAYER":
                    left_gun_2 = self.paddle_x_2 - half_w_2 + 5
                    right_gun_2 = self.paddle_x_2 + half_w_2 - 5
                    self.lasers.append(CyberLaser(left_gun_2, self.paddle_y_2))
                    self.lasers.append(CyberLaser(right_gun_2, self.paddle_y_2))
                    
                self.laser_cooldown = 0.28
                trigger_sound("beep")
        
        if self.laser_cooldown > 0:
            self.laser_cooldown -= dt
            
        if self.sticky_timer > 0:
            self.sticky_timer -= dt
            self.is_sticky = True
        else:
            # Level 1 sticky is permanent
            if self.difficulty != 1:
                self.is_sticky = False
            
        # Relaunch caught balls
        p1_release = self.pressed_keys.get("space") or self.pressed_keys.get("w") or self.pressed_keys.get("W")
        p2_release = self.pressed_keys.get("Up")
        if p1_release or (self.mode == "MULTIPLAYER" and p2_release):
            for ball in self.balls:
                if ball.is_caught:
                    ball.is_caught = False
                    ball.dy = -abs(ball.dy)
                    trigger_sound("click")
                    
        # Update balls
        dead_balls = []
        for ball in self.balls:
            if ball.is_caught:
                cp = getattr(ball, 'caught_paddle', 1)
                if cp == 2 and self.mode == "MULTIPLAYER":
                    ball.x = self.paddle_x_2 + ball.offset_x
                    ball.y = self.paddle_y_2 - self.paddle_height//2 - ball.radius
                else:
                    ball.x = self.paddle_x + ball.offset_x
                    ball.y = self.paddle_y - self.paddle_height//2 - ball.radius
                continue
                
            ball.x += ball.dx * dt
            ball.y += ball.dy * dt
            
            # Wall reflection
            if ball.x - ball.radius < 10:
                ball.x = 10 + ball.radius
                ball.dx = abs(ball.dx)
                trigger_sound("click")
            elif ball.x + ball.radius > self.width - 10:
                ball.x = self.width - 10 - ball.radius
                ball.dx = -abs(ball.dx)
                trigger_sound("click")
                
            if ball.y - ball.radius < 40:
                ball.y = 40 + ball.radius
                ball.dy = abs(ball.dy)
                trigger_sound("click")
            elif ball.y + ball.radius > self.height:
                dead_balls.append(ball)
                continue
                
            # Paddle 1 collision
            paddle_rect = pygame.Rect(self.paddle_x - half_w, self.paddle_y - self.paddle_height//2, self.paddle_width, self.paddle_height)
            ball_rect = pygame.Rect(ball.x - ball.radius, ball.y - ball.radius, ball.radius*2, ball.radius*2)
            
            if ball_rect.colliderect(paddle_rect) and ball.dy > 0:
                if self.is_sticky:
                    ball.is_caught = True
                    ball.offset_x = ball.x - self.paddle_x
                    ball.caught_paddle = 1
                    trigger_sound("click")
                else:
                    relative_hit = (ball.x - (self.paddle_x - half_w)) / self.paddle_width
                    relative_hit = max(0.0, min(1.0, relative_hit))
                    influence = (relative_hit - 0.5) * 2.0
                    
                    speed = math.hypot(ball.dx, ball.dy)
                    ball.dx = speed * influence * 0.8
                    ball.dy = -math.sqrt(max(0.15, speed**2 - ball.dx**2))
                    trigger_sound("click")
                    
            # Paddle 2 collision (Multiplayer stacked inner defense)
            if self.mode == "MULTIPLAYER":
                half_w_2 = self.paddle_width_2 / 2
                paddle_rect_2 = pygame.Rect(self.paddle_x_2 - half_w_2, self.paddle_y_2 - self.paddle_height//2, self.paddle_width_2, self.paddle_height)
                
                if ball_rect.colliderect(paddle_rect_2) and ball.dy > 0:
                    if self.is_sticky:
                        ball.is_caught = True
                        ball.offset_x = ball.x - self.paddle_x_2
                        ball.caught_paddle = 2
                        trigger_sound("click")
                    else:
                        relative_hit = (ball.x - (self.paddle_x_2 - half_w_2)) / self.paddle_width_2
                        relative_hit = max(0.0, min(1.0, relative_hit))
                        influence = (relative_hit - 0.5) * 2.0
                        
                        speed = math.hypot(ball.dx, ball.dy)
                        ball.dx = speed * influence * 0.8
                        ball.dy = -math.sqrt(max(0.15, speed**2 - ball.dx**2))
                        trigger_sound("click")
                        
            # Block collisions
            for block in self.blocks[:]:
                if ball_rect.colliderect(block.rect):
                    block.health -= 1
                    self.score += block.score_val
                    if self.score > self.high_score:
                        self.high_score = self.score
                        
                    if block.health <= 0:
                        trigger_sound("explosion")
                        self.spawn_debris(block.rect.centerx, block.rect.centery, block.color, 12)
                        self.blocks.remove(block)
                        
                        # Generate falling hazard lasers in Level 4
                        if self.difficulty == 4:
                            self.hazards.append(CyberHazard(block.rect.centerx, block.rect.centery))
                        else:
                            # Drop powerups (Level 1 drops at 100%, Level 2 at 15%)
                            drop_rate = 1.0 if self.difficulty == 1 else 0.15
                            if random.random() < drop_rate:
                                p_type = random.choice(["EXPAND", "MULTI", "LASER", "STICKY"])
                                self.powerups.append(CyberPowerUp(block.rect.centerx, block.rect.centery, p_type))
                    else:
                        if self.difficulty == 4:
                            trigger_sound("alarm") # In Level 4, play alarm sounds
                        else:
                            trigger_sound("beep")
                        self.spawn_debris(ball.x, ball.y, block.color, 4)
                        
                    overlap_x = min(ball_rect.right - block.rect.left, block.rect.right - ball_rect.left)
                    overlap_y = min(ball_rect.bottom - block.rect.top, block.rect.bottom - ball_rect.top)
                    
                    if overlap_x < overlap_y:
                        if ball.dx > 0 and ball.x < block.rect.centerx:
                            ball.dx = -abs(ball.dx)
                        elif ball.dx < 0 and ball.x > block.rect.centerx:
                            ball.dx = abs(ball.dx)
                    else:
                        if ball.dy > 0 and ball.y < block.rect.centery:
                            ball.dy = -abs(ball.dy)
                        elif ball.dy < 0 and ball.y > block.rect.centery:
                            ball.dy = abs(ball.dy)
                    break
                    
        for b in dead_balls:
            if b in self.balls:
                self.balls.remove(b)
                
        if not self.balls:
            self.lives -= 1
            if self.lives > 0:
                self.spawn_initial_ball()
                self.expand_timer = 0.0
                self.laser_timer = 0.0
                self.sticky_timer = 0.0
                self.controls_inverted_timer = 0.0
                self.hazards.clear()
                trigger_sound("explosion")
            else:
                self.game_state = "GAMEOVER"
                self.hazards.clear()
                trigger_sound("explosion")
                
        if not self.blocks and self.game_state == "PLAYING":
            self.game_state = "VICTORY"
            self.hazards.clear()
            trigger_sound("beep")
            
        # Update powerups
        for pu in self.powerups[:]:
            pu.y += pu.speed * dt
            pu_rect = pygame.Rect(pu.x - pu.width//2, pu.y - pu.height//2, pu.width, pu.height)
            
            # Catch checks for P1 or P2 stacked paddles
            pad1_rect = pygame.Rect(self.paddle_x - half_w, self.paddle_y - self.paddle_height//2, self.paddle_width, self.paddle_height)
            caught = pu_rect.colliderect(pad1_rect)
            
            if self.mode == "MULTIPLAYER" and not caught:
                half_w_2 = self.paddle_width_2 / 2
                pad2_rect = pygame.Rect(self.paddle_x_2 - half_w_2, self.paddle_y_2 - self.paddle_height//2, self.paddle_width_2, self.paddle_height)
                caught = pu_rect.colliderect(pad2_rect)
                
            if caught:
                if self.difficulty == 4:
                    # Malware traps: Pick up inverts controls or shrinks paddle
                    trigger_sound("explosion")
                    if random.random() < 0.5:
                        self.controls_inverted_timer = 5.0
                    else:
                        self.paddle_width = max(10, self.paddle_width - 5)
                        self.paddle_width_2 = max(10, self.paddle_width_2 - 5)
                else:
                    trigger_sound("beep")
                    self.apply_powerup(pu.type)
                self.powerups.remove(pu)
            elif pu.y > self.height:
                self.powerups.remove(pu)
                
        # Update hazards (laser fire debris) in Level 4
        for hz in self.hazards[:]:
            hz.y += hz.speed * dt
            hz_rect = pygame.Rect(hz.x - hz.width//2, hz.y - hz.height//2, hz.width, hz.height)
            
            # Catch checks for P1 or P2 paddles
            pad1_rect = pygame.Rect(self.paddle_x - half_w, self.paddle_y - self.paddle_height//2, self.paddle_width, self.paddle_height)
            hit = hz_rect.colliderect(pad1_rect)
            
            if self.mode == "MULTIPLAYER" and not hit:
                half_w_2 = self.paddle_width_2 / 2
                pad2_rect = pygame.Rect(self.paddle_x_2 - half_w_2, self.paddle_y_2 - self.paddle_height//2, self.paddle_width_2, self.paddle_height)
                hit = hz_rect.colliderect(pad2_rect)
                
            if hit:
                # Laser debris destroys paddle on contact!
                trigger_sound("explosion")
                self.lives -= 1
                self.hazards.clear()
                self.powerups.clear()
                if self.lives > 0:
                    self.spawn_initial_ball()
                    self.controls_inverted_timer = 0.0
                else:
                    self.game_state = "GAMEOVER"
                break
            elif hz.y > self.height:
                self.hazards.remove(hz)
                
        # Update lasers
        for l in self.lasers[:]:
            l.y -= l.speed * dt
            l_rect = pygame.Rect(l.x - l.width//2, l.y - l.height//2, l.width, l.height)
            
            if l.y < 40:
                self.lasers.remove(l)
                continue
                
            hit = False
            for block in self.blocks[:]:
                if l_rect.colliderect(block.rect):
                    hit = True
                    block.health -= 1
                    self.score += block.score_val
                    if self.score > self.high_score:
                        self.high_score = self.score
                        
                    if block.health <= 0:
                        trigger_sound("explosion")
                        self.spawn_debris(block.rect.centerx, block.rect.centery, block.color, 12)
                        self.blocks.remove(block)
                        if self.difficulty == 4:
                            self.hazards.append(CyberHazard(block.rect.centerx, block.rect.centery))
                        else:
                            drop_rate = 1.0 if self.difficulty == 1 else 0.15
                            if random.random() < drop_rate:
                                p_type = random.choice(["EXPAND", "MULTI", "LASER", "STICKY"])
                                self.powerups.append(CyberPowerUp(block.rect.centerx, block.rect.centery, p_type))
                    else:
                        trigger_sound("beep")
                        self.spawn_debris(l.x, l.y, block.color, 5)
                        
                    self.lasers.remove(l)
                    break
            if hit:
                continue

        # Check high score qualification when game transitions to GAMEOVER or VICTORY
        if (self.game_state == "GAMEOVER" or self.game_state == "VICTORY") and self.mode == "SINGLE" and not getattr(self, "score_submitted", False):
            self.score_submitted = True
            from leaderboard import check_and_intercept_score
            check_and_intercept_score(self, "CYBER BREAK", self.difficulty, self.score)

    def apply_powerup(self, p_type):
        if p_type == "EXPAND":
            self.expand_timer = 10.0
        elif p_type == "MULTI":
            new_balls = []
            for b in self.balls:
                speed = math.hypot(b.dx, b.dy)
                angle = math.atan2(b.dy, b.dx)
                for ang_offset in [-0.28, 0.28]:
                    n_ang = angle + ang_offset + random.uniform(-0.06, 0.06)
                    n_dx = speed * math.cos(n_ang)
                    n_dy = speed * math.sin(n_ang)
                    ball = CyberBall(b.x, b.y, n_dx, n_dy)
                    ball.caught_paddle = getattr(b, 'caught_paddle', 1)
                    new_balls.append(ball)
            self.balls.extend(new_balls)
        elif p_type == "LASER":
            self.laser_timer = 8.0
        elif p_type == "STICKY":
            self.is_sticky = True
            self.sticky_timer = 10.0

    def draw(self, surface):
        surface.fill((0, 0, 0))
        
        # Cyber-terminal grid background
        grid_col = (15, 0, 0) if self.difficulty == 4 else (8, 12, 8)
        for y in range(40, self.height, 25):
            pygame.draw.line(surface, grid_col, (10, y), (self.width - 10, y))
        for x in range(10, self.width, 25):
            pygame.draw.line(surface, grid_col, (x, 40), (x, self.height))
            
        border_col = (255, 0, 0) if self.difficulty == 4 else (255, 0, 255)
        pygame.draw.rect(surface, border_col, (10, 40, self.width - 20, self.height - 40), 1)
        
        # Draw HUD Panel
        pygame.draw.rect(surface, (11, 11, 11), (0, 0, self.width, 40))
        hud_line_col = (255, 0, 0) if self.difficulty == 4 else (0, 255, 255)
        pygame.draw.line(surface, hud_line_col, (0, 40), (self.width, 40), 2)
        
        font = pygame.font.SysFont("Courier", 13, bold=True)
        hud_txt = font.render(f"SCORE: {self.score:05d}  HI-SCORE: {self.high_score:05d}", True, (255, 0, 0) if self.difficulty == 4 else (0, 255, 255))
        surface.blit(hud_txt, (15, 12))
        
        # Shared life pool (crimson red on Level 4)
        life_col = (255, 0, 0) if self.difficulty == 4 else (0, 255, 0)
        lives_lbl = font.render("SYSTEM LIFE:", True, life_col)
        surface.blit(lives_lbl, (self.width - 160, 12))
        for i in range(self.lives):
            lx = self.width - 60 + i * 16
            pygame.draw.rect(surface, life_col, (lx, 15, 10, 8))
            
        # Draw blocks
        for block in self.blocks:
            fill_color = (int(block.color[0]*0.15), int(block.color[1]*0.15), int(block.color[2]*0.15))
            pygame.draw.rect(surface, fill_color, block.rect)
            pygame.draw.rect(surface, (255, 0, 0) if self.difficulty == 4 else block.color, block.rect, 1)
            
            tw = block.rect.width
            th = block.rect.height
            for h in range(block.health):
                tx = block.rect.left + 5 + h * 8
                ty = block.rect.top + 4
                pygame.draw.rect(surface, (255, 0, 0) if self.difficulty == 4 else block.color, (tx, ty, 4, th - 8))
                
        # Draw power-ups
        for pu in self.powerups:
            color_map = {
                "EXPAND": (0, 255, 255),
                "MULTI": (0, 255, 0),
                "LASER": (255, 0, 255),
                "STICKY": (255, 255, 0)
            }
            color = (255, 0, 0) if self.difficulty == 4 else color_map.get(pu.type, (255, 255, 255))
            px = int(pu.x - pu.width//2)
            py = int(pu.y - pu.height//2)
            pygame.draw.rect(surface, (0, 0, 0), (px, py, pu.width, pu.height))
            pygame.draw.rect(surface, color, (px, py, pu.width, pu.height), 1)
            
            sym_char = pu.type[0]
            sym = font.render(sym_char, True, color)
            surface.blit(sym, (px + pu.width//2 - sym.get_width()//2, py + pu.height//2 - sym.get_height()//2 + 1))
            
        # Draw hazards (falling red lasers)
        for hz in self.hazards:
            hx = int(hz.x - hz.width//2)
            hy = int(hz.y - hz.height//2)
            pygame.draw.rect(surface, (255, 0, 0), (hx, hy, hz.width, hz.height))
            pygame.draw.rect(surface, (255, 200, 200), (hx + 2, hy + 2, hz.width - 4, hz.height - 4))
            
        # Draw lasers
        for l in self.lasers:
            lx = int(l.x - l.width//2)
            ly = int(l.y - l.height//2)
            pygame.draw.rect(surface, (255, 50, 50), (lx, ly, l.width, l.height))
            
        # Draw particles
        for p in self.particles:
            pygame.draw.circle(surface, p["color"], (int(p["x"]), int(p["y"])), 2)
            
        # Draw defensive structures: Paddle 1 (Outer / Baseline)
        half_w = self.paddle_width // 2
        px = int(self.paddle_x - half_w)
        py = int(self.paddle_y - self.paddle_height//2)
        
        pad_col = (255, 0, 0) if self.difficulty == 4 else (0, 255, 255)
        accent_col = (255, 255, 0) if self.difficulty != 4 else (255, 255, 255)
        
        pygame.draw.rect(surface, pad_col, (px, py, self.paddle_width, self.paddle_height))
        pygame.draw.rect(surface, accent_col, (px, py, min(self.paddle_width, 6), self.paddle_height))
        pygame.draw.rect(surface, accent_col, (px + max(0, self.paddle_width - 6), py, min(self.paddle_width, 6), self.paddle_height))
        
        if self.is_sticky:
            pygame.draw.rect(surface, (0, 255, 0), (px, py, self.paddle_width, self.paddle_height), 1)
        if self.laser_timer > 0:
            pygame.draw.rect(surface, (255, 0, 255), (px - 2, py - 4, 4, 6))
            pygame.draw.rect(surface, (255, 0, 255), (px + self.paddle_width - 2, py - 4, 4, 6))
            
        # Draw Paddle 2 (Inner defense stacked above)
        if self.mode == "MULTIPLAYER":
            half_w_2 = self.paddle_width_2 // 2
            px2 = int(self.paddle_x_2 - half_w_2)
            py2 = int(self.paddle_y_2 - self.paddle_height//2)
            
            pad2_col = (255, 0, 0) if self.difficulty == 4 else (255, 0, 255)
            pygame.draw.rect(surface, pad2_col, (px2, py2, self.paddle_width_2, self.paddle_height))
            pygame.draw.rect(surface, accent_col, (px2, py2, min(self.paddle_width_2, 6), self.paddle_height))
            pygame.draw.rect(surface, accent_col, (px2 + max(0, self.paddle_width_2 - 6), py2, min(self.paddle_width_2, 6), self.paddle_height))
            
            if self.is_sticky:
                pygame.draw.rect(surface, (0, 255, 0), (px2, py2, self.paddle_width_2, self.paddle_height), 1)
            if self.laser_timer > 0:
                pygame.draw.rect(surface, (255, 0, 255), (px2 - 2, py2 - 4, 4, 6))
                pygame.draw.rect(surface, (255, 0, 255), (px2 + self.paddle_width_2 - 2, py2 - 4, 4, 6))
            
        # Draw balls
        for ball in self.balls:
            bx = int(ball.x)
            by = int(ball.y)
            pygame.draw.circle(surface, (255, 0, 0) if self.difficulty == 4 else (0, 255, 0), (bx, by), ball.radius)
            pygame.draw.circle(surface, (255, 255, 255), (bx, by), ball.radius - 2)
            
        # Scanlines
        for y in range(0, self.height, 4):
            pygame.draw.line(surface, (5, 5, 5), (0, y), (self.width, y))
            
        # Screen state overlays
        if self.game_state == "MENU":
            self.draw_overlay_screen(surface, "CYBER BLOCK BREAKER", "PRESS 'S' TO START PROGRAM", (255, 0, 0) if self.difficulty == 4 else (0, 255, 255))
        elif self.game_state == "GAMEOVER":
            self.draw_overlay_screen(surface, "SYSTEM TERMINATED // GAME OVER", "PRESS 'R' TO REBOOT PROGRAM", (255, 0, 0))
        elif self.game_state == "VICTORY":
            self.draw_overlay_screen(surface, "TRANSACTION SECURED // VICTORY ACHIEVED", "PRESS 'R' TO REBOOT PROGRAM", (255, 0, 0) if self.difficulty == 4 else (0, 255, 0))

    def draw_overlay_screen(self, surface, title_str, prompt_str, color):
        pygame.draw.rect(surface, (0, 0, 0), (40, 100, self.width - 80, 200))
        pygame.draw.rect(surface, color, (40, 100, self.width - 80, 200), 2)
        
        font_lg = pygame.font.SysFont("Courier", 20, bold=True)
        font_sm = pygame.font.SysFont("Courier", 12, bold=True)
        
        t_surf = font_lg.render(title_str, True, color)
        p_surf = font_sm.render(prompt_str, True, (255, 255, 0))
        e_surf = font_sm.render("PRESS 'ESC' FOR MAIN ENCLAVE", True, (255, 255, 255))
        
        surface.blit(t_surf, (self.width//2 - t_surf.get_width()//2, 140))
        surface.blit(p_surf, (self.width//2 - p_surf.get_width()//2, 195))
        surface.blit(e_surf, (self.width//2 - e_surf.get_width()//2, 230))


# ==============================================================================
# ENTITIES FOR SHIFTING LANES RACER
# ==============================================================================
class CyberObstacle:
    def __init__(self, lane, y, obs_type):
        self.lane = lane
        self.y = float(y)
        self.type = obs_type  # "WALL", "BLOCKADE", "NODE"
        self.width = 65
        self.height = 22
        
        if obs_type == "WALL":
            self.width = 85
            self.height = 18
        elif obs_type == "BLOCKADE":
            self.width = 75
            self.height = 26
        elif obs_type == "NODE":
            self.width = 40
            self.height = 40


# ==============================================================================
# GAME 2: SHIFTING LANES RACER (NeonRunner)
# ==============================================================================
class NeonRunner(PygameGameFrame):
    def reset_game(self):
        self.score = 0
        self.high_score = 0
        self.game_state = "MENU"  # "MENU", "PLAYING", "GAMEOVER"
        self.winner = None
        self.score_submitted = False
        
        # Difficulty Warp road properties
        if self.difficulty == 1:
            self.lane_width = 160
            self.lanes = [140, 300, 460]
            self.player_width = 20
            self.player_height = 30
            self.base_speed = 150.0
        elif self.difficulty == 3:
            self.lane_width = 100
            self.lanes = [200, 300, 400]
            self.player_width = 32
            self.player_height = 44
            self.base_speed = 300.0
        elif self.difficulty == 4:
            self.lane_width = 80
            self.lanes = [220, 300, 380]
            self.player_width = 32
            self.player_height = 44
            self.base_speed = 400.0
        else: # difficulty == 2
            self.lane_width = 120
            self.lanes = [180, 300, 420]
            self.player_width = 32
            self.player_height = 44
            self.base_speed = 220.0
            
        self.current_lane = 1
        self.player_x = float(self.lanes[self.current_lane])
        self.player_y = 320.0
        
        self.speed_multiplier = 1.0
        self.global_speed = self.base_speed
        
        self.scroll_y = 0.0
        
        self.obstacles = []
        self.spawn_timer = 0.0
        
        # Multiplayer Viewport Setup
        if hasattr(self, 'mode') and self.mode == "MULTIPLAYER":
            if self.difficulty == 1:
                self.lanes_1 = [40, 150, 260]
                self.lanes_2 = [340, 450, 560]
            elif self.difficulty == 3:
                self.lanes_1 = [65, 150, 235]
                self.lanes_2 = [365, 450, 535]
            elif self.difficulty == 4:
                self.lanes_1 = [70, 150, 230]
                self.lanes_2 = [370, 450, 530]
            else: # difficulty == 2
                self.lanes_1 = [60, 150, 240]
                self.lanes_2 = [360, 450, 540]
            
            self.current_lane = 1
            self.player_x = float(self.lanes_1[self.current_lane])
            
            self.current_lane_2 = 1
            self.player_x_2 = float(self.lanes_2[self.current_lane_2])
            
            self.obstacles_2 = []
            self.spawn_timer_2 = 0.0
            
            self.p1_crashed = False
            self.p2_crashed = False
        
        self.shake_time = 0.0
        self.shake_magnitude = 0.0
        self.shake_x = 0
        self.shake_y = 0
        
        self.ambient_stars = []
        for _ in range(35):
            self.ambient_stars.append({
                "x": random.randint(10, self.width - 10),
                "y": random.randint(0, self.height),
                "speed": random.uniform(1.2, 3.5),
                "size": random.randint(1, 2)
            })

    def handle_single_key(self, key):
        if self.game_state == "MENU":
            if key in ["s", "S"]:
                self.game_state = "PLAYING"
                trigger_sound("click")
        elif self.game_state == "GAMEOVER":
            if key in ["r", "R"]:
                self.reset_game()
                self.game_state = "PLAYING"
                trigger_sound("click")
            elif key == "Escape":
                self.return_to_main_menu()
        elif self.game_state == "PLAYING":
            if self.mode == "SINGLE":
                if key in ["Left", "a", "A"] and self.current_lane > 0:
                    self.current_lane -= 1
                    trigger_sound("click")
                elif key in ["Right", "d", "D"] and self.current_lane < 2:
                    self.current_lane += 1
                    trigger_sound("click")
            else:
                # Player 1: A/D or W/S
                if key in ["a", "A", "w", "W"] and self.current_lane > 0:
                    self.current_lane -= 1
                    trigger_sound("click")
                elif key in ["d", "D", "s", "S"] and self.current_lane < 2:
                    self.current_lane += 1
                    trigger_sound("click")
                    
                # Player 2: Left/Right or Up/Down
                if key in ["Left", "Up"] and self.current_lane_2 > 0:
                    self.current_lane_2 -= 1
                    trigger_sound("click")
                elif key in ["Right", "Down"] and self.current_lane_2 < 2:
                    self.current_lane_2 += 1
                    trigger_sound("click")
                    
            if key == "Escape":
                self.return_to_main_menu()

    def update(self, dt):
        if self.shake_time > 0:
            self.shake_time -= dt
            self.shake_x = random.randint(-int(self.shake_magnitude), int(self.shake_magnitude))
            self.shake_y = random.randint(-int(self.shake_magnitude), int(self.shake_magnitude))
        else:
            self.shake_x = 0
            self.shake_y = 0
            
        if self.game_state != "PLAYING":
            return
            
        # Throttled active visual degradation on Tier 4 to protect FPS
        if self.difficulty == 4 and self.glitch_manager and random.random() < 0.08:
            self.glitch_manager.trigger_throttled_global_glitch(duration=150, magnitude=0.45, min_interval=1.5)
            
        self.speed_multiplier += 0.05 * dt
        self.global_speed = self.base_speed * self.speed_multiplier
        
        self.scroll_y = (self.scroll_y + self.global_speed * dt) % 60
        
        for star in self.ambient_stars:
            star["y"] += star["speed"] * self.global_speed * dt * 0.15
            if star["y"] > self.height:
                star["y"] = -10
                star["x"] = random.randint(10, self.width - 10)
                
        if self.mode == "SINGLE":
            target_x = float(self.lanes[self.current_lane])
            self.player_x += (target_x - self.player_x) * (1.0 - math.exp(-18 * dt))
            
            self.spawn_timer -= dt
            if self.spawn_timer <= 0:
                if self.difficulty == 1:
                    spawn_interval = max(1.8, 3.5 / self.speed_multiplier)
                elif self.difficulty == 3:
                    spawn_interval = max(0.5, 1.2 / self.speed_multiplier)
                elif self.difficulty == 4:
                    spawn_interval = max(0.35, 0.7 / self.speed_multiplier)
                else:
                    spawn_interval = max(0.65, 1.7 / self.speed_multiplier)
                    
                self.spawn_timer = spawn_interval + random.uniform(-0.15, 0.15)
                
                # Double spawn probability
                double_spawn_prob = 0.35
                if self.difficulty == 1:
                    double_spawn_prob = 0.0
                elif self.difficulty == 3:
                    double_spawn_prob = 0.5
                elif self.difficulty == 4:
                    double_spawn_prob = 0.75
                
                if self.difficulty != 1 and (self.speed_multiplier > 1.4 or self.difficulty >= 3) and random.random() < double_spawn_prob:
                    lanes = [0, 1, 2]
                    blocked_lanes = random.sample(lanes, 2)
                    for l in blocked_lanes:
                        o_type = random.choice(["WALL", "BLOCKADE", "NODE"])
                        obs = CyberObstacle(l, -40, o_type)
                        if self.difficulty == 4:
                            obs.width = int(obs.width * 1.1)
                        elif self.difficulty == 1:
                            obs.width = int(obs.width * 0.75)
                        self.obstacles.append(obs)
                else:
                    l = random.choice([0, 1, 2])
                    o_type = random.choice(["WALL", "BLOCKADE", "NODE"])
                    obs = CyberObstacle(l, -40, o_type)
                    if self.difficulty == 4:
                        obs.width = int(obs.width * 1.1)
                    elif self.difficulty == 1:
                        obs.width = int(obs.width * 0.75)
                    self.obstacles.append(obs)
                    
            player_rect = pygame.Rect(self.player_x - self.player_width//2, self.player_y - self.player_height//2, self.player_width, self.player_height)
            
            for obs in self.obstacles[:]:
                obs.y += self.global_speed * dt
                
                if obs.y > self.height + 40:
                    self.obstacles.remove(obs)
                    old_score = self.score
                    self.score += 10
                    if self.score > self.high_score:
                        self.high_score = self.score
                        
                    # Milestone check: Crossing a multiple of 50 score
                    if self.difficulty == 4 and (self.score // 50) > (old_score // 50):
                        self.shake_time = 0.6
                        self.shake_magnitude = 18.0
                        trigger_sound("alarm")
                        if self.glitch_manager:
                            self.glitch_manager.trigger_throttled_global_glitch(duration=350, magnitude=0.6, min_interval=1.2)
                    continue
                    
                obs_x = self.lanes[obs.lane]
                obs_rect = pygame.Rect(obs_x - obs.width//2, obs.y - obs.height//2, obs.width, obs.height)
                
                if player_rect.colliderect(obs_rect):
                    self.game_state = "GAMEOVER"
                    self.shake_time = 0.5
                    self.shake_magnitude = 10.0
                    trigger_sound("explosion")
                    break
        else:
            target_x_1 = float(self.lanes_1[self.current_lane])
            self.player_x += (target_x_1 - self.player_x) * (1.0 - math.exp(-18 * dt))
            
            target_x_2 = float(self.lanes_2[self.current_lane_2])
            self.player_x_2 += (target_x_2 - self.player_x_2) * (1.0 - math.exp(-18 * dt))
            
            # Procedural spawn logic for Viewport 1 (P1)
            self.spawn_timer -= dt
            if self.spawn_timer <= 0:
                if self.difficulty == 1:
                    spawn_interval = max(1.8, 3.5 / self.speed_multiplier)
                elif self.difficulty == 3:
                    spawn_interval = max(0.5, 1.2 / self.speed_multiplier)
                elif self.difficulty == 4:
                    spawn_interval = max(0.35, 0.7 / self.speed_multiplier)
                else:
                    spawn_interval = max(0.65, 1.7 / self.speed_multiplier)
                self.spawn_timer = spawn_interval + random.uniform(-0.15, 0.15)
                
                l = random.choice([0, 1, 2])
                o_type = random.choice(["WALL", "BLOCKADE", "NODE"])
                obs = CyberObstacle(l, -40, o_type)
                
                width_scalar = 0.65
                if self.difficulty == 4:
                    width_scalar = 0.8
                elif self.difficulty == 1:
                    width_scalar = 0.5
                obs.width = int(obs.width * width_scalar)
                self.obstacles.append(obs)
                
            # Procedural spawn logic for Viewport 2 (P2)
            self.spawn_timer_2 -= dt
            if self.spawn_timer_2 <= 0:
                if self.difficulty == 1:
                    spawn_interval = max(1.8, 3.5 / self.speed_multiplier)
                elif self.difficulty == 3:
                    spawn_interval = max(0.5, 1.2 / self.speed_multiplier)
                elif self.difficulty == 4:
                    spawn_interval = max(0.35, 0.7 / self.speed_multiplier)
                else:
                    spawn_interval = max(0.65, 1.7 / self.speed_multiplier)
                self.spawn_timer_2 = spawn_interval + random.uniform(-0.15, 0.15)
                
                l = random.choice([0, 1, 2])
                o_type = random.choice(["WALL", "BLOCKADE", "NODE"])
                obs = CyberObstacle(l, -40, o_type)
                
                width_scalar = 0.65
                if self.difficulty == 4:
                    width_scalar = 0.8
                elif self.difficulty == 1:
                    width_scalar = 0.5
                obs.width = int(obs.width * width_scalar)
                self.obstacles_2.append(obs)
                
            # Collision detect Viewport 1 (P1)
            p1_rect = pygame.Rect(self.player_x - self.player_width//2, self.player_y - self.player_height//2, self.player_width, self.player_height)
            for obs in self.obstacles[:]:
                obs.y += self.global_speed * dt
                if obs.y > self.height + 40:
                    self.obstacles.remove(obs)
                    old_score = self.score
                    self.score += 10
                    # Milestone check
                    if self.difficulty == 4 and (self.score // 50) > (old_score // 50):
                        self.shake_time = 0.6
                        self.shake_magnitude = 18.0
                        trigger_sound("alarm")
                        if self.glitch_manager:
                            self.glitch_manager.trigger_throttled_global_glitch(duration=350, magnitude=0.6, min_interval=1.2)
                    continue
                    
                obs_x = self.lanes_1[obs.lane]
                obs_rect = pygame.Rect(obs_x - obs.width//2, obs.y - obs.height//2, obs.width, obs.height)
                if p1_rect.colliderect(obs_rect):
                    self.p1_crashed = True
                    
            # Collision detect Viewport 2 (P2)
            p2_rect = pygame.Rect(self.player_x_2 - self.player_width//2, self.player_y - self.player_height//2, self.player_width, self.player_height)
            for obs in self.obstacles_2[:]:
                obs.y += self.global_speed * dt
                if obs.y > self.height + 40:
                    self.obstacles_2.remove(obs)
                    old_score = self.score
                    self.score += 10
                    # Milestone check
                    if self.difficulty == 4 and (self.score // 50) > (old_score // 50):
                        self.shake_time = 0.6
                        self.shake_magnitude = 18.0
                        trigger_sound("alarm")
                        if self.glitch_manager:
                            self.glitch_manager.trigger_throttled_global_glitch(duration=350, magnitude=0.6, min_interval=1.2)
                    continue
                    
                obs_x = self.lanes_2[obs.lane]
                obs_rect = pygame.Rect(obs_x - obs.width//2, obs.y - obs.height//2, obs.width, obs.height)
                if p2_rect.colliderect(obs_rect):
                    self.p2_crashed = True
                    
            # Survival win check
            if self.p1_crashed or self.p2_crashed:
                self.game_state = "GAMEOVER"
                self.shake_time = 0.5
                self.shake_magnitude = 10.0
                trigger_sound("explosion")
                
                if self.p1_crashed and self.p2_crashed:
                    self.winner = "TIE"
                elif self.p1_crashed:
                    self.winner = "P2 (NEON CYAN)"
                else:
                    self.winner = "P1 (HOT MAGENTA)"

        # Check high score qualification when game transitions to GAMEOVER
        if self.game_state == "GAMEOVER" and self.mode == "SINGLE" and not getattr(self, "score_submitted", False):
            self.score_submitted = True
            from leaderboard import check_and_intercept_score
            check_and_intercept_score(self, "NEON RUNNER", self.difficulty, self.score)

    def draw_obstacle(self, surface, obs, ox, oy, rx, ry, font):
        obs_col = (255, 0, 0) if self.difficulty == 4 else (255, 0, 255)
        text_col = (255, 50, 50) if self.difficulty == 4 else (255, 0, 255)
        
        if obs.type == "WALL":
            pygame.draw.rect(surface, obs_col, (rx, ry, obs.width, obs.height))
            pygame.draw.rect(surface, (0, 0, 0), (rx + 2, ry + 2, obs.width - 4, obs.height - 4))
            t_lbl = font.render("LOCKED" if self.difficulty != 4 else "CRITICAL", True, text_col)
            surface.blit(t_lbl, (ox - t_lbl.get_width()//2, oy - t_lbl.get_height()//2))
        elif obs.type == "BLOCKADE":
            blockade_col = (255, 0, 0) if self.difficulty == 4 else (255, 255, 0)
            pygame.draw.rect(surface, blockade_col, (rx, ry, obs.width, obs.height), 2)
            for offset in range(0, obs.width, 10):
                pygame.draw.line(surface, blockade_col, (rx + offset, ry), (rx + min(obs.width, offset + 8), ry + obs.height - 2), 1)
        elif obs.type == "NODE":
            pts = [
                (ox, ry),
                (rx + obs.width, oy),
                (ox, ry + obs.height),
                (rx, oy)
            ]
            node_col = (255, 0, 0) if self.difficulty == 4 else (0, 255, 255)
            pygame.draw.polygon(surface, node_col, pts, 1)
            dec_lbl = font.render("ERR_0x42" if self.difficulty != 4 else "SYS_HAZARD", True, node_col)
            surface.blit(dec_lbl, (ox - dec_lbl.get_width()//2, oy - dec_lbl.get_height()//2))

    def draw_vehicle(self, surface, px, py, color):
        pw = self.player_width
        ph = self.player_height
        pts_chassis = [
            (px, py - ph//2),
            (px + pw//2, py + ph//2),
            (px + pw//4, py + ph//3),
            (px - pw//4, py + ph//3),
            (px - pw//2, py + ph//2)
        ]
        pygame.draw.polygon(surface, color, pts_chassis, 2)
        
        boost_y = py + ph//2 + 5
        if self.game_state == "PLAYING" and int(time.time() * 20) % 2 == 0:
            pygame.draw.line(surface, (255, 255, 0), (px, boost_y), (px, boost_y + 12), 2)
            pygame.draw.line(surface, (0, 255, 0), (px - 4, boost_y), (px - 4, boost_y + 6), 1)
            pygame.draw.line(surface, (0, 255, 0), (px + 4, boost_y), (px + 4, boost_y + 6), 1)
            
        if self.game_state == "PLAYING":
            light_left = px - pw//4
            light_right = px + pw//4
            pygame.draw.polygon(surface, (0, 30, 30), [(light_left, py - ph//2), (light_left - 25, 0), (light_left + 15, 0)])
            pygame.draw.polygon(surface, (0, 30, 30), [(light_right, py - ph//2), (light_right - 15, 0), (light_right + 25, 0)])

    def draw(self, surface):
        surface.fill((0, 0, 0))
        
        canvas_surface = pygame.Surface((self.width, self.height))
        canvas_surface.fill((0, 0, 0))
        
        # Ambient side space starfield (White/Red stars in level 4)
        for star in self.ambient_stars:
            star_color = (255, 100, 100) if (self.difficulty == 4 and random.random() < 0.25) else (100, 100, 100)
            pygame.draw.rect(canvas_surface, star_color, (int(star["x"]), int(star["y"]), star["size"], star["size"]))
            
        if self.mode == "SINGLE":
            # Road edge margins
            road_col = (255, 0, 0) if self.difficulty == 4 else (0, 255, 255)
            dash_col = (100, 0, 0) if self.difficulty == 4 else (0, 150, 150)
            
            road_left = self.lanes[0] - self.lane_width // 2
            road_right = self.lanes[2] + self.lane_width // 2
            pygame.draw.line(canvas_surface, road_col, (road_left, 0), (road_left, self.height), 2)
            pygame.draw.line(canvas_surface, road_col, (road_right, 0), (road_right, self.height), 2)
            
            dash_y = int(self.scroll_y) - 60
            while dash_y < self.height + 60:
                pygame.draw.line(canvas_surface, dash_col, (self.lanes[0] + self.lane_width//2, dash_y), (self.lanes[0] + self.lane_width//2, dash_y + 25), 1)
                pygame.draw.line(canvas_surface, dash_col, (self.lanes[1] + self.lane_width//2, dash_y), (self.lanes[1] + self.lane_width//2, dash_y + 25), 1)
                dash_y += 60
                
            font = pygame.font.SysFont("Courier", 11, bold=True)
            for obs in self.obstacles:
                ox = self.lanes[obs.lane]
                oy = int(obs.y)
                rx = ox - obs.width // 2
                ry = oy - obs.height // 2
                self.draw_obstacle(canvas_surface, obs, ox, oy, rx, ry, font)
                
            self.draw_vehicle(canvas_surface, self.player_x, self.player_y, (255, 0, 0) if self.difficulty == 4 else (0, 255, 255))
        else:
            # Draw side-by-side vertical divider partition down middle
            pygame.draw.line(canvas_surface, (255, 0, 255), (300, 0), (300, self.height), 3)
            
            # --- Viewport 1 (Player 1 Left) ---
            lane_w_1 = self.lanes_1[1] - self.lanes_1[0]
            road_left_1 = self.lanes_1[0] - lane_w_1 // 2
            road_right_1 = self.lanes_1[2] + lane_w_1 // 2
            
            road_col_1 = (255, 0, 0) if self.difficulty == 4 else (0, 255, 255)
            dash_col_1 = (100, 0, 0) if self.difficulty == 4 else (0, 150, 150)
            
            pygame.draw.line(canvas_surface, road_col_1, (road_left_1, 0), (road_left_1, self.height), 2)
            pygame.draw.line(canvas_surface, road_col_1, (road_right_1, 0), (road_right_1, self.height), 2)
            
            dash_y = int(self.scroll_y) - 60
            while dash_y < self.height + 60:
                pygame.draw.line(canvas_surface, dash_col_1, (self.lanes_1[0] + lane_w_1//2, dash_y), (self.lanes_1[0] + lane_w_1//2, dash_y + 25), 1)
                pygame.draw.line(canvas_surface, dash_col_1, (self.lanes_1[1] + lane_w_1//2, dash_y), (self.lanes_1[1] + lane_w_1//2, dash_y + 25), 1)
                dash_y += 60
                
            font = pygame.font.SysFont("Courier", 8, bold=True)
            for obs in self.obstacles:
                ox = self.lanes_1[obs.lane]
                oy = int(obs.y)
                rx = ox - obs.width // 2
                ry = oy - obs.height // 2
                self.draw_obstacle(canvas_surface, obs, ox, oy, rx, ry, font)
                
            self.draw_vehicle(canvas_surface, self.player_x, self.player_y, (255, 0, 0) if self.difficulty == 4 else (0, 255, 255))
            
            # --- Viewport 2 (Player 2 Right) ---
            lane_w_2 = self.lanes_2[1] - self.lanes_2[0]
            road_left_2 = self.lanes_2[0] - lane_w_2 // 2
            road_right_2 = self.lanes_2[2] + lane_w_2 // 2
            
            road_col_2 = (255, 0, 0) if self.difficulty == 4 else (255, 0, 255)
            dash_col_2 = (100, 0, 0) if self.difficulty == 4 else (150, 0, 150)
            
            pygame.draw.line(canvas_surface, road_col_2, (road_left_2, 0), (road_left_2, self.height), 2)
            pygame.draw.line(canvas_surface, road_col_2, (road_right_2, 0), (road_right_2, self.height), 2)
            
            dash_y = int(self.scroll_y) - 60
            while dash_y < self.height + 60:
                pygame.draw.line(canvas_surface, dash_col_2, (self.lanes_2[0] + lane_w_2//2, dash_y), (self.lanes_2[0] + lane_w_2//2, dash_y + 25), 1)
                pygame.draw.line(canvas_surface, dash_col_2, (self.lanes_2[1] + lane_w_2//2, dash_y), (self.lanes_2[1] + lane_w_2//2, dash_y + 25), 1)
                dash_y += 60
                
            for obs in self.obstacles_2:
                ox = self.lanes_2[obs.lane]
                oy = int(obs.y)
                rx = ox - obs.width // 2
                ry = oy - obs.height // 2
                self.draw_obstacle(canvas_surface, obs, ox, oy, rx, ry, font)
                
            self.draw_vehicle(canvas_surface, self.player_x_2, self.player_y, (255, 0, 0) if self.difficulty == 4 else (255, 0, 255))
            
        # Draw TV static overlay directly on surface in Level 4
        if self.difficulty == 4:
            for _ in range(30):
                sx = random.randint(0, self.width)
                sy = random.randint(0, self.height)
                sw = random.randint(10, 45)
                sh = random.randint(1, 2)
                pygame.draw.rect(canvas_surface, (60, 20, 20), (sx, sy, sw, sh))
                
        surface.blit(canvas_surface, (self.shake_x, self.shake_y))
        
        # HUD Panel
        pygame.draw.rect(surface, (11, 11, 11), (0, 0, self.width, 40))
        hud_border_col = (255, 0, 0) if self.difficulty == 4 else (0, 255, 255)
        pygame.draw.line(surface, hud_border_col, (0, 40), (self.width, 40), 2)
        
        hud_font = pygame.font.SysFont("Courier", 13, bold=True)
        hud_text_col = (255, 0, 0) if self.difficulty == 4 else (0, 255, 255)
        hud_txt = hud_font.render(f"SCORE: {self.score:05d}  HI-SCORE: {self.high_score:05d}  MULTIPLIER: {self.speed_multiplier:.2f}X", True, hud_text_col)
        surface.blit(hud_txt, (15, 12))
        
        # Scanlines overlay
        for y in range(0, self.height, 4):
            pygame.draw.line(surface, (6, 6, 6), (0, y), (self.width, y))
            
        # Overlays
        if self.game_state == "MENU":
            self.draw_overlay_screen(surface, "SHIFTING LANES RACER", "PRESS 'S' TO START VEHICLE CORE", (255, 0, 0) if self.difficulty == 4 else (0, 255, 255))
        elif self.game_state == "GAMEOVER":
            if self.mode == "SINGLE":
                self.draw_overlay_screen(surface, "VEHICLE CORE SHATTERED // GAME OVER", "PRESS 'R' TO RE-CALIBRATE SPEED MULTIPLIER", (255, 0, 0))
            else:
                self.draw_overlay_screen(surface, f"MATCH RESULTS: {self.winner}", "PRESS 'R' TO RE-CALIBRATE BOTH CORES", (255, 0, 0))

    def draw_overlay_screen(self, surface, title_str, prompt_str, color):
        pygame.draw.rect(surface, (0, 0, 0), (40, 120, self.width - 80, 180))
        pygame.draw.rect(surface, color, (40, 120, self.width - 80, 180), 2)
        
        font_lg = pygame.font.SysFont("Courier", 18, bold=True)
        font_sm = pygame.font.SysFont("Courier", 11, bold=True)
        
        t_surf = font_lg.render(title_str, True, color)
        p_surf = font_sm.render(prompt_str, True, (255, 255, 0))
        e_surf = font_sm.render("PRESS 'ESC' TO DISCONNECT MATCH LINK", True, (255, 255, 255))
        
        surface.blit(t_surf, (self.width//2 - t_surf.get_width()//2, 155))
        surface.blit(p_surf, (self.width//2 - p_surf.get_width()//2, 205))
        surface.blit(e_surf, (self.width//2 - e_surf.get_width()//2, 240))
