"""Handles in-game toxic dialogue overlays."""

from __future__ import annotations

import random
import os
from typing import Dict, List, Optional
import pygame

import config


class DialogueManager:
    """Controls the escalating toxic narrator feedback."""

    # Tiers of insults based on attempt count
    TOXIC_TIERS: Dict[int, Dict[str, List[str]]] = {
        1: { 
            "range": range(1, 4), 
            "phrases": [
                "Did you forget how to jump? 🤡",
                "Tutorial is that way -> 👶",
                "Gravity check: Passed ✅. Skill check: Failed ❌.",
                "My grandma plays faster than this. 👵",
                "Wow. Just... wow. 😐",
            ]
        },
        2: { 
            "range": range(4, 7), 
            "phrases": [
                "Are you playing with your feet? 🦶",
                "Maybe try a different game? Like Sudoku? 📉",
                "I'm embarrassed for you. 🫣",
                "Lag? No, that was just you. 😂",
                "You're actually trying, aren't you? 🥺",
            ]
        },
        3: { 
            "range": range(7, 11), 
            "phrases": [
                "Just ALT+F4 already. Save your dignity. 🗑️",
                "I've seen AI play better, and I AM AI. 🤖",
                "You are the reason shampoo has instructions. 🧼",
                "Is your monitor even on? 📺",
                "This is painful to watch. 💀",
            ]
        },
        4: { 
            "range": range(11, 10000), 
            "phrases": [
                "Error 404: Skill not found. 🚫",
                "Go touch grass. Seriously. 🌱",
                "I'm going to sleep. Wake me when you get good. 😴",
                "Delete the game. Do it. 🚮",
                "You have reached peak failure. 📉",
            ]
        },
    }

    def _generate_toxic_sound(self) -> Optional[pygame.mixer.Sound]:
        """Generates a bolder, glitchier toxic voice blip."""
        try:
            import array
            duration = 0.06
            n_samples = int(duration * 22050)
            samples = array.array('h', [0] * n_samples)
            for i in range(n_samples):
                t = i / n_samples
                # FM Synthesis-like glitch: Sine wave with frequency modulation
                freq = 140 + 60 * math.sin(2 * math.pi * 40 * t)
                # Envelope: sharp start, quick decay
                env = 28000 * (1.0 - t)**0.5
                samples[i] = int(env * math.sin(2.0 * math.pi * freq * i / 22050))
            return pygame.mixer.Sound(samples)
        except Exception:
            return None # Fallback if audio fails

    def __init__(self, surface_size: tuple[int, int]) -> None:
        self.screen_width, self.screen_height = surface_size
        
        # FIX: Reduced Font Size for better text fitting
        self.font = pygame.font.Font(config.FONT_NAME, 30) 
        
        self.active = False
        self.locked = False
        self.end_time = 0
        self.current_phrase = ""
        self.current_tier = 1
        
        self.face_surface = self._build_face_surface()
        self.img = self._load_img()
        self.sound = self._generate_toxic_sound()
        
        # Typing Effect State
        self.displayed_text = ""
        self.displayed_hint = ""
        self.text_timer = 0.0
        self.char_index = 0
        self.hint_index = 0
        self.typing_speed = 0.04 # Seconds per character
        self.hint_text = "Press Any Key to Retry (If you dare)"

    def _build_face_surface(self) -> pygame.Surface:
        """Draws the pixel-art style face for the center of the screen."""
        face = pygame.Surface((220, 220), pygame.SRCALPHA)
        face.fill((0, 0, 0, 0))
        
        pygame.draw.rect(face, config.RED, (10, 10, 200, 200), border_radius=16)
        pygame.draw.circle(face, config.YELLOW, (80, 90), 25)
        pygame.draw.circle(face, config.YELLOW, (140, 90), 25)
        pygame.draw.circle(face, config.BLACK, (80, 90), 10)
        pygame.draw.circle(face, config.BLACK, (140, 90), 10)
        
        pygame.draw.rect(face, config.BLACK, (60, 150, 100, 20))
        return face

    def _load_img(self) -> pygame.Surface:
        """Loads the monster image or creates a fallback to prevent crashes."""
        path = "talha_project 2/assets/monsters/monster_frame_0.png"
        
        if os.path.exists(path):
            try:
                raw_img = pygame.image.load(path).convert_alpha()
                return pygame.transform.scale(raw_img, (200, 200))
            except pygame.error:
                print(f"Warning: Could not load {path}, using fallback.")
        
        # Fallback: Draw a red circle if file is missing
        s = pygame.Surface((200, 200), pygame.SRCALPHA)
        pygame.draw.circle(s, config.RED, (100, 100), 80)
        return s

    def _determine_tier(self, attempts: int) -> int:
        for tier, data in self.TOXIC_TIERS.items():
            if attempts in data["range"]:
                return tier
        return config.MAX_TOXICITY_TIER

    def trigger(self, attempts: int) -> None:
        """Activates the dialogue screen."""
        self.current_tier = self._determine_tier(attempts)
        phrases = self.TOXIC_TIERS.get(self.current_tier, {}).get("phrases", [])
        self.current_phrase = random.choice(phrases) if phrases else "..."
        
        self.active = True
        self.locked = True # Lock input
        self.end_time = pygame.time.get_ticks() + config.DIALOGUE_DISPLAY_MS
        
        # Reset typing effect
        self.displayed_text = ""
        self.displayed_hint = ""
        self.char_index = 0
        self.hint_index = 0
        self.text_timer = 0
        
        if self.sound:
            self.sound.play()

    def update(self, dt: float) -> None:
        """Updates the lock timer and typing effect."""
        if self.locked and pygame.time.get_ticks() >= self.end_time:
            self.locked = False
            
        if self.active:
            self.text_timer += dt
            if self.char_index < len(self.current_phrase) and self.text_timer >= self.typing_speed:
                char = self.current_phrase[self.char_index]
                self.displayed_text += char
                self.char_index += 1
                self.text_timer = 0
                if char != " " and self.sound: self.sound.play()
            
            # Start typing hint only after main text is DONE and locked is FALSE
            elif not self.locked and self.hint_index < len(self.hint_text) and self.text_timer >= self.typing_speed:
                char = self.hint_text[self.hint_index]
                self.displayed_hint += char
                self.hint_index += 1
                self.text_timer = 0
                if char != " " and self.sound: self.sound.play()

    def end_dialogue(self) -> None:
        """Closes the dialogue window."""
        self.active = False
        self.locked = False

    def draw(self, surface: pygame.Surface) -> None:
        """Renders the overlay, monster, face, and text."""
        if not self.active: 
            return
        
        # 1. Darken the background
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        # 2. Draw Monster Image (Top Right)
        surface.blit(self.img, (self.screen_width - 220, 20))
        
        # 3. Draw Center Face
        # FIX: Move face slightly down for a better vertical center visualization
        face_pos = (
            (self.screen_width // 2) - 110, 
            (self.screen_height // 2) - 130 # Adjusted Y position
        )
        surface.blit(self.face_surface, face_pos)
        
        # 4. Draw Toxic Text (Typing Effect)
        txt_surf = self.font.render(self.displayed_text, True, config.WHITE)
        # FIX: Adjust text Y position to be centered below the face
        txt_rect = txt_surf.get_rect(center=(self.screen_width // 2, self.screen_height // 2 + 100))
        surface.blit(txt_surf, txt_rect)
        
        # 5. Draw Continue Prompt (Typing Effect)
        if not self.locked:
            hint_font = pygame.font.Font(config.FONT_NAME, 20)
            hint = hint_font.render(self.displayed_hint, True, config.CYAN)
            hint_rect = hint.get_rect(center=(self.screen_width // 2, txt_rect.bottom + 40))
            surface.blit(hint, hint_rect)

    @property 
    def is_locked(self) -> bool:
        return self.active and self.locked