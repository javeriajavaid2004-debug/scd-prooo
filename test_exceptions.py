import unittest
import sqlite3
import os
from database_manager import DatabaseManager
from level_manager import LevelManager

class TestExceptionHandling(unittest.TestCase):
    def setUp(self):
        self.db = DatabaseManager()

    def test_database_connection_failure(self):
        # Testing behavior when connection string is completely invalid
        self.db._conn_parts = {"SERVER": "invalid_server", "DATABASE": "invalid_db"}
        
        # Depending on implementation, it might fallback to SQLite or raise error
        # In this project, it falls back to SQLite. Let's verify it doesn't crash.
        try:
            self.db.connect()
        except Exception as e:
            self.fail(f"Database connection raised an unexpected exception: {e}")
        
        self.assertEqual(self.db._db_type, "sqlite")

    def test_invalid_auth_input(self):
        # Testing with None or empty values
        user = self.db.authenticate_user("", "")
        self.assertIsNone(user)

    def test_level_loading_index_out_of_bounds(self):
        lm = LevelManager(level_id=1)
        # Testing if it handles out of bounds index gracefully (should use modulo)
        try:
            lm.load_level(index=999)
            self.assertIsNotNone(lm.level_id)
        except Exception as e:
            self.fail(f"LevelManager failed to handle out-of-bounds index: {e}")

    def test_sql_execution_error_handling(self):
        # Force a syntax error in a raw execute (if exposed) or via a mock
        # We test that _execute rolls back and raises RuntimeError
        self.db.connect()
        with self.assertRaises(RuntimeError):
            self.db._execute("SELECT * FROM NonExistentTable")

if __name__ == "__main__":
    unittest.main()
