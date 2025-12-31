"""Hazard primitives for Devil Run side-scrolling levels."""

from __future__ import annotations

import math
from typing import Optional, Tuple

import pygame

import config


class HazardBase:
    """Base class for all hazard types."""
    color = config.TRAP_COLOR

    def update(self, dt: float, player_rect: Optional[pygame.Rect] = None) -> None: 
        """Updates the hazard's state/position."""
        pass

    def draw(self, surface: pygame.Surface, camera_x: float) -> None: 
        """Draws the hazard relative to the camera."""
        pass

    def collides(self, rect: pygame.Rect) -> bool:
        """Checks collision with the player."""
        return False


class OscillatingHazard(HazardBase):
    """
    A block that moves back and forth (Vertical or Horizontal).
    Used for: Moving platforms, crushing ceilings, sliding walls.
    """
    def __init__(self, rect_tuple, axis: str = "y", amplitude: int = 35, speed: float = 2.2):
        self.base_rect = pygame.Rect(rect_tuple) # The starting position
        self.rect = pygame.Rect(rect_tuple)      # The current position
        self.axis = axis       # "x" or "y"
        self.amplitude = amplitude # How far it moves
        self.speed = speed     # How fast it moves
        self.timer = 0.0

    def update(self, dt: float, player_rect: Optional[pygame.Rect] = None) -> None:
        self.timer += dt
        # Calculate offset using sine wave for smooth movement
        offset = math.sin(self.timer * self.speed) * self.amplitude
        
        if self.axis == "x":
            self.rect.x = int(self.base_rect.x + offset)
        else:
            self.rect.y = int(self.base_rect.y + offset)

    def draw(self, surface: pygame.Surface, camera_x: float) -> None:
        screen_rect = self.rect.move(-camera_x, 0)
        pygame.draw.rect(surface, self.color, screen_rect)

    def collides(self, rect: pygame.Rect) -> bool:
        # Shrink the hitbox slightly for more 'generous' feel (4 pixels on each side)
        generous_rect = rect.inflate(-8, -8)
        return self.rect.colliderect(generous_rect)


class TriggerSpike(HazardBase):
    """
    A trap that stays hidden until the player enters the 'trigger' zone.
    Used for: Surprise spikes from the ground or ceiling.
    """
    def __init__(self, *, trigger_rect, spike_rect, rise_pixels: int = 40, rise_speed: float = 140.0):
        self.trigger_rect = pygame.Rect(trigger_rect) # The invisible zone that activates it
        self.rest_rect = pygame.Rect(spike_rect)      # The final position (deadly)
        self.rect = pygame.Rect(spike_rect)           # The current position
        
        # Start hidden (moved down by rise_pixels)
        self.hidden_y = self.rect.y + rise_pixels
        self.rect.y = self.hidden_y
        
        self.target_y = self.rest_rect.y
        self.rise_speed = rise_speed
        self.active = False

    def update(self, dt: float, player_rect: Optional[pygame.Rect] = None) -> None:
        # Check if player stepped on the trigger
        if not self.active and player_rect and player_rect.colliderect(self.trigger_rect):
            self.active = True
            
        # If active, move the spike up to the target position
        if self.active and self.rect.y > self.target_y:
            self.rect.y = max(self.target_y, self.rect.y - int(self.rise_speed * dt))

    def draw(self, surface: pygame.Surface, camera_x: float) -> None:
        screen_rect = self.rect.move(-camera_x, 0)
        pygame.draw.rect(surface, self.color, screen_rect)

    def collides(self, rect: pygame.Rect) -> bool:
        # Only kills if it has started moving/is active
        generous_rect = rect.inflate(-8, -8)
        return self.active and self.rect.colliderect(generous_rect)


class SwingingAxe(HazardBase):
    """
    A hazard that rotates back and forth around a pivot point.
    Used for: Timing challenges in advanced levels.
    """
    def __init__(
        self,
        *,
        pivot,
        length: int = 120,
        blade_size = (30, 60),
        swing_degrees: int = 45,
        speed: float = 1.8,
    ) -> None:
        self.pivot = pygame.Vector2(pivot)
        self.length = length
        self.blade_size = blade_size
        self.swing_radians = math.radians(swing_degrees)
        self.speed = speed
        self.time = 0.0
        self.rect = pygame.Rect(0, 0, blade_size[0], blade_size[1])

    def update(self, dt: float, player_rect: Optional[pygame.Rect] = None) -> None:
        self.time += dt
        # Calculate angle
        angle = math.sin(self.time * self.speed) * self.swing_radians
        
        # Calculate new position based on angle and length
        blade_center_x = self.pivot.x + math.sin(angle) * self.length
        blade_center_y = self.pivot.y + math.cos(angle) * self.length
        
        self.rect.center = (int(blade_center_x), int(blade_center_y))

    def draw(self, surface: pygame.Surface, camera_x: float) -> None:
        # Adjust pivot for camera
        screen_pivot = (int(self.pivot.x - camera_x), int(self.pivot.y))
        screen_rect = self.rect.move(-camera_x, 0)
        
        # Draw the "rope" or chain
        pygame.draw.line(surface, config.INK, screen_pivot, screen_rect.center, 4)
        # Draw the "blade"
        pygame.draw.rect(surface, self.color, screen_rect, border_radius=4)

    def collides(self, rect: pygame.Rect) -> bool:
        # Shrink the hitbox slightly for more 'generous' feel (4 pixels on each side)
        generous_rect = rect.inflate(-8, -8)
        return self.rect.colliderect(generous_rect)


