"""Handles all database interactions for Devil Run."""

from __future__ import annotations

import hashlib
from typing import Dict, List, Optional, Sequence

import pyodbc
import sqlite3
import os

import config


class DatabaseManager:
    """Simple wrapper around pyodbc for project-specific queries."""

    def __init__(self) -> None:
        self._conn: Optional[pyodbc.Connection] = None
        self._logged_connection_ok = False
        self._schema_ready = False
        self._conn_parts = self._parse_connection_string(config.DB_CONNECTION_STRING)

    # ------------------------------------------------------------------
    # Connection helpers (omitted for brevity, assume working)
    # ------------------------------------------------------------------

    def connect(self) -> None:
        if self._conn:
            return
            
        # 1. Try configured ODBC (SQL Server)
        try:
            target_conn_str = self._build_connection_string(self._conn_parts)
            self._conn = pyodbc.connect(target_conn_str, autocommit=False)
            self._db_type = "mssql"
            if not self._logged_connection_ok:
                print(f"[DB] Connected to SQL Server: {self._conn_parts.get('SERVER')}")
                self._logged_connection_ok = True
            self._ensure_schema()
            return
        except (pyodbc.Error, RuntimeError) as exc:
            print(f"[DB] SQL Server connection failed: {exc}")
            
        # 2. Try Fallback: SQLite
        print("[DB] Falling back to SQLite for local progress...")
        try:
            db_path = "devil_run.db"
            self._conn = sqlite3.connect(db_path)
            self._conn.row_factory = sqlite3.Row
            self._db_type = "sqlite"
            self._ensure_schema()
            if not self._logged_connection_ok:
                print(f"[DB] Connected to SQLite: {os.path.abspath(db_path)}")
                self._logged_connection_ok = True
        except Exception as exc:
            print(f"[DB] Critical Failure: Could not connect to any database! {exc}")
            raise

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    @staticmethod
    def _hash_password(raw_password: str) -> str:
        return hashlib.sha256(raw_password.encode("utf-8")).hexdigest()

    def _execute(
        self,
        query: str,
        params: Sequence = (),
        *,
        fetchone: bool = False,
        fetchall: bool = False,
        commit: bool = False,
    ):
        self.connect()
        assert self._conn is not None
        
        # SQL Server uses ? as placeholder, SQLite also uses ?
        # However, SQL Server functions like GETDATE() or ISNULL() differ in SQLite.
        # We'll normalize common dialect differences.
        if self._db_type == "sqlite":
            import re
            query = query.replace("GETDATE()", "CURRENT_TIMESTAMP")
            query = query.replace("ISNULL(", "IFNULL(")
            
            # Handle the IF OBJECT_ID pattern
            if "IF OBJECT_ID" in query:
                query = re.sub(r"IF OBJECT_ID\(.*?, 'U'\) IS NULL\s+CREATE TABLE\s+(dbo\.)?(\w+)", r"CREATE TABLE IF NOT EXISTS \2", query, flags=re.IGNORECASE)

            # Standardize types and identity
            query = query.replace("INT IDENTITY(1,1) PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT")
            query = query.replace("IDENTITY(1,1)", "PRIMARY KEY AUTOINCREMENT")
            query = query.replace("NVARCHAR", "VARCHAR")
            query = query.replace("dbo.", "")
            
            # SQLite doesn't support OUTPUT INSERTED.id. We'll use lastrowid.
            is_insert_with_output = "OUTPUT INSERTED.id" in query
            if is_insert_with_output:
                query = query.replace("OUTPUT INSERTED.id AS user_id", "")

        try:
            cursor = self._conn.cursor()
            cursor.execute(query, params)
            
            row = None
            if fetchone:
                raw_row = cursor.fetchone()
                row = self._row_to_dict(cursor, raw_row)
                if self._db_type == "sqlite" and is_insert_with_output and row is None:
                    # Special case for user creation output
                    row = {"user_id": cursor.lastrowid}
            elif fetchall:
                rows = cursor.fetchall()
                row = [self._row_to_dict(cursor, r) for r in rows]
            
            if commit:
                self._conn.commit()
            
            return row
        except (pyodbc.Error, sqlite3.Error) as exc:
            print(f"[DB] Query failed ({self._db_type}): {exc} | SQL: {query}")
            if self._conn: self._conn.rollback()
            raise RuntimeError(f"Database query failed: {exc}") from exc
        finally:
            if 'cursor' in locals(): cursor.close()

    # --- Utility Definitions (Keep these) ---
    @staticmethod
    def _parse_connection_string(conn_str: str) -> Dict[str, str]:
        parts: Dict[str, str] = {}
        for segment in conn_str.split(";"):
            if not segment.strip(): continue
            if "=" not in segment: continue
            key, value = segment.split("=", 1)
            parts[key.strip().upper()] = value.strip()
        return parts

    @staticmethod
    def _build_connection_string(parts: Dict[str, str]) -> str:
        return ";".join(f"{key}={value}" for key, value in parts.items() if value) + ";"

    @staticmethod
    def _is_missing_database_error(exc: pyodbc.Error) -> bool:
        message = str(exc).lower()
        return "cannot open database" in message or "does not exist" in message or "cannot find the database" in message

    def _ensure_database_exists(self) -> None:
        target_db = self._conn_parts.get("DATABASE")
        if not target_db: return
        master_parts = dict(self._conn_parts)
        master_parts["DATABASE"] = "master"
        conn_str = self._build_connection_string(master_parts)
        escaped_db = target_db.replace("]", "]]" )
        try:
            with pyodbc.connect(conn_str, autocommit=True) as master_conn:
                cursor = master_conn.cursor()
                cursor.execute(
                    f"IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = '{escaped_db}') "
                    f"BEGIN CREATE DATABASE [{escaped_db}] END"
                )
                cursor.close()
        except pyodbc.Error as exc:
            raise RuntimeError(f"Database bootstrap failed: {exc}") from exc


    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._conn: return
        
        try:
            # Table: Players
            # Note: _execute handles dialect translations like GETDATE() -> CURRENT_TIMESTAMP
            self._execute(
                "IF OBJECT_ID('dbo.Players', 'U') IS NULL "
                "CREATE TABLE dbo.Players ("
                "id INT IDENTITY(1,1) PRIMARY KEY, "
                "username NVARCHAR(50) NOT NULL UNIQUE, "
                "password_hash CHAR(64) NOT NULL, "
                "name NVARCHAR(100) NULL, "
                "dob NVARCHAR(20) NULL, "
                "total_stars INT NOT NULL DEFAULT 0, "
                "created_at DATETIME NOT NULL DEFAULT GETDATE())",
                commit=True
            )
            
            # Table: Deaths
            self._execute(
                "IF OBJECT_ID('dbo.Deaths', 'U') IS NULL "
                "CREATE TABLE dbo.Deaths ("
                "id INT IDENTITY(1,1) PRIMARY KEY, "
                "level_id INT NOT NULL, "
                "coord_x INT NOT NULL, "
                "coord_y INT NOT NULL, "
                "created_at DATETIME NOT NULL DEFAULT GETDATE())",
                commit=True
            )
            
            # Table: Level_Attempts
            self._execute(
                "IF OBJECT_ID('dbo.Level_Attempts', 'U') IS NULL "
                "CREATE TABLE dbo.Level_Attempts ("
                "id INT IDENTITY(1,1) PRIMARY KEY, "
                "user_id INT NOT NULL, "
                "level_id INT NOT NULL, "
                "attempts INT NOT NULL, "
                "stars_earned INT NOT NULL, "
                "completed_at DATETIME NOT NULL DEFAULT GETDATE())",
                commit=True
            )
            
            self._schema_ready = True
            print(f"[DB] Schema verified/initialized on {self._db_type}.")
        except Exception as exc:
            print(f"[DB] Schema check failed: {exc}")
            raise RuntimeError(f"Database schema initialization failed: {exc}") from exc

    @staticmethod
    def _row_to_dict(cursor: pyodbc.Cursor, row: Optional[pyodbc.Row]):
        if row is None: return None
        if not cursor.description: return row
        columns = [col[0] for col in cursor.description]
        return {col: row[idx] for idx, col in enumerate(columns)}
    
    # --- NEW HELPER FOR MAX STAR LOGIC ---

    def _get_max_stars_for_level(self, user_id: int, level_id: int) -> int:
        """Fetches the maximum number of stars a user has currently earned on a specific level."""
        query = (
            "SELECT ISNULL(MAX(stars_earned), 0) AS max_stars "
            "FROM Level_Attempts WHERE user_id = ? AND level_id = ?"
        )
        result = self._execute(query, (user_id, level_id), fetchone=True)
        # Handle the result safely, ISNULL should prevent None but better be safe
        return int(result['max_stars']) if result and 'max_stars' in result else 0

    # ------------------------------------------------------------------
    # User Management
    # ------------------------------------------------------------------

    def create_user(
        self, 
        username: str, 
        password: str, 
        name: Optional[str] = None, 
        dob: Optional[str] = None
    ) -> int:
        password_hash = self._hash_password(password)
        query = (
            "INSERT INTO Players (username, password_hash, name, dob, total_stars) "
            "OUTPUT INSERTED.id AS user_id "
            "VALUES (?, ?, ?, ?, 0)"
        )
        result = self._execute(query, (username, password_hash, name, dob), commit=True, fetchone=True)
        return int(result.get("user_id")) if result else -1

    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        query = "SELECT id, username, password_hash, total_stars, name FROM Players WHERE username = ?"
        record = self._execute(query, (username,), fetchone=True)
        if not record:
            return None
        provided_hash = self._hash_password(password)
        if provided_hash != record["password_hash"]:
            return None
        return {
            "id": record["id"],
            "username": record["username"],
            "total_stars": record["total_stars"],
            "name": record["name"],
        }

    def delete_user(self, user_id: int) -> bool:
        """Deletes a user and their associated progression data."""
        try:
            self._execute("DELETE FROM Level_Attempts WHERE user_id = ?", (user_id,), commit=True)
            self._execute("DELETE FROM Players WHERE id = ?", (user_id,), commit=True)
            return True
        except Exception as e:
            print(f"Error deleting user: {e}")
            return False

    # ------------------------------------------------------------------
    # Gameplay Data
    # ------------------------------------------------------------------
    def get_player_level_stars(self, user_id: int) -> Dict[int, int]:
        """Retrieves map of {level_id: max_stars} for map progression."""
        query = (
            "SELECT level_id, MAX(stars_earned) AS stars "
            "FROM Level_Attempts WHERE user_id = ? "
            "GROUP BY level_id"
        )
        results = self._execute(query, (user_id,), fetchall=True) or []
        return {r['level_id']: r['stars'] for r in results}

    def get_player_level_stars(self, user_id: int) -> Dict[int, int]:
        """Retrieves map of {level_id: max_stars} for map progression."""
        query = (
            "SELECT level_id, MAX(stars_earned) AS stars "
            "FROM Level_Attempts WHERE user_id = ? "
            "GROUP BY level_id"
        )
        results = self._execute(query, (user_id,), fetchall=True) or []
        return {r['level_id']: r['stars'] for r in results}

    def log_death(self, level_id: int, coord_x: int, coord_y: int) -> None:
        query = (
            "INSERT INTO Deaths (level_id, coord_x, coord_y, created_at) "
            "VALUES (?, ?, ?, GETDATE())"
        )
        self._execute(query, (level_id, coord_x, coord_y), commit=True)

    def get_most_lethal_spots(self, level_id: int, limit: int = 5) -> List[Dict]:
        query = (
            "SELECT coord_x, coord_y, COUNT(*) AS death_count "
            "FROM Deaths WHERE level_id = ? "
            "GROUP BY coord_x, coord_y "
            "ORDER BY death_count DESC "
            "OFFSET 0 ROWS FETCH NEXT ? ROWS ONLY"
        )
        return self._execute(query, (level_id, limit), fetchall=True) or []

    def record_level_attempt(
        self,
        user_id: int,
        level_id: int,
        attempts: int,
        stars_earned: int,
    ) -> None:
        """
        CRITICAL FIX: Ensures only the net gain in stars (new high score - old high score)
        is added to the Player's total stars.
        """
        
        # 1. Get the current maximum stars for this level
        max_stars_old = self._get_max_stars_for_level(user_id, level_id)
        
        # 2. Determine the net gain (delta)
        # If new score is 2, and old score was 1, delta = 1.
        # If new score is 1, and old score was 2, delta = -1, clamped to 0.
        star_delta = max(0, stars_earned - max_stars_old)

        # 3. Insert the new attempt record (we save all attempts for metrics)
        insert_attempt = (
            "INSERT INTO Level_Attempts (user_id, level_id, attempts, stars_earned, completed_at) "
            "VALUES (?, ?, ?, ?, GETDATE())"
        )
        self._execute(insert_attempt, (user_id, level_id, attempts, stars_earned), commit=True)

        # 4. Update the Player's total stars ONLY if there was a net gain
        if star_delta > 0:
            update_player = "UPDATE Players SET total_stars = total_stars + ? WHERE id = ?"
            self._execute(update_player, (star_delta, user_id), commit=True)


db_manager = DatabaseManager()