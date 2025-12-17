"""Unit tests for configuration functionality"""

import pytest
import sqlite3
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from auto_rca.database import init_db, get_connection
from auto_rca.repositories.config_repository import get_session_field, set_session_field


class TestDatabase:
    """Test cases for database module"""
    
    def test_init_db_creates_table_and_default(self):
        """Test that init_db creates the config table with default value"""
        # Use a temporary database
        with tempfile.TemporaryDirectory() as temp_dir:
            test_db_path = os.path.join(temp_dir, "test_config.db")
            
            # Patch the Path to use our test database
            with patch('auto_rca.database.Path') as mock_path:
                mock_path_instance = MagicMock()
                mock_path_instance.parent.mkdir = MagicMock()
                mock_path_instance.__str__ = lambda self: test_db_path
                mock_path.return_value = mock_path_instance
                
                # Initialize database
                init_db()
                
                # Verify table and default value exist
                conn = sqlite3.connect(test_db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Check table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='config'")
                result = cursor.fetchone()
                assert result is not None
                
                # Check default value
                cursor.execute("SELECT value FROM config WHERE key = 'session_field'")
                result = cursor.fetchone()
                assert result is not None
                assert result['value'] == 'session_id'
                
                cursor.close()
                conn.close()
    
    def test_init_db_does_not_overwrite_existing(self):
        """Test that init_db doesn't overwrite existing session_field"""
        # Use a temporary database
        with tempfile.TemporaryDirectory() as temp_dir:
            test_db_path = os.path.join(temp_dir, "test_config.db")
            
            # Patch the Path to use our test database
            with patch('auto_rca.database.Path') as mock_path:
                mock_path_instance = MagicMock()
                mock_path_instance.parent.mkdir = MagicMock()
                mock_path_instance.__str__ = lambda self: test_db_path
                mock_path.return_value = mock_path_instance
                
                # Initialize first time
                init_db()
                
                # Change the value directly
                conn = sqlite3.connect(test_db_path)
                cursor = conn.cursor()
                cursor.execute("UPDATE config SET value = 'token' WHERE key = 'session_field'")
                conn.commit()
                cursor.close()
                conn.close()
                
                # Initialize again
                init_db()
                
                # Verify value is still 'token'
                conn = sqlite3.connect(test_db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM config WHERE key = 'session_field'")
                result = cursor.fetchone()
                assert result is not None
                assert result['value'] == 'token'
                cursor.close()
                conn.close()


class TestConfigRepository:
    """Test cases for configuration repository"""
    
    def test_get_session_field_default(self):
        """Test getting default session field"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_db_path = os.path.join(temp_dir, "test_config.db")
            
            # Create database with default value
            conn = sqlite3.connect(test_db_path)
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE config (key TEXT PRIMARY KEY, value TEXT)")
            cursor.execute("INSERT INTO config (key, value) VALUES ('session_field', 'session_id')")
            conn.commit()
            cursor.close()
            conn.close()
            
            # Mock get_connection
            with patch('auto_rca.repositories.config_repository.get_connection') as mock_get_conn:
                def get_mock_connection():
                    conn = sqlite3.connect(test_db_path)
                    conn.row_factory = sqlite3.Row
                    return conn
                mock_get_conn.side_effect = get_mock_connection
                
                # Get session field
                field = get_session_field()
                assert field == 'session_id'
    
    def test_get_session_field_custom(self):
        """Test getting custom session field"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_db_path = os.path.join(temp_dir, "test_config.db")
            
            # Create database with custom value
            conn = sqlite3.connect(test_db_path)
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE config (key TEXT PRIMARY KEY, value TEXT)")
            cursor.execute("INSERT INTO config (key, value) VALUES ('session_field', 'token')")
            conn.commit()
            cursor.close()
            conn.close()
            
            # Mock get_connection
            with patch('auto_rca.repositories.config_repository.get_connection') as mock_get_conn:
                def get_mock_connection():
                    conn = sqlite3.connect(test_db_path)
                    conn.row_factory = sqlite3.Row
                    return conn
                mock_get_conn.side_effect = get_mock_connection
                
                # Get session field
                field = get_session_field()
                assert field == 'token'
    
    def test_get_session_field_missing(self):
        """Test getting session field when not in database"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_db_path = os.path.join(temp_dir, "test_config.db")
            
            # Create database without session_field
            conn = sqlite3.connect(test_db_path)
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE config (key TEXT PRIMARY KEY, value TEXT)")
            conn.commit()
            cursor.close()
            conn.close()
            
            # Mock get_connection
            with patch('auto_rca.repositories.config_repository.get_connection') as mock_get_conn:
                def get_mock_connection():
                    conn = sqlite3.connect(test_db_path)
                    conn.row_factory = sqlite3.Row
                    return conn
                mock_get_conn.side_effect = get_mock_connection
                
                # Get session field - should return default
                field = get_session_field()
                assert field == 'session_id'
    
    def test_set_session_field(self):
        """Test setting session field"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_db_path = os.path.join(temp_dir, "test_config.db")
            
            # Create database
            conn = sqlite3.connect(test_db_path)
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE config (key TEXT PRIMARY KEY, value TEXT)")
            conn.commit()
            cursor.close()
            conn.close()
            
            # Mock get_connection
            with patch('auto_rca.repositories.config_repository.get_connection') as mock_get_conn:
                def get_mock_connection():
                    conn = sqlite3.connect(test_db_path)
                    conn.row_factory = sqlite3.Row
                    return conn
                mock_get_conn.side_effect = get_mock_connection
                
                # Set session field
                set_session_field('order_id')
                
                # Verify it was set
                conn = sqlite3.connect(test_db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM config WHERE key = 'session_field'")
                result = cursor.fetchone()
                assert result is not None
                assert result['value'] == 'order_id'
                cursor.close()
                conn.close()
    
    def test_set_session_field_update(self):
        """Test updating existing session field"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_db_path = os.path.join(temp_dir, "test_config.db")
            
            # Create database with existing value
            conn = sqlite3.connect(test_db_path)
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE config (key TEXT PRIMARY KEY, value TEXT)")
            cursor.execute("INSERT INTO config (key, value) VALUES ('session_field', 'session_id')")
            conn.commit()
            cursor.close()
            conn.close()
            
            # Mock get_connection
            with patch('auto_rca.repositories.config_repository.get_connection') as mock_get_conn:
                def get_mock_connection():
                    conn = sqlite3.connect(test_db_path)
                    conn.row_factory = sqlite3.Row
                    return conn
                mock_get_conn.side_effect = get_mock_connection
                
                # Update session field
                set_session_field('transaction_id')
                
                # Verify it was updated
                conn = sqlite3.connect(test_db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM config WHERE key = 'session_field'")
                result = cursor.fetchone()
                assert result is not None
                assert result['value'] == 'transaction_id'
                cursor.close()
                conn.close()

