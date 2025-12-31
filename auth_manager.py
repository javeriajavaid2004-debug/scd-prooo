"""Manages the Login/Signup UI state and submission logic."""

from __future__ import annotations

import sys
from typing import Dict, Optional, List
import random 

import pygame

import config
from database_manager import db_manager


class InputField:
    """Minimal peach-toned input for signup/login with smooth focus."""

    def __init__(self, rect: pygame.Rect, placeholder: str, *, is_password: bool = False) -> None:
        self.rect = rect
        self.placeholder = placeholder
        self.is_password = is_password
        self.text = ""
        self.active = False
        self.font = pygame.font.Font(config.FONT_NAME, config.AUTH_FONT_SIZE)
        self.last_enter_time = 0

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Returns True if a valid submission (Enter/Click) occurred."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
            return False

        if not self.active or event.type != pygame.KEYDOWN:
            return False

        if event.key == pygame.K_BACKSPACE:
            self.text = self.text[:-1]
        elif event.key == pygame.K_RETURN:
            if pygame.time.get_ticks() - self.last_enter_time > 300:
                self.last_enter_time = pygame.time.get_ticks()
                return True
        else:
            if len(event.unicode) == 1 and 32 <= ord(event.unicode) <= 126:
                self.text += event.unicode
        return False

    def draw(self, surface: pygame.Surface) -> None:
        border_color = config.UI_BORDER_COLOR if self.active else config.PEACH_MED
        pygame.draw.rect(surface, config.BACKGROUND_COLOR, self.rect)
        pygame.draw.rect(surface, border_color, self.rect, 3, border_radius=6)
        
        display = self.text if self.text else self.placeholder
        if self.text and self.is_password:
            display = "*" * len(self.text)
            
        color = config.UI_BUTTON_TEXT if self.text else config.PEACH_DARK
        
        # Render text, potentially clipped if too long for simple display
        # A proper implementation would scroll or clip based on width, 
        # but for now we trust the field width.
        text_surf = self.font.render(display, True, color)
        
        # Simple clipping to prevent overflow drawing
        if text_surf.get_width() > self.rect.width - 24:
             # Basic safety clip: only show last N chars if too long (rough approx)
             # Ideally use surface subsampling
             pass 

        text_rect = text_surf.get_rect(midleft=(self.rect.x + 12, self.rect.centery))
        surface.blit(text_surf, text_rect)

    def clear(self) -> None:
        self.text = ""

    def get_text(self) -> str:
        return self.text.strip()