class ChasingHazard(HazardBase):
    """
    A drone/ghost trap that tracks the player's X-position for a limited time.
    """
    def __init__(self, spawn_pos: Tuple[int, int], speed: float = 120.0, max_time: float = 3.0):
        self.pos = pygame.Vector2(spawn_pos)
        self.speed = speed
        self.max_time = max_time
        self.timer = max_time
        self.is_active = True
        self.rect = pygame.Rect(0, 0, config.TILE_SIZE, config.TILE_SIZE) # Standard size

    def update(self, dt: float, player_rect: Optional[pygame.Rect] = None) -> None:
        if not self.is_active:
            return

        self.timer -= dt
        if self.timer <= 0:
            self.is_active = False
            return

        if player_rect:
            # Calculate direction vector towards player's X-center
            target_x = player_rect.centerx
            direction_x = target_x - self.pos.x
            
            # Move towards player's X position
            if direction_x > 0:
                self.pos.x += min(direction_x, self.speed * dt)
            elif direction_x < 0:
                self.pos.x += max(direction_x, -self.speed * dt)
                
            # Maintain Y position (or add slow fall/rise if desired)
            
            # Update the collision rectangle
            self.rect.topleft = (int(self.pos.x - self.rect.width/2), int(self.pos.y))

    def draw(self, surface: pygame.Surface, camera_x: float) -> None:
        if self.is_active:
            screen_rect = self.rect.move(-camera_x, 0)
            # Draw as a pulsing circle/square (e.g., color changes based on timer)
            pulse_radius = int(config.TILE_SIZE * 0.4 * (0.5 + self.timer/self.max_time))
            pygame.draw.circle(surface, self.color, screen_rect.center, pulse_radius)

    def collides(self, rect: pygame.Rect) -> bool:
        generous_rect = rect.inflate(-8, -8)
        return self.is_active and self.rect.colliderect(generous_rect)
    
class DisappearingPlatform(HazardBase):
    """
    A platform that disappears when the player enters a defined trigger area.
    """
    def __init__(self, trigger_rect_tuple: Tuple, target_platform_rect: pygame.Rect):
        self.trigger_rect = pygame.Rect(trigger_rect_tuple)
        self.target_platform_rect = target_platform_rect
        self.is_removed = False

    def update(self, dt: float, player_rect: Optional[pygame.Rect] = None) -> None:
        if not self.is_removed and player_rect and player_rect.colliderect(self.trigger_rect):
            self.is_removed = True
            
    def draw(self, surface: pygame.Surface, camera_x: float) -> None:
        # This hazard is passive and drawn by level_manager (as a regular platform) 
        # unless we explicitly draw a visual effect here. We rely on level_manager 
        # removing it from its platforms list.
        pass


class CrushingHazard(HazardBase):
    """
    A ceiling trap that slams down when the player passes underneath.
    """
    def __init__(self, rect_tuple, slam_height: int = 400, speed: float = 600.0, return_speed: float = 100.0):
        self.base_rect = pygame.Rect(rect_tuple)
        self.rect = pygame.Rect(rect_tuple)
        self.slam_height = slam_height # How many pixels down it slams
        self.speed = speed
        self.return_speed = return_speed
        self.state = "IDLE" # IDLE, SLAMMING, RETURNING
        self.target_y = self.base_rect.y + slam_height
        
    def update(self, dt: float, player_rect: Optional[pygame.Rect] = None) -> None:
        if self.state == "IDLE":
            if player_rect and abs(player_rect.centerx - self.rect.centerx) < 100:
                self.state = "SLAMMING"
        
        elif self.state == "SLAMMING":
            self.rect.y += int(self.speed * dt)
            if self.rect.y >= self.target_y:
                self.rect.y = self.target_y
                self.state = "RETURNING"
        
        elif self.state == "RETURNING":
            self.rect.y -= int(self.return_speed * dt)
            if self.rect.y <= self.base_rect.y:
                self.rect.y = self.base_rect.y
                self.state = "IDLE"

    def draw(self, surface: pygame.Surface, camera_x: float) -> None:
        screen_rect = self.rect.move(-camera_x, 0)
        # Draw the crusher
        pygame.draw.rect(surface, config.PEACH_DARK, screen_rect)
        pygame.draw.rect(surface, self.color, screen_rect, 4) # Red border for danger

    def collides(self, rect: pygame.Rect) -> bool:
        return self.rect.colliderect(rect)