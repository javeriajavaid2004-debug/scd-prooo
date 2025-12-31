import unittest
import pygame
from hazards import OscillatingHazard, TriggerSpike, ChasingHazard, CrushingHazard

class TestHazards(unittest.TestCase):
    def setUp(self):
        pygame.init()

    def test_oscillating_hazard_movement(self):
        # Initial position
        rect_tuple = (100, 100, 50, 50)
        osc = OscillatingHazard(rect_tuple, axis='y', amplitude=100, speed=1.0)
        
        initial_y = osc.rect.y
        # Update with dt
        osc.update(0.5, pygame.Rect(0, 0, 10, 10))
        
        # After 0.5s at speed 1.0, sin(0.5) should be > 0
        self.assertNotEqual(osc.rect.y, initial_y)

    def test_trigger_spike_activation(self):
        trigger_rect = (100, 100, 50, 50)
        spike_rect = (100, 50, 50, 50)
        trig = TriggerSpike(trigger_rect=trigger_rect, spike_rect=spike_rect)
        
        self.assertFalse(trig.active)
        
        # Player inside trigger
        player_rect = pygame.Rect(110, 110, 10, 10)
        trig.update(0.1, player_rect)
        
        self.assertTrue(trig.active)
        # Collision with active spike
        self.assertTrue(trig.collides(player_rect))

    def test_crushing_hazard_slam(self):
        rect_tuple = (100, 0, 50, 50)
        slam_height = 400
        crush = CrushingHazard(rect_tuple, slam_height=slam_height)
        
        initial_y = crush.rect.y
        # Move player under it to trigger SLAMMING state
        player_rect = pygame.Rect(120, 100, 10, 10) # Centered enough on X
        
        crush.update(0.1, player_rect) # First update sets state to SLAMMING
        crush.update(0.1, player_rect) # Second update moves it
        self.assertGreater(crush.rect.y, initial_y)

    def test_chasing_hazard_logic(self):
        spawn_pos = (100, 100)
        chaser = ChasingHazard(spawn_pos, speed=100.0, max_time=5.0)
        
        player_rect = pygame.Rect(200, 200, 10, 10)
        initial_pos = pygame.Vector2(chaser.pos)
        
        chaser.update(0.1, player_rect)
        
        # Distance should decrease
        new_dist = pygame.Vector2(chaser.pos).distance_to(pygame.Vector2(player_rect.center))
        old_dist = initial_pos.distance_to(pygame.Vector2(player_rect.center))
        self.assertLess(new_dist, old_dist)

if __name__ == "__main__":
    unittest.main()