class AuthManager:
    """Manages all authentication fields, state, and submissions."""
    
    TOXIC_WELCOME_PHRASES = [
        "Welcome back to failure, {username}.",
        "Ah, the fool returns. Prepare for disappointment, {username}.",
        "Glad you could stop wasting time elsewhere, {username}.",
        "The game was waiting for you to fail, {username}.",
        "Let the suffering begin, {username}.",
    ]

    def __init__(self, surface: pygame.Surface) -> None:
        self.surface = surface
        self.state = "LOGIN"  # LOGIN, SIGNUP
        self.auth_error = ""
        self.current_field_index = 0
        self.field_groups: Dict[str, List[InputField]] = {}
        self.title_font = pygame.font.Font(config.FONT_NAME, config.TITLE_FONT_SIZE)
        self.hud_font = pygame.font.Font(config.FONT_NAME, config.HUD_FONT_SIZE)
        self._setup_fields()
        self._set_active_group("LOGIN")

    def _setup_fields(self) -> None:
        field_width = 360
        field_height = 52
        center_x = config.SCREEN_WIDTH // 2
        base_y = config.SCREEN_HEIGHT // 2 - 120

        # Login Fields
        self.field_groups["LOGIN"] = [
            InputField(pygame.Rect(center_x - field_width // 2, base_y, field_width, field_height), "username"),
            InputField(pygame.Rect(center_x - field_width // 2, base_y + 70, field_width, field_height), "password", is_password=True),
        ]

        # Signup Fields (For detailed registration)
        # Shift starting Y up to fit more fields
        signup_start_y = base_y - 100 
        self.field_groups["SIGNUP"] = [
            InputField(pygame.Rect(center_x - field_width // 2, signup_start_y, field_width, field_height), "new username"),
            InputField(pygame.Rect(center_x - field_width // 2, signup_start_y + 70, field_width, field_height), "new password", is_password=True),
            InputField(pygame.Rect(center_x - field_width // 2, signup_start_y + 140, field_width, field_height), "confirm password", is_password=True),
            # NEW FIELDS
            InputField(pygame.Rect(center_x - field_width // 2, signup_start_y + 210, field_width, field_height), "full name"),
            InputField(pygame.Rect(center_x - field_width // 2, signup_start_y + 280, field_width, field_height), "dob (YYYY-MM-DD)"),
        ]

    def _set_active_group(self, state: str) -> None:
        self.state = state
        self.current_field_index = 0
        for group in self.field_groups.values():
            for field in group:
                field.active = False
        if state in self.field_groups:
            self.field_groups[state][0].active = True

    def toggle_mode(self) -> None:
        if self.state == "LOGIN":
            self._set_active_group("SIGNUP")
        else:
            self._set_active_group("LOGIN")
        self.auth_error = ""

    def handle_event(self, event: pygame.event.Event) -> Optional[Dict]:
        """
        Processes events and returns Dict on successful login/signup.
        The Dict includes the user data and the toxic welcome message.
        """
        current_fields = self.field_groups[self.state]
        
        # 1. Check Toggle Button Click (Top Left)
        if event.type == pygame.MOUSEBUTTONDOWN:
            toggle_rect = pygame.Rect(24, 24, 100, 48)
            if toggle_rect.collidepoint(event.pos):
                self.toggle_mode()
                return None # Consumes the click event

        # 2. Input Field and Submission Check
        for i, field in enumerate(current_fields):
            is_submission = field.handle_event(event)
            if field.active:
                self.current_field_index = i
            
            # Submission Logic (Enter key)
            if is_submission:
                if self.current_field_index < len(current_fields) - 1:
                    # Move to next field on Enter
                    self.current_field_index += 1
                    self.set_active_field(self.current_field_index)
                else:
                    # Submit form on Enter key press in the last field
                    return self._submit_form()
        
        # 3. Handle Mouse Click on the main submit button
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self._check_button_click(event.pos):
                return self._submit_form()
        
        return None # No successful submission occurred

    def set_active_field(self, index: int) -> None:
        current_fields = self.field_groups[self.state]
        self.current_field_index = max(0, min(index, len(current_fields) - 1))
        for i, field in enumerate(current_fields):
            field.active = (i == self.current_field_index)

    def _get_toxic_welcome_message(self, username: str) -> str:
        """Chooses a random toxic welcome message."""
        message = random.choice(self.TOXIC_WELCOME_PHRASES)
        return message.format(username=username)

    def _submit_form(self) -> Optional[Dict]:
        self.auth_error = ""
        
        if self.state == "LOGIN":
            username = self.field_groups["LOGIN"][0].get_text()
            password = self.field_groups["LOGIN"][1].get_text()
            if not username or not password:
                self.auth_error = "enter both fields."
                return None
            try:
                user = db_manager.authenticate_user(username, password)
            except RuntimeError as exc:
                self.auth_error = str(exc)
                return None
            if not user:
                self.auth_error = "bad credentials."
                return None
            
            # --- PACK SUCCESS RESULT ---
            welcome_msg = self._get_toxic_welcome_message(user['username'])
            
            return {"user": user, "success": True, "message": welcome_msg}

        else:  # SIGNUP
            fields = self.field_groups["SIGNUP"]
            username = fields[0].get_text()
            password = fields[1].get_text()
            confirm = fields[2].get_text()
            # New fields
            full_name = fields[3].get_text()
            dob = fields[4].get_text()
            
            if not username or not password or not confirm:
                self.auth_error = "fill required fields."
                return None
            if password != confirm:
                self.auth_error = "passwords mismatch."
                return None

            try:
                # Calls the DB to create user, passing new fields
                user_id = db_manager.create_user(username, password, full_name, dob) 
                if user_id > 0:
                    # FIX: Auto-login after signup to prevent user confusion
                    user = {
                        "id": user_id,
                        "username": username,
                        "total_stars": 0
                    }
                    welcome_msg = self._get_toxic_welcome_message(username)
                    return {"user": user, "success": True, "message": "Account created! " + welcome_msg}
            except RuntimeError as exc:
                self.auth_error = f"signup failed: {exc}"
                return None
            return None

    def _check_button_click(self, pos: tuple[int, int]) -> bool:
        button_rect = self._get_submit_button_rect()
        return button_rect.collidepoint(pos)

    def _get_submit_button_rect(self) -> pygame.Rect:
        button_rect = pygame.Rect(0, 0, 200, 56)
        # Push button lower for signup to fit new fields
        button_y = 0.72 if self.state == "LOGIN" else 0.88 
        button_rect.center = (config.SCREEN_WIDTH // 2, int(config.SCREEN_HEIGHT * button_y))
        return button_rect

    def draw(self) -> None:
        self.surface.fill(config.PEACH_LIGHT)
        
        # Header Bar
        pygame.draw.rect(self.surface, config.PEACH_DARK, (0, 0, config.SCREEN_WIDTH, 90))
        title_text = self.state.lower()
        title = self.title_font.render(title_text, True, config.ACCENT_WHITE)
        self.surface.blit(title, title.get_rect(center=(config.SCREEN_WIDTH // 2, 52)))

        # Toggle Button (Top Left)
        toggle_rect = pygame.Rect(24, 24, 100, 48)
        pygame.draw.rect(self.surface, config.UI_BUTTON_BG, toggle_rect, border_radius=6)
        arrow = "SIGN UP" if self.state == "LOGIN" else "LOG IN"
        arrow_surf = self.hud_font.render(arrow, True, config.UI_BUTTON_TEXT)
        self.surface.blit(arrow_surf, arrow_surf.get_rect(center=toggle_rect.center))

        # Input Fields
        for field in self.field_groups[self.state]:
            field.draw(self.surface)

        # Submit Button
        button_rect = self._get_submit_button_rect()
        btn_label = "create account" if self.state == "SIGNUP" else "login"
        pygame.draw.rect(self.surface, config.UI_BUTTON_BG, button_rect, border_radius=10)
        label = self.hud_font.render(btn_label, True, config.UI_BUTTON_TEXT)
        self.surface.blit(label, label.get_rect(center=button_rect.center))

        # Error Message
        if self.auth_error:
            error = self.hud_font.render(self.auth_error, True, config.ACCENT_RED)
            self.surface.blit(error, error.get_rect(center=(config.SCREEN_WIDTH // 2, button_rect.bottom + 20)))