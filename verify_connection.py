from database_manager import db_manager
import os

print("Testing connection using DatabaseManager (with Fallback logic)...")

try:
    db_manager.connect()
    print(f"SUCCESS: Connected to database! Type: {db_manager._db_type}")
    
    # Try a simple query
    results = db_manager._execute("SELECT name FROM sys.objects WHERE type='U'", fetchall=True)
    if not results and db_manager._db_type == "sqlite":
         # sqlite equivalent
         results = db_manager._execute("SELECT name FROM sqlite_master WHERE type='table'", fetchall=True)
    
    print("Tables found:")
    if results:
        for table in results:
            print(f" - {table.get('name')}")
    else:
        print(" - (None yet)")
        
    db_manager.close()
except Exception as e:
    print(f"FAILURE: DB Manager failed. Error: {e}")
