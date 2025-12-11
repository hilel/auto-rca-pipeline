"""Unit tests for log parsing module"""

import pytest
from datetime import datetime

from auto_rca.parsing import LogParser


class TestLogParser:
    """Test cases for LogParser class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.parser = LogParser()
    
    def test_parse_text_log(self):
        """Test parsing text log entry"""
        log_entry = {
            'raw_text': '[2024-01-01 10:00:00] ERROR - Database connection failed',
            'format': 'text'
        }
        
        parsed = self.parser.parse_log(log_entry)
        
        assert parsed['log_level'] == 'ERROR'
        assert parsed['timestamp'] is not None
        assert 'Database connection failed' in parsed['message']
    
    def test_parse_json_log(self):
        """Test parsing JSON log entry"""
        log_entry = {
            'timestamp': '2024-01-01T10:00:00',
            'level': 'INFO',
            'message': 'Request processed',
            'user_id': 'user_123',
            'request_id': 'req_456',
            'format': 'json'
        }
        
        parsed = self.parser.parse_log(log_entry)
        
        assert parsed['log_level'] == 'INFO'
        assert parsed['timestamp'] == '2024-01-01T10:00:00'
        assert parsed['user_id'] == 'user_123'
        assert parsed['request_id'] == 'req_456'
    
    def test_extract_ip_address(self):
        """Test IP address extraction"""
        log_entry = {
            'raw_text': '192.168.1.100 - GET /api/users',
            'format': 'text'
        }
        
        parsed = self.parser.parse_log(log_entry)
        
        assert parsed['ip_address'] == '192.168.1.100'
    
    def test_extract_http_info(self):
        """Test HTTP method and status code extraction"""
        log_entry = {
            'raw_text': 'GET /api/users 200',
            'format': 'text'
        }
        
        parsed = self.parser.parse_log(log_entry)
        
        assert parsed['http_method'] == 'GET'
        assert parsed['status_code'] == 200
    
    def test_extract_exception(self):
        """Test exception extraction"""
        log_entry = {
            'raw_text': 'NullPointerException: Object reference not set to instance',
            'format': 'text'
        }
        
        parsed = self.parser.parse_log(log_entry)
        
        assert parsed['exception'] is not None
        assert 'Object reference not set to instance' in parsed['exception']
    
    def test_parse_multiple_logs(self):
        """Test parsing multiple log entries"""
        log_entries = [
            {'raw_text': '[2024-01-01 10:00:00] INFO - Started', 'format': 'text'},
            {'raw_text': '[2024-01-01 10:00:01] ERROR - Failed', 'format': 'text'},
            {'raw_text': '[2024-01-01 10:00:02] DEBUG - Debugging', 'format': 'text'}
        ]
        
        parsed_logs = self.parser.parse_logs(log_entries)
        
        assert len(parsed_logs) == 3
        assert parsed_logs[0]['log_level'] == 'INFO'
        assert parsed_logs[1]['log_level'] == 'ERROR'
        assert parsed_logs[2]['log_level'] == 'DEBUG'
