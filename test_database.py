import unittest
import os
import sqlite3
import shutil
from database_manager import DatabaseManager

class TestDatabaseManager(unittest.TestCase):
    def setUp(self):
        # Use a temporary SQLite database for testing
        self.test_db_path = "test_devil_run.db"
        self.db = DatabaseManager()
        # Mocking the connection string to force SQLite
        self.db._conn_parts = {} 
        # Manually force SQLite for tests
        self.db._db_type = "sqlite"
        self.db._conn = sqlite3.connect(self.test_db_path)
        self.db._conn.row_factory = sqlite3.Row
        self.db._ensure_schema()

    def tearDown(self):
        if self.db._conn:
            self.db._conn.close()
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

    def test_user_creation_and_auth(self):
        username = "testuser"
        password = "password123"
        name = "Test Name"
        dob = "2000-01-01"
        
        # Create user
        user_id = self.db.create_user(username, password, name, dob)
        self.assertIsNotNone(user_id)
        
        # Authenticate user
        user = self.db.authenticate_user(username, password)
        self.assertIsNotNone(user)
        self.assertEqual(user['username'], username)
        self.assertEqual(user['name'], name)

    def test_invalid_auth(self):
        username = "nonexistent"
        password = "wrongpassword"
        user = self.db.authenticate_user(username, password)
        self.assertIsNone(user)

    def test_log_death(self):
        level_id = 1
        x, y = 100, 200
        # No error should occur
        self.db.log_death(level_id, x, y)
        
        # Verify in DB
        deaths = self.db._execute("SELECT * FROM Deaths WHERE level_id = ?", (level_id,), fetchall=True)
        self.assertEqual(len(deaths), 1)
        self.assertEqual(deaths[0]['coord_x'], x)
        self.assertEqual(deaths[0]['coord_y'], y)

    def test_record_level_attempt(self):
        user_id = self.db.create_user("staruser", "pass", "Star User", "1990-01-01")
        level_id = 1
        attempts = 3
        stars = 3
        
        self.db.record_level_attempt(user_id, level_id, attempts, stars)
        
        # Verify log
        logs = self.db._execute("SELECT * FROM Level_Attempts WHERE user_id = ?", (user_id,), fetchall=True)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]['stars_earned'], stars)
        
        # Verify total stars updated
        user = self.db._execute("SELECT total_stars FROM Players WHERE id = ?", (user_id,), fetchone=True)
        self.assertEqual(user['total_stars'], stars)

if __name__ == "__main__":
    unittest.main()
