import unittest
import pygame
from level_manager import LevelManager, LEVEL_BLUEPRINTS

class TestLevelManager(unittest.TestCase):
    def setUp(self):
        pygame.init()
        # Mocking screen for TILE_SIZE if needed, but LevelManager uses config.py
        self.lm = LevelManager(level_id=1)

    def test_level_loading(self):
        self.lm.load_level(index=0)
        self.assertEqual(self.lm.level_id, 1)
        self.assertGreater(len(self.lm.platforms), 0)
        self.assertGreater(len(self.lm.oscillators), 0)

    def test_star_rating_logic(self):
        # 3 or fewer attempts = 3 stars
        self.lm.reset_attempts()
        self.lm.increment_attempts() # 1
        self.lm.increment_attempts() # 2
        self.assertEqual(self.lm.calculate_star_rating(), 3)
        
        # 4-5 attempts = 2 stars
        self.lm.increment_attempts() # 3
        self.lm.increment_attempts() # 4
        self.assertEqual(self.lm.calculate_star_rating(), 2)
        
        # > 5 attempts = 1 star
        self.lm.increment_attempts() # 5
        self.lm.increment_attempts() # 6
        self.assertEqual(self.lm.calculate_star_rating(), 1)

    def test_hazard_collision_check(self):
        self.lm.load_level(index=0)
        # Place a player rect where we know a static trap or hazard might be
        # In Level 1, static_traps[0] is R(10, 1, 2, 1)
        # R(10, 1, 2, 1) converts to (TILE*10, GROUND_Y - TILE*1, TILE*2, TILE*1)
        # Using the R function directly for testing
        from level_manager import R
        trap_rect = pygame.Rect(*R(10, 1, 2, 1))
        
        # Create a player rect inside that trap
        player_rect = trap_rect.copy()
        player_rect.inflate_ip(-5, -5)
        
        self.assertTrue(self.lm.check_hazard_collision(player_rect))

if __name__ == "__main__":
    unittest.main()
