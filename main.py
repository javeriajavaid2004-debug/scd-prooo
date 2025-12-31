"""Side-scrolling Devil Run homage with responsive UI and toxic progression."""

from __future__ import annotations

import sys
from typing import Dict, Optional, Tuple

import pygame

import config
from database_manager import db_manager
from dialogue_manager import DialogueManager
from level_manager import level_manager 
from auth_manager import AuthManager
import os
import random
import math

# --- DATABASE HELPER MOVED TO CLASS OR KEPT IF UTILITY ---
# Keeping it here as a helper function for now, but could be refactored.


class Particle:
    """Simple circular particle for visual flair."""
    def __init__(self, pos: pygame.Vector2, vel: pygame.Vector2, color: Tuple[int, int, int], life: float) -> None:
        self.pos = pos
        self.vel = vel
        self.color = color
        self.life = life
        self.max_life = life

    def update(self, dt: float) -> bool:
        self.pos += self.vel * dt
        self.life -= dt
        return self.life > 0

    def draw(self, surface: pygame.Surface, camera_x: float) -> None:
        alpha = int((self.life / self.max_life) * 255)
        radius = max(1, int(4 * (self.life / self.max_life)))
        # Pygame 2.x supports alpha in draw.circle with a 4-length tuple
        color_with_alpha = (*self.color, alpha)
        
        # We use a temporary surface for alpha if needed, but for simplicity:
        pygame.draw.circle(surface, self.color, (int(self.pos.x - camera_x), int(self.pos.y)), radius)


