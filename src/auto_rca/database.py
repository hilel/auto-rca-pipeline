"""SQLite database connection and initialization for configuration storage"""

import sqlite3
from pathlib import Path
from typing import Optional


def get_connection() -> sqlite3.Connection:
    """
    Get a connection to the SQLite database.
    
    Returns:
        sqlite3.Connection: Connection to the config database
    """
    # Ensure db directory exists
    db_path = Path("db/config.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(db_path))
    # Enable row factory for dictionary-like access
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """
    Initialize the database with config table and default values.
    Creates the config table if it doesn't exist and inserts default session_field.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Create config table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        
        # Check if session_field already exists
        cursor.execute("SELECT value FROM config WHERE key = 'session_field'")
        result = cursor.fetchone()
        
        # Insert default session_field if not present
        if result is None:
            cursor.execute(
                "INSERT INTO config (key, value) VALUES ('session_field', 'session_id')"
            )
        
        conn.commit()
    finally:
        cursor.close()
        conn.close()
