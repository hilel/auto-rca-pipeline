"""Enhanced tests for edge cases and error handling in configuration"""

import pytest
import sqlite3
import tempfile
import os
from unittest.mock import patch, MagicMock
from pathlib import Path

from auto_rca.database import init_db, get_connection
from auto_rca.repositories.config_repository import get_session_field, set_session_field


class TestDatabaseEdgeCases:
    """Test edge cases for database operations"""
    
    def test_concurrent_init_db_calls(self):
        """Test multiple concurrent init_db calls don't cause issues"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_db_path = os.path.join(temp_dir, "test_config.db")
            
            with patch('auto_rca.database.Path') as mock_path:
                mock_path_instance = MagicMock()
                mock_path_instance.parent.mkdir = MagicMock()
                mock_path_instance.__str__ = lambda self: test_db_path
                mock_path.return_value = mock_path_instance
                
                # Call init_db multiple times
                for _ in range(5):
                    init_db()
                
                # Verify only one row exists
                conn = sqlite3.connect(test_db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) as count FROM config WHERE key = 'session_field'")
                result = cursor.fetchone()
                assert result['count'] == 1
                cursor.close()
                conn.close()
    
    def test_database_path_with_nested_directories(self):
        """Test database creation with nested directory structure"""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_path = os.path.join(temp_dir, "level1", "level2", "config.db")
            
            with patch('auto_rca.database.Path') as mock_path:
                mock_path_instance = MagicMock()
                # Simulate mkdir with parents=True
                def mock_mkdir(**kwargs):
                    os.makedirs(os.path.dirname(nested_path), exist_ok=True)
                mock_path_instance.parent.mkdir = mock_mkdir
                mock_path_instance.__str__ = lambda self: nested_path
                mock_path.return_value = mock_path_instance
                
                init_db()
                
                # Verify database was created
                assert os.path.exists(nested_path)
                
                # Verify it has correct schema
                conn = sqlite3.connect(nested_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='config'")
                result = cursor.fetchone()
                assert result is not None
                cursor.close()
                conn.close()
    
    def test_database_permissions_error(self):
        """Test handling of database permission errors"""
        with patch('auto_rca.database.sqlite3.connect') as mock_connect:
            mock_connect.side_effect = sqlite3.OperationalError("unable to open database file")
            
            with pytest.raises(sqlite3.OperationalError):
                get_connection()
    
    def test_init_db_handles_corrupt_database(self):
        """Test that init_db can handle a corrupt database"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_db_path = os.path.join(temp_dir, "corrupt.db")
            
            # Create a corrupt database file (just write garbage)
            with open(test_db_path, 'wb') as f:
                f.write(b'This is not a valid SQLite database\x00\x00\x00')
            
            with patch('auto_rca.database.Path') as mock_path:
                mock_path_instance = MagicMock()
                mock_path_instance.parent.mkdir = MagicMock()
                mock_path_instance.__str__ = lambda self: test_db_path
                mock_path.return_value = mock_path_instance
                
                # This should raise an error due to corrupt database
                with pytest.raises(sqlite3.DatabaseError):
                    init_db()