class Player:
    """Animated character silhouette with platformer physics."""
    def __init__(self, spawn_point: pygame.Vector2) -> None:
        self.spawn_point = spawn_point.copy()
        # Increased height slightly for the sprite
        self.rect = pygame.Rect(spawn_point.x, spawn_point.y, config.TILE_SIZE, int(config.TILE_SIZE * 1.5))
        self.vel = pygame.Vector2(0, 0)
        self.on_ground = False
        self.coyote_timer = 0.0
        self.jump_buffer_timer = 0.0
        self.facing_right = True
        
        # Animations & Visual Polish
        self.stretch_y = 1.0  # Squash and stretch factor
        self.breath_timer = 0.0
        self.walk_timer = 0.0
        self.is_moving = False
        self.jumps_left = 2 # Allow double jump
        
        # Sprite Loading (Optional - we'll focus on the procedural fallback for "Real Banda")
        self.sprite = self._load_sprite()

    def _load_sprite(self) -> pygame.Surface:
        # Path to the generated artifact
        path = r"C:\Users\dell\.gemini\antigravity\brain\39ef2a92-0a36-42e2-9b10-c22c5414b25b\player_character_v2_png_1766182952157.png"
        if os.path.exists(path):
            try:
                sheet = pygame.image.load(path).convert_alpha()
                # The generated image had 2 views. Let's crop the side view (right half)
                # Sheet is likely square. Side view is roughly the right half.
                w, h = sheet.get_size()
                # Subsurface(x, y, w, h)
                # Assuming the character is in the right half of the image
                side_view = sheet.subsurface((w // 2, 0, w // 2, h))
                return pygame.transform.scale(side_view, (self.rect.width, self.rect.height))
            except Exception as e:
                print(f"Sprite load error: {e}")
        
        # Fallback if sprite missing: Black box
        surf = pygame.Surface((self.rect.width, self.rect.height))
        surf.fill(config.PLAYER_COLOR)
        return surf

    def reset(self) -> None:
        self.rect.topleft = (self.spawn_point.x, self.spawn_point.y)
        self.vel.xy = (0, 0)
        self.on_ground = False
        self.coyote_timer = 0.0
        self.jump_buffer_timer = 0.0
        self.jumps_left = 2

    def set_spawn(self, spawn_point: pygame.Vector2) -> None:
        self.spawn_point = spawn_point.copy()
        self.last_victory_stars = 0
        self.last_victory_level = ""
        self.reset()

    def handle_input(self, keys: pygame.key.ScancodeWrapper) -> None:
        self.vel.x = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.vel.x = -config.PLAYER_SPEED
            self.facing_right = False
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.vel.x = config.PLAYER_SPEED
            self.facing_right = True

    def jump(self) -> None:
        self.jump_buffer_timer = config.JUMP_BUFFER_TIME

    def update(self, dt: float, platforms: list[pygame.Rect], level_length: int) -> None:
        was_on_ground = self.on_ground
        self.jump_buffer_timer = max(0.0, self.jump_buffer_timer - dt)
        self.coyote_timer = max(0.0, self.coyote_timer - dt)

        self.vel.y += config.GRAVITY
        self.vel.y = min(self.vel.y, config.MAX_FALL_SPEED)

        self.rect.x += int(self.vel.x)
        self._resolve_collisions(axis="x", platforms=platforms)
        self.rect.x = max(0, min(self.rect.x, level_length - self.rect.width))

        self.rect.y += int(self.vel.y)
        self.on_ground = False
        self._resolve_collisions(axis="y", platforms=platforms)
        
        # Coyote Time Logic: Gives a small buffer time after leaving the ground
        if self.on_ground:
            self.jumps_left = 2
            self.coyote_timer = config.COYOTE_TIME
        elif was_on_ground:
             self.coyote_timer = config.COYOTE_TIME

        return self._consume_buffered_jump()

    def _consume_buffered_jump(self) -> bool:
        # 1. Ground/Coyote Jump
        can_jump = self.on_ground or self.coyote_timer > 0
        
        if self.jump_buffer_timer > 0:
            if can_jump:
                self.vel.y = config.JUMP_FORCE
                self.on_ground = False
                self.jump_buffer_timer = 0.0
                self.coyote_timer = 0.0
                self.jumps_left = 1 
                return True
            elif self.jumps_left > 0: # Air jump
                self.vel.y = config.JUMP_FORCE * 0.85
                self.jump_buffer_timer = 0.0
                self.jumps_left -= 1
                return True
        return False

    def _resolve_collisions(self, *, axis: str, platforms: list[pygame.Rect]) -> None:
        for plat in platforms:
            if self.rect.colliderect(plat):
                if axis == "x":
                    if self.vel.x > 0:
                        self.rect.right = plat.left
                    elif self.vel.x < 0:
                        self.rect.left = plat.right
                    self.vel.x = 0
                else:
                    if self.vel.y > 0:
                        self.rect.bottom = plat.top
                        self.vel.y = 0
                        self.on_ground = True
                    elif self.vel.y < 0:
                        self.rect.top = plat.bottom
                        self.vel.y = 0

    def draw(self, surface: pygame.Surface, camera_x: float) -> None:
        # --- ADVANCED PROCEDURAL HUMANOID (Real Banda Feel) ---
        # We draw this instead of the sprite to give the user exactly what they asked for logic-wise
        x, y = self.rect.x - camera_x, self.rect.y
        w, h = self.rect.width, self.rect.height
        
        # Calculate squashed/stretched dimensions
        draw_h = int(h * self.stretch_y)
        draw_w = int(w * (2.0 - self.stretch_y)) # Conserve volume (wider when shorter)
        draw_x = x + (w - draw_w) // 2
        draw_y = y + (h - draw_h)
        
        # Body Colors
        skin_color = (255, 218, 185) # Peach
        clothes_color = (40, 40, 50)  # Dark Blueish Grey
        shoe_color = (20, 20, 20)
        
        # Breathing effect
        breathe = math.sin(self.breath_timer) * 2
        
        # 1. Legs & Shoes
        leg_anim = math.sin(self.walk_timer) * 12 if self.is_moving else 0
        leg_y_start = draw_y + int(draw_h * 0.7)
        # Left Leg
        pygame.draw.line(surface, clothes_color, (draw_x + draw_w//4, leg_y_start), (draw_x + draw_w//4 + leg_anim, draw_y + draw_h), 6)
        pygame.draw.rect(surface, shoe_color, (draw_x + draw_w//4 + leg_anim - 4, draw_y + draw_h - 4, 10, 6))
        # Right Leg
        pygame.draw.line(surface, clothes_color, (draw_x + 3*draw_w//4, leg_y_start), (draw_x + 3*draw_w//4 - leg_anim, draw_y + draw_h), 6)
        pygame.draw.rect(surface, shoe_color, (draw_x + 3*draw_w//4 - leg_anim - 4, draw_y + draw_h - 4, 10, 6))

        # 2. Torso (Jacket/Shirt)
        torso_rect = pygame.Rect(draw_x + draw_w//4, draw_y + draw_h//3 + int(breathe), draw_w//2, draw_h//2)
        pygame.draw.rect(surface, clothes_color, torso_rect, border_radius=5)
        
        # 3. Head
        head_radius = int(draw_w * 0.4)
        head_center = (draw_x + draw_w//2, draw_y + draw_h//5 + int(breathe))
        pygame.draw.circle(surface, skin_color, head_center, head_radius)
        
        # 4. Eyes (Directional)
        eye_offset = 6 if self.facing_right else -6
        pygame.draw.circle(surface, (255, 255, 255), (head_center[0] + eye_offset, head_center[1] - 2), 3)
        pygame.draw.circle(surface, (0, 0, 0), (head_center[0] + eye_offset + (1 if self.facing_right else -1), head_center[1] - 2), 1)

        # 5. Arms
        arm_anim = -math.sin(self.walk_timer) * 10 if self.is_moving else (math.sin(self.breath_timer) * 2)
        # Back Arm
        pygame.draw.line(surface, clothes_color, (draw_x + draw_w//2, draw_y + draw_h//3 + 5), (draw_x + draw_w//2 + 15 + arm_anim if self.facing_right else draw_x + draw_w//2 - 15 - arm_anim, draw_y + draw_h//2 + 5), 4)


class Game:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Devil Run: The Journey")
        
        flags = pygame.FULLSCREEN if config.DEFAULT_FULLSCREEN else 0
        self.screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), flags)
        self.is_fullscreen = config.DEFAULT_FULLSCREEN
        
        self.clock = pygame.time.Clock()
        self.delta = 0.0

        self.state = "LOGIN" 
        self.current_user: Optional[Dict] = None

        self.level_manager = level_manager
        self.level_manager.load_level()
        self.player = Player(self.level_manager.spawn_point)
        self.dialogue = DialogueManager(self.screen.get_size())
        
        self.auth_manager = AuthManager(self.screen) 

        # Fonts
        self.title_font = pygame.font.Font(config.FONT_NAME, config.TITLE_FONT_SIZE)
        self.hud_font = pygame.font.Font(config.FONT_NAME, config.HUD_FONT_SIZE)
        self.map_font = pygame.font.Font(config.FONT_NAME, 24) 

        self.message_text = ""
        self.message_expires = 0
        self.camera_x = 0.0
        self.map_progress: Dict[int, int] = {} 
        self.particles: List[Particle] = []
        
        # Audio Initialization
        self.jump_sound = self._gen_sound("jump")
        self.death_sound = self._gen_sound("death")
        self._start_music()

        try:
            db_manager.connect()
        except RuntimeError:
            self.set_flash_message("DB Error: Cannot connect. Check config.py.", 5000)

    # ------------------------------------------------------------------
    # UI/Status Helpers
    # ------------------------------------------------------------------
    def set_flash_message(self, text: str, duration_ms: int = 2500) -> None:
        self.message_text = text
        self.message_expires = pygame.time.get_ticks() + duration_ms

    def _gen_sound(self, kind: str) -> Optional[pygame.mixer.Sound]:
        """Generates procedural sound effects."""
        try:
            import array
            duration = 0.15 if kind == "jump" else 0.5
            freq_start = 300 if kind == "jump" else 800
            freq_end = 800 if kind == "jump" else 100
            
            n_samples = int(duration * 22050)
            samples = array.array('h', [0] * n_samples)
            for i in range(n_samples):
                t = i / n_samples
                freq = freq_start + (freq_end - freq_start) * t
                env = (1.0 - t)**2 if kind == "death" else (1.0 - t)**0.5
                vol = 24000 * env
                samples[i] = int(vol * math.sin(2.0 * math.pi * freq * i / 22050))
            return pygame.mixer.Sound(samples)
        except Exception:
            return None

    def _start_music(self) -> None:
        """Starts procedural background music."""
        try:
            import array
            # Generate 2 seconds of atmospheric drone
            duration = 4.0
            sr = 22050
            n_samples = int(duration * sr)
            samples = array.array('h', [0] * n_samples)
            
            for i in range(n_samples):
                t = i / n_samples
                # Layer multiple low frequencies for a "drone" feel
                s = 0.4 * math.sin(2 * math.pi * 55 * t) # Low A
                s += 0.3 * math.sin(2 * math.pi * 110 * t) # A bit higher
                s += 0.2 * math.sin(2 * math.pi * 82.4 * t) # E note
                s *= (0.8 + 0.2 * math.sin(2 * math.pi * 0.5 * t)) # LFO Volume modulation
                
                samples[i] = int(s * 14000)
            
            music_sound = pygame.mixer.Sound(samples)
            music_sound.play(-1) # Loop forever
        except Exception:
            pass

    def spawn_particles(self, pos: pygame.Vector2, count: int, color: Tuple[int, int, int]) -> None:
        for _ in range(count):
            vel = pygame.Vector2(random.uniform(-100, 100), random.uniform(-200, 50))
            self.particles.append(Particle(pos.copy(), vel, color, random.uniform(0.5, 1.2)))

    def toggle_fullscreen(self) -> None:
        self.is_fullscreen = not self.is_fullscreen
        flags = pygame.FULLSCREEN if self.is_fullscreen else 0
        res = (0, 0) if self.is_fullscreen else (config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
        self.screen = pygame.display.set_mode(res, flags)
        
        self.dialogue.screen_width = self.screen.get_width()
        self.dialogue.screen_height = self.screen.get_height()

    def get_player_rank(self) -> Tuple[str, Tuple[int, int, int]]:
        if not self.current_user:
            return "Unranked", config.PEACH_DARK

        total_stars = self.current_user.get('total_stars', 0)
        best_rank = config.RANKS[0]
        for star_threshold, rank_name in config.RANKS:
            if total_stars >= star_threshold:
                # FIX: Rank color should be ACCENT_YELLOW/RED not PEACH_DARK
                best_rank = (rank_name, config.ACCENT_YELLOW) if star_threshold >= 15 else (rank_name, config.PEACH_MED)
            else:
                break
        return best_rank

    def _get_map_node_position(self, i: int) -> Tuple[int, int]:
        """Calculates responsive, centered, diagonal zigzag positions."""
        w, h = self.screen.get_size()
        margin_x = w * 0.1
        available_w = w - (2 * margin_x)
        total_nodes = config.TOTAL_LEVELS + 1 
        x_step = available_w / total_nodes
        x = margin_x + (i - 1) * x_step
        
        center_y = (h / 2) + 20
        amplitude = h * 0.15 
        
        if i % 2 == 0:
            y = center_y + amplitude
        else:
            y = center_y - amplitude
            
        if i == config.TOTAL_LEVELS + 1: 
            x += x_step * 0.5 
            y = center_y
            
        return int(x), int(y)

    # ------------------------------------------------------------------
    # Game Logic & Transitions
    # ------------------------------------------------------------------
    def handle_death(self, reason_position: pygame.Vector2) -> None:
        self.level_manager.increment_attempts()
        self.level_manager.log_death(reason_position)
        
        # Explosion of red particles
        self.spawn_particles(reason_position, 15, config.ACCENT_RED)
        
        if self.death_sound:
            self.death_sound.play()
        
        if self.level_manager.current_attempts > 20: # Increased limit
            self.state = "DEATH_MENU"
            self.dialogue.trigger(12) 
        else:
            # TRIGGER DIALOGUE EVERY TIME for 'voice' feel as requested
            self.dialogue.trigger(self.level_manager.current_attempts)
            self.state = "DIALOGUE" 

    def handle_victory(self) -> None:
        """CRITICAL FIX: Updates map progress immediately after victory."""
        stars = self.level_manager.calculate_star_rating()
        
        if self.current_user:
            try:
                # 1. Record attempt (db_manager handles delta calculation now)
                db_manager.record_level_attempt(
                    self.current_user["id"],
                    self.level_manager.level_id,
                    self.level_manager.current_attempts,
                    stars,
                )
                
                # 2. FIX: Refresh map progress immediately from DB
                self.map_progress = db_manager.get_player_level_stars(self.current_user['id'])
                
                # 3. Recalculate total stars for current user display
                self.current_user['total_stars'] = sum(self.map_progress.values())
                
            except RuntimeError as exc:
                self.set_flash_message(f"Save Error: {exc}", 4000)
        
        self.last_victory_level = self.level_manager.level_name
        self.last_victory_stars = stars
        self.state = "VICTORY" 

    # ------------------------------------------------------------------
    # Event Handling
    # ------------------------------------------------------------------
    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                self.toggle_fullscreen()

            if self.state in {"LOGIN", "SIGNUP"}:
                self._handle_auth_event(event)
            elif self.state == "PLAYING":
                self._handle_play_event(event)
            elif self.state == "DIALOGUE":
                if not self.dialogue.is_locked and event.type == pygame.KEYDOWN:
                    self.dialogue.end_dialogue()
                    self.player.reset()
                    self.camera_x = 0
                    self.state = "PLAYING" 
            elif self.state == "DEATH_MENU":
                self._handle_death_menu_event(event)
            elif self.state == "MAP_MENU":
                self._handle_map_menu_event(event)
            elif self.state == "VICTORY":
                self._handle_victory_event(event)


    def _handle_auth_event(self, event: pygame.event.Event) -> None:
        auth_result = self.auth_manager.handle_event(event)
        
        if auth_result and auth_result.get("success"):
            self.current_user = auth_result["user"]
            try:
                self.map_progress = db_manager.get_player_level_stars(self.current_user['id'])
                self.current_user['total_stars'] = sum(self.map_progress.values())
            except RuntimeError:
                pass
            self.state = "MAP_MENU" 
            self.set_flash_message(auth_result.get("message", "Welcome."), 4000)
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
             pass

    def _handle_play_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                self.player.jump()
                # Jump dust (we still spawn dust on trigger even if buffer fails)
                self.spawn_particles(pygame.Vector2(self.player.rect.centerx, self.player.rect.bottom), 5, (200, 200, 200))
            elif event.key == pygame.K_ESCAPE:
                self.state = "MAP_MENU"

    def _handle_victory_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN:
            w, h = self.screen.get_size()
            
            # Continue Button
            cont_rect = pygame.Rect(w // 2 - 100, h // 2 + 50, 200, 50)
            if cont_rect.collidepoint(event.pos):
                self.level_manager.reset_attempts()
                self.player.set_spawn(self.level_manager.spawn_point)
                self.camera_x = 0
                self.state = "MAP_MENU"
            
            # Replay Button
            replay_rect = pygame.Rect(w // 2 - 100, h // 2 + 120, 200, 50)
            if replay_rect.collidepoint(event.pos):
                self.level_manager.reset_attempts()
                self.player.set_spawn(self.level_manager.spawn_point)
                self.camera_x = 0
                self.state = "PLAYING"

    def _handle_death_menu_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN:
            w = self.screen.get_width()
            
            # Retry Button (New)
            retry_rect = pygame.Rect(w // 2 - 60, 200, 120, 50)
            if retry_rect.collidepoint(event.pos):
                self.player.reset()
                self.camera_x = 0
                self.state = "PLAYING"
            
            # Menu Button
            btn_rect = pygame.Rect(w - 150, 20, 120, 50)
            if btn_rect.collidepoint(event.pos):
                self.player.reset()
                self.state = "MAP_MENU"
            
    def _handle_map_menu_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN:
            w = self.screen.get_width()
            
            # 1. Check Quit Button
            quit_rect = pygame.Rect(w - 150, 80, 120, 50)
            if quit_rect.collidepoint(event.pos):
                pygame.quit()
                sys.exit()

            # 2. Check Delete Account Button
            del_rect = pygame.Rect(w//2 - 100, self.screen.get_height() - 60, 200, 40)
            if del_rect.collidepoint(event.pos):
                if self.current_user:
                    db_manager.delete_user(self.current_user['id'])
                    self.current_user = None
                    self.state = "LOGIN"
                    self.auth_manager.auth_error = "Account Deleted."
                    return

            # 3. Check Level Nodes
            for i in range(1, config.TOTAL_LEVELS + 2): 
                x, y = self._get_map_node_position(i)
                node_hitbox = pygame.Rect(0, 0, 70, 70)
                node_hitbox.center = (x, y)

                if node_hitbox.collidepoint(event.pos):
                    if self._is_level_unlocked(i):
                        self.level_manager.load_level(index=i-1)
                        self.player.set_spawn(self.level_manager.spawn_point)
                        self.camera_x = 0
                        self.level_manager.reset_attempts()
                        self.state = "PLAYING"
                        self.set_flash_message(f"Entering {self.level_manager.level_name}...", 1500)
                        return
                    else:
                        req_stars = config.BOSS_UNLOCK_STARS if i == config.TOTAL_LEVELS + 1 else "previous level"
                        msg = f"LOCKED! Need {req_stars}." if isinstance(req_stars, int) else "Locked! Finish previous."
                        self.set_flash_message(msg, 1000)

    def _is_level_unlocked(self, level_num: int) -> bool:
        if level_num == 1:
            return True
        if level_num <= config.TOTAL_LEVELS:
            # FIX: Checks if the ID of the *previous* level is in the map_progress keys
            return (level_num - 1) in self.map_progress
        if level_num == config.TOTAL_LEVELS + 1: # Boss
            return self.current_user.get('total_stars', 0) >= config.BOSS_UNLOCK_STARS
        return False


    # ------------------------------------------------------------------
    # Update loop
    # ------------------------------------------------------------------
    def update(self) -> None:
        if self.state == "PLAYING":
            self._update_play()
        elif self.state == "DIALOGUE" or self.state == "DEATH_MENU" or self.state == "VICTORY":
            self.dialogue.update(self.delta)
        
        # Always update particles if any exist
        self.particles = [p for p in self.particles if p.update(self.delta)]

    def _update_play(self) -> None:
        keys = pygame.key.get_pressed()
        self.player.handle_input(keys)
        # Play jump sound if player.update returns True (meaning a jump just started)
        if self.player.update(
            self.delta,
            self.level_manager.platforms,
            self.level_manager.level_length,
        ):
            if self.jump_sound:
                self.jump_sound.play()
        self.level_manager.update_hazards(self.delta, self.player.rect)

        if self.player.rect.top > config.SCREEN_HEIGHT + 200 or \
           self.level_manager.check_hazard_collision(self.player.rect):
            self.handle_death(pygame.Vector2(self.player.rect.center))
            return
            
        # Detection buffer (25px) to ensure victory triggers even on edge-touches
        if self.level_manager.goal_rect and self.player.rect.colliderect(self.level_manager.goal_rect.inflate(25, 25)):
            self.handle_victory()
            return
        self._update_camera()

    def _update_camera(self) -> None:
        target = self.player.rect.centerx - self.screen.get_width() * 0.35
        max_scroll = max(0, self.level_manager.level_length - self.screen.get_width())
        self.camera_x += (target - self.camera_x) * 0.12
        self.camera_x = max(0, min(self.camera_x, max_scroll))

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------
    def draw(self) -> None:
        if self.state in {"LOGIN", "SIGNUP"}:
            self.auth_manager.draw()
        elif self.state == "MAP_MENU":
            self._draw_map_menu()
        elif self.state == "DEATH_MENU":
            self._draw_death_menu()
        elif self.state == "VICTORY":
            self._draw_level() # Keep background
            self._draw_victory()
        else: # PLAYING or DIALOGUE
            self._draw_level()
            if self.state == "DIALOGUE":
                self.dialogue.draw(self.screen)
        
        # Flash Message Drawing (Global, centered at the top)
        if self.message_text and pygame.time.get_ticks() < self.message_expires:
            msg = self.hud_font.render(self.message_text, True, config.ACCENT_RED)
            msg_rect = msg.get_rect(center=(self.screen.get_width() // 2, 40))
            self.screen.blit(msg, msg_rect)
        pygame.display.flip()

    def _draw_level(self) -> None:
        # Draw sky gradient (Red theme)
        self.screen.fill(config.BACKGROUND_COLOR)
        w = self.screen.get_width()
        
        # 0. Draw Decorations (Ghas and Pathar)
        for dec in self.level_manager.decorations:
            pos = (dec['pos'].x - self.camera_x, dec['pos'].y)
            if dec['type'] == 'grass':
                # Draw small stalks
                pygame.draw.line(self.screen, dec['color'], pos, (pos[0], pos[1] - dec['size']), 2)
                pygame.draw.line(self.screen, dec['color'], pos, (pos[0]-3, pos[1] - dec['size']+2), 2)
            elif dec['type'] == 'stone':
                # Draw stone circles
                pygame.draw.circle(self.screen, dec['color'], (int(pos[0]), int(pos[1])), dec['size'])
            else: # tree
                # 1. Trunk (Tapered)
                trunk_w = max(4, dec['size'] // 10)
                trunk_h = dec['size']
                trunk_color = (60, 30, 20) # Brown
                pygame.draw.polygon(self.screen, trunk_color, [
                    (pos[0] - trunk_w, pos[1]),
                    (pos[0] + trunk_w, pos[1]),
                    (pos[0] + trunk_w//2, pos[1] - trunk_h),
                    (pos[0] - trunk_w//2, pos[1] - trunk_h)
                ])
                # 2. Branches (Small hints)
                pygame.draw.line(self.screen, trunk_color, (pos[0], pos[1] - trunk_h//2), (pos[0] + 10, pos[1] - trunk_h//2 - 10), 2)
                pygame.draw.line(self.screen, trunk_color, (pos[0], pos[1] - 2*trunk_h//3), (pos[0] - 10, pos[1] - 2*trunk_h//3 - 5), 2)
                # 3. Canopy (Layered for 'real' look)
                leaf_color = dec['color']
                leaf_radius = dec['size'] // 3
                # Draw 3-4 overlapping circles for volume
                pygame.draw.circle(self.screen, leaf_color, (int(pos[0]), int(pos[1] - trunk_h)), leaf_radius)
                pygame.draw.circle(self.screen, (leaf_color[0]//2, leaf_color[1]//2, leaf_color[2]//2), (int(pos[0] - 8, ), int(pos[1] - trunk_h - 5)), leaf_radius - 2)
                pygame.draw.circle(self.screen, leaf_color, (int(pos[0] + 8), int(pos[1] - trunk_h - 5)), leaf_radius - 2)

        pygame.draw.rect(self.screen, config.PEACH_MED, (0, 0, w, 70))
        title = self.title_font.render(self.level_manager.level_name, True, config.ACCENT_WHITE)
        self.screen.blit(title, title.get_rect(center=(w // 2, 40)))

        # Draw World
        for platform in self.level_manager.platforms:
            screen_rect = platform.move(-self.camera_x, 0)
            pygame.draw.rect(self.screen, config.PLATFORM_COLOR, screen_rect)
        for trap in self.level_manager.static_traps:
            screen_rect = trap.move(-self.camera_x, 0)
            pygame.draw.rect(self.screen, config.TRAP_COLOR, screen_rect)

        for osc in self.level_manager.oscillators: osc.draw(self.screen, self.camera_x)
        for trig in self.level_manager.trigger_spikes: trig.draw(self.screen, self.camera_x)
        for axe in self.level_manager.swing_axes: axe.draw(self.screen, self.camera_x)
        for crush in self.level_manager.crushing_hazards: crush.draw(self.screen, self.camera_x)

        if self.level_manager.goal_rect:
            goal_rect = self.level_manager.goal_rect.move(-self.camera_x, 0)
            pygame.draw.rect(self.screen, config.GOAL_COLOR, goal_rect, border_radius=6)

        for chaser in self.level_manager.chasers: chaser.draw(self.screen, self.camera_x)

        self.player.draw(self.screen, self.camera_x)
        
        for p in self.particles:
            p.draw(self.screen, self.camera_x)
            
        self._draw_hud()

    def _draw_victory(self) -> None:
        # Draw semi-transparent overlay
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        w, h = self.screen.get_size()
        
        # 1. Title
        title = self.title_font.render("LEVEL COMPLETE!", True, config.GOAL_GREEN)
        self.screen.blit(title, title.get_rect(center=(w // 2, h // 2 - 120)))
        
        # 2. Level Name
        lvl_text = self.hud_font.render(self.last_victory_level, True, config.ACCENT_WHITE)
        self.screen.blit(lvl_text, lvl_text.get_rect(center=(w // 2, h // 2 - 60)))
        
        # 3. Stars
        star_str = "★" * self.last_victory_stars + "☆" * (3 - self.last_victory_stars)
        star_text = self.title_font.render(star_str, True, config.ACCENT_YELLOW)
        self.screen.blit(star_text, star_text.get_rect(center=(w // 2, h // 2)))
        
        # 4. Buttons
        # Continue
        cont_rect = pygame.Rect(w // 2 - 100, h // 2 + 50, 200, 50)
        pygame.draw.rect(self.screen, config.GOAL_GREEN, cont_rect, border_radius=8)
        c_label = self.hud_font.render("CONTINUE", True, config.INK)
        self.screen.blit(c_label, c_label.get_rect(center=cont_rect.center))
        
        # Replay
        replay_rect = pygame.Rect(w // 2 - 100, h // 2 + 120, 200, 50)
        pygame.draw.rect(self.screen, (100, 100, 100), replay_rect, border_radius=8)
        r_label = self.hud_font.render("REPLAY", True, config.WHITE)
        self.screen.blit(r_label, r_label.get_rect(center=replay_rect.center))

    def _draw_hud(self) -> None:
        h = self.screen.get_height()
        attempts = self.hud_font.render(
            f"tries {self.level_manager.current_attempts}", True, config.HUD_TEXT_COLOR
        )
        self.screen.blit(attempts, (20, h - 60))
        if self.current_user:
            runner = self.hud_font.render(
                f"runner: {self.current_user['username']}", True, config.HUD_TEXT_COLOR
            )
            self.screen.blit(runner, (20, h - 90))

    def _draw_death_menu(self) -> None:
        self.dialogue.draw(self.screen)
        w, h = self.screen.get_size()
        
        # Menu Button
        btn_rect = pygame.Rect(w - 150, 20, 120, 50)
        pygame.draw.rect(self.screen, config.UI_BUTTON_BG, btn_rect, border_radius=6)
        label = self.hud_font.render("Menu", True, config.UI_BUTTON_TEXT)
        self.screen.blit(label, label.get_rect(center=btn_rect.center))
        
        # Retry Button (Center)
        retry_rect = pygame.Rect(w // 2 - 60, 200, 120, 50)
        pygame.draw.rect(self.screen, config.GOAL_GREEN, retry_rect, border_radius=6)
        r_label = self.hud_font.render("Retry", True, config.INK)
        self.screen.blit(r_label, r_label.get_rect(center=retry_rect.center))

        reason = self.title_font.render("YOU FAILED. AGAIN.", True, config.ACCENT_RED)
        self.screen.blit(reason, reason.get_rect(center=(w // 2, 100)))

    def _draw_map_menu(self) -> None:
        self.screen.fill(config.BACKGROUND_COLOR)
        w, h = self.screen.get_size()
        
        # --- HEADER (Professional Status Bar) ---
        header_h = 140
        pygame.draw.rect(self.screen, config.PEACH_DARK, (0, 0, w, header_h))
        
        rank_name, rank_color = self.get_player_rank()
        total_stars = self.current_user.get('total_stars', 0)

        # 1. Rank & Info
        rank_text = self.title_font.render(rank_name, True, rank_color)
        user_text = self.hud_font.render(f"Runner: {self.current_user['username']}", True, config.ACCENT_WHITE)
        self.screen.blit(rank_text, (40, 30))
        self.screen.blit(user_text, (40, 85))

        # 2. Total Stars
        star_text = self.title_font.render(f"Total Stars: {total_stars}", True, config.ACCENT_YELLOW)
        star_rect = star_text.get_rect(topright=(w - 40, 30))
        self.screen.blit(star_text, star_rect)
        
        # 3. Quit Button
        quit_rect = pygame.Rect(w - 150, 80, 120, 50)
        pygame.draw.rect(self.screen, config.UI_BUTTON_BG, quit_rect, border_radius=6)
        label = self.hud_font.render("Quit", True, config.UI_BUTTON_TEXT)
        self.screen.blit(label, label.get_rect(center=quit_rect.center))

        # 4. Delete Account Button
        del_rect = pygame.Rect(w//2 - 100, h - 60, 200, 40)
        pygame.draw.rect(self.screen, (80, 80, 80), del_rect, border_radius=6)
        t_del = self.hud_font.render("Delete Account", True, config.WHITE)
        self.screen.blit(t_del, t_del.get_rect(center=del_rect.center))

        # --- DRAW CONNECTING LINES FIRST ---
        last_pos = None
        for i in range(1, config.TOTAL_LEVELS + 2):
            x, y = self._get_map_node_position(i)
            current_pos = (x, y)
            is_unlocked = self._is_level_unlocked(i)
            
            if last_pos:
                line_color = config.ACCENT_RED if is_unlocked else config.INK
                pygame.draw.line(self.screen, line_color, last_pos, current_pos, 4)
            last_pos = current_pos

        # --- DRAW NODES ON TOP ---
        for i in range(1, config.TOTAL_LEVELS + 2): 
            x, y = self._get_map_node_position(i)
            is_boss = (i == config.TOTAL_LEVELS + 1)
            is_unlocked = self._is_level_unlocked(i)
            
            # Node Visuals
            node_color = config.ACCENT_RED if is_boss else config.PEACH_DARK
            if not is_unlocked: node_color = config.INK
            
            border_color = config.ACCENT_YELLOW if is_unlocked else config.PEACH_MED
            if is_boss and is_unlocked: border_color = config.ACCENT_RED
            
            # Draw Monster Gate (Boss) or Normal Gate
            radius = 35 if is_boss else 28
            pygame.draw.circle(self.screen, node_color, (x, y), radius)
            pygame.draw.circle(self.screen, border_color, (x, y), radius + 4, 4)
            
            # Labels
            label_text = "BOSS" if is_boss else str(i)
            label = self.map_font.render(label_text, True, config.ACCENT_WHITE)
            label_rect = label.get_rect(center=(x, y))
            self.screen.blit(label, label_rect)

            # Stars (if unlocked/played)
            if i in self.map_progress:
                stars = self.map_progress[i]
                if stars > 0:
                    star_symbol = "★" * stars
                    star_text = self.hud_font.render(star_symbol, True, config.ACCENT_YELLOW)
                    self.screen.blit(star_text, star_text.get_rect(center=(x, y + 45)))

            # Lock visual (Red X)
            if not is_unlocked:
                pygame.draw.line(self.screen, config.ACCENT_RED, (x - 15, y - 15), (x + 15, y + 15), 4)
                pygame.draw.line(self.screen, config.ACCENT_RED, (x + 15, y - 15), (x - 15, y + 15), 4)


def main() -> None:
    game = Game()
    while True:
        game.delta = game.clock.tick(config.FPS) / 1000.0
        game.handle_events()
        game.update()
        game.draw()


if __name__ == "__main__":
    main()