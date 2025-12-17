"""Configuration repository for managing application configuration in SQLite"""

from auto_rca.database import get_connection


def get_session_field() -> str:
    """
    Get the current session identifier field from the config database.
    
    Returns:
        str: The field name to use for session identification (default: 'session_id')
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT value FROM config WHERE key = 'session_field'")
        result = cursor.fetchone()
        
        if result:
            return result['value']
        else:
            # Default to 'session_id' if not found
            return 'session_id'
    finally:
        cursor.close()
        conn.close()


def set_session_field(field_name: str) -> None:
    """
    Update the session identifier field in the config database.
    
    Args:
        field_name: The field name to use for session identification
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Use INSERT OR REPLACE to update or insert
        cursor.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES ('session_field', ?)",
            (field_name,)
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()