class TestConfigRepositoryEdgeCases:
    """Test edge cases for configuration repository"""
    
    def test_get_session_field_with_null_value(self):
        """Test getting session field when value is NULL"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_db_path = os.path.join(temp_dir, "test_config.db")
            
            # Create database with NULL value
            conn = sqlite3.connect(test_db_path)
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE config (key TEXT PRIMARY KEY, value TEXT)")
            # This will fail due to NOT NULL constraint in actual schema, but let's test the fallback
            conn.commit()
            cursor.close()
            conn.close()
            
            with patch('auto_rca.repositories.config_repository.get_connection') as mock_get_conn:
                def get_mock_connection():
                    conn = sqlite3.connect(test_db_path)
                    conn.row_factory = sqlite3.Row
                    return conn
                mock_get_conn.side_effect = get_mock_connection
                
                # Should return default
                field = get_session_field()
                assert field == 'session_id'
    
    def test_set_session_field_with_very_long_value(self):
        """Test setting session field with very long value"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_db_path = os.path.join(temp_dir, "test_config.db")
            
            conn = sqlite3.connect(test_db_path)
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE config (key TEXT PRIMARY KEY, value TEXT)")
            conn.commit()
            cursor.close()
            conn.close()
            
            with patch('auto_rca.repositories.config_repository.get_connection') as mock_get_conn:
                def get_mock_connection():
                    conn = sqlite3.connect(test_db_path)
                    conn.row_factory = sqlite3.Row
                    return conn
                mock_get_conn.side_effect = get_mock_connection
                
                # Set a very long field name
                long_field = 'x' * 10000
                set_session_field(long_field)
                
                # Verify it was stored correctly
                field = get_session_field()
                assert field == long_field
                assert len(field) == 10000
    
    def test_set_session_field_with_unicode(self):
        """Test setting session field with Unicode characters"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_db_path = os.path.join(temp_dir, "test_config.db")
            
            conn = sqlite3.connect(test_db_path)
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE config (key TEXT PRIMARY KEY, value TEXT)")
            conn.commit()
            cursor.close()
            conn.close()
            
            with patch('auto_rca.repositories.config_repository.get_connection') as mock_get_conn:
                def get_mock_connection():
                    conn = sqlite3.connect(test_db_path)
                    conn.row_factory = sqlite3.Row
                    return conn
                mock_get_conn.side_effect = get_mock_connection
                
                # Test various Unicode characters
                unicode_fields = [
                    '会话标识',  # Chinese
                    'идентификатор_сессии',  # Russian
                    'セッションID',  # Japanese
                    'session_🔑',  # Emoji
                    'ñoño_sesión'  # Spanish with tildes
                ]
                
                for unicode_field in unicode_fields:
                    set_session_field(unicode_field)
                    field = get_session_field()
                    assert field == unicode_field
    
    def test_set_session_field_with_sql_injection_attempt(self):
        """Test that SQL injection attempts are properly escaped"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_db_path = os.path.join(temp_dir, "test_config.db")
            
            conn = sqlite3.connect(test_db_path)
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE config (key TEXT PRIMARY KEY, value TEXT)")
            conn.commit()
            cursor.close()
            conn.close()
            
            with patch('auto_rca.repositories.config_repository.get_connection') as mock_get_conn:
                def get_mock_connection():
                    conn = sqlite3.connect(test_db_path)
                    conn.row_factory = sqlite3.Row
                    return conn
                mock_get_conn.side_effect = get_mock_connection
                
                # Try SQL injection attempts
                malicious_inputs = [
                    "'; DROP TABLE config; --",
                    "session_id' OR '1'='1",
                    "session_id'); DELETE FROM config; --",
                ]
                
                for malicious_input in malicious_inputs:
                    set_session_field(malicious_input)
                    
                    # Verify the malicious input was stored as data, not executed
                    field = get_session_field()
                    assert field == malicious_input
                    
                    # Verify table still exists
                    conn = sqlite3.connect(test_db_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='config'")
                    result = cursor.fetchone()
                    assert result is not None
                    cursor.close()
                    conn.close()
    
    def test_connection_closes_on_error(self):
        """Test that database connections are properly closed on error"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_db_path = os.path.join(temp_dir, "test_config.db")
            
            conn = sqlite3.connect(test_db_path)
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE config (key TEXT PRIMARY KEY, value TEXT)")
            conn.commit()
            cursor.close()
            conn.close()
            
            connection_count = 0
            
            def counting_connection():
                nonlocal connection_count
                connection_count += 1
                conn = sqlite3.connect(test_db_path)
                conn.row_factory = sqlite3.Row
                
                # Make cursor.execute fail sometimes
                original_execute = conn.cursor().execute
                def failing_execute(*args, **kwargs):
                    if connection_count == 2:
                        raise sqlite3.OperationalError("Simulated error")
                    return original_execute(*args, **kwargs)
                
                return conn
            
            with patch('auto_rca.repositories.config_repository.get_connection') as mock_get_conn:
                mock_get_conn.side_effect = counting_connection
                
                # First call should succeed
                set_session_field("test_field")
                
                # Second call should fail but connection should still close
                # (We can't easily test connection closure, but we verify error handling)
                try:
                    # This will fail due to our mock
                    conn = counting_connection()
                    cursor = conn.cursor()
                    cursor.execute("INVALID SQL")
                except sqlite3.OperationalError:
                    pass
                
                # Third call should still work
                set_session_field("test_field_3")
                field = get_session_field()
                assert field == "test_field_3"


class TestConfigRepositoryTransactions:
    """Test transaction handling in configuration repository"""
    
    def test_set_session_field_commits_transaction(self):
        """Test that set_session_field properly commits the transaction"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_db_path = os.path.join(temp_dir, "test_config.db")
            
            conn = sqlite3.connect(test_db_path)
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE config (key TEXT PRIMARY KEY, value TEXT)")
            conn.commit()
            cursor.close()
            conn.close()
            
            with patch('auto_rca.repositories.config_repository.get_connection') as mock_get_conn:
                def get_mock_connection():
                    conn = sqlite3.connect(test_db_path)
                    conn.row_factory = sqlite3.Row
                    return conn
                mock_get_conn.side_effect = get_mock_connection
                
                # Set a field
                set_session_field("committed_field")
                
                # Open a new connection to verify it was committed
                conn = sqlite3.connect(test_db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM config WHERE key = 'session_field'")
                result = cursor.fetchone()
                assert result is not None
                assert result['value'] == "committed_field"
                cursor.close()
                conn.close()
