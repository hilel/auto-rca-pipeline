"""Unit tests for sessionization module"""

import pytest
from datetime import datetime, timedelta

from auto_rca.sessionization import SessionGrouper


class TestSessionGrouper:
    """Test cases for SessionGrouper class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.grouper = SessionGrouper(session_gap_seconds=300)
    
    def create_log_entry(self, timestamp, user_id='user_1', log_level='INFO'):
        """Helper to create a log entry"""
        return {
            'timestamp': timestamp.isoformat(),
            'user_id': user_id,
            'log_level': log_level,
            'message': f'{log_level} message'
        }
    
    def test_group_by_user_id(self):
        """Test grouping logs by user ID"""
        base_time = datetime.now()
        
        log_entries = [
            self.create_log_entry(base_time, 'user_1'),
            self.create_log_entry(base_time + timedelta(seconds=10), 'user_1'),
            self.create_log_entry(base_time + timedelta(seconds=20), 'user_2'),
            self.create_log_entry(base_time + timedelta(seconds=30), 'user_2'),
        ]
        
        sessions = self.grouper.group_by_session(log_entries)
        
        assert len(sessions) == 2
        # Each user should have one session
        session_ids = [s['session_id'] for s in sessions]
        assert 'user_1' in session_ids
        assert 'user_2' in session_ids
    
    def test_split_by_time_gap(self):
        """Test splitting sessions by time gap"""
        base_time = datetime.now()
        
        log_entries = [
            self.create_log_entry(base_time, 'user_1'),
            self.create_log_entry(base_time + timedelta(seconds=10), 'user_1'),
            # Large gap (10 minutes)
            self.create_log_entry(base_time + timedelta(minutes=10), 'user_1'),
            self.create_log_entry(base_time + timedelta(minutes=10, seconds=10), 'user_1'),
        ]
        
        sessions = self.grouper.group_by_session(log_entries)
        
        # Should create 2 sessions due to time gap
        assert len(sessions) >= 2
    
    def test_detect_error_session(self):
        """Test detection of error sessions"""
        base_time = datetime.now()
        
        log_entries = [
            self.create_log_entry(base_time, 'user_1', 'INFO'),
            self.create_log_entry(base_time + timedelta(seconds=10), 'user_1', 'ERROR'),
            self.create_log_entry(base_time + timedelta(seconds=20), 'user_1', 'INFO'),
        ]
        
        sessions = self.grouper.group_by_session(log_entries)
        
        assert len(sessions) > 0
        assert sessions[0]['has_errors'] is True
        assert sessions[0]['log_level_counts']['ERROR'] == 1
    
    def test_session_metadata(self):
        """Test session metadata extraction"""
        base_time = datetime.now()
        
        log_entries = [
            self.create_log_entry(base_time, 'user_1'),
            self.create_log_entry(base_time + timedelta(seconds=30), 'user_1'),
        ]
        
        sessions = self.grouper.group_by_session(log_entries)
        
        assert len(sessions) > 0
        session = sessions[0]
        
        assert 'start_time' in session
        assert 'end_time' in session
        assert 'duration_seconds' in session
        assert session['duration_seconds'] >= 30
        assert session['log_count'] == 2
    
    def test_analyze_sessions(self):
        """Test session analysis"""
        base_time = datetime.now()
        
        # Create sessions with and without errors
        sessions = [
            {
                'session_id': 'session_1',
                'has_errors': True,
                'duration_seconds': 60,
                'log_count': 10
            },
            {
                'session_id': 'session_2',
                'has_errors': False,
                'duration_seconds': 30,
                'log_count': 5
            }
        ]
        
        analysis = self.grouper.analyze_sessions(sessions)
        
        assert analysis['total_sessions'] == 2
        assert analysis['error_sessions'] == 1
        assert analysis['error_rate'] == 0.5
        assert analysis['avg_duration_seconds'] == 45
        assert analysis['avg_logs_per_session'] == 7.5
    
    def test_group_by_custom_field(self):
        """Test grouping by custom configured field"""
        from unittest.mock import patch
        base_time = datetime.now()
        
        # Mock the get_session_field to return 'token'
        with patch('auto_rca.sessionization.session_grouper.get_session_field') as mock_get:
            mock_get.return_value = 'token'
            
            log_entries = [
                {
                    'timestamp': base_time.isoformat(),
                    'token': 'token_1',
                    'log_level': 'INFO',
                    'message': 'Message 1'
                },
                {
                    'timestamp': (base_time + timedelta(seconds=10)).isoformat(),
                    'token': 'token_1',
                    'log_level': 'INFO',
                    'message': 'Message 2'
                },
                {
                    'timestamp': (base_time + timedelta(seconds=20)).isoformat(),
                    'token': 'token_2',
                    'log_level': 'INFO',
                    'message': 'Message 3'
                },
            ]
            
            sessions = self.grouper.group_by_session(log_entries)
            
            # Should create 2 sessions based on token
            assert len(sessions) == 2
            session_ids = [s['session_id'] for s in sessions]
            assert 'token_1' in session_ids
            assert 'token_2' in session_ids
    
    def test_group_by_custom_field_with_fallback(self):
        """Test grouping with custom field falling back to default fields"""
        from unittest.mock import patch
        base_time = datetime.now()
        
        # Mock the get_session_field to return 'order_id'
        with patch('auto_rca.sessionization.session_grouper.get_session_field') as mock_get:
            mock_get.return_value = 'order_id'
            
            log_entries = [
                {
                    'timestamp': base_time.isoformat(),
                    'order_id': 'order_1',
                    'log_level': 'INFO',
                    'message': 'Message 1'
                },
                {
                    'timestamp': (base_time + timedelta(seconds=10)).isoformat(),
                    # This log doesn't have order_id, should fall back to user_id
                    'user_id': 'user_1',
                    'log_level': 'INFO',
                    'message': 'Message 2'
                },
                {
                    'timestamp': (base_time + timedelta(seconds=20)).isoformat(),
                    'order_id': 'order_1',
                    'log_level': 'INFO',
                    'message': 'Message 3'
                },
            ]
            
            sessions = self.grouper.group_by_session(log_entries)
            
            # Should create 2 sessions: one for order_1, one for user_1
            assert len(sessions) == 2
            session_ids = [s['session_id'] for s in sessions]
            assert 'order_1' in session_ids
            assert 'user_1' in session_ids
    
    def test_group_by_custom_field_db_error_fallback(self):
        """Test grouping falls back to session_id when database access fails"""
        from unittest.mock import patch
        base_time = datetime.now()
        
        # Mock the get_session_field to raise an exception
        with patch('auto_rca.sessionization.session_grouper.get_session_field') as mock_get:
            mock_get.side_effect = Exception("Database error")
            
            log_entries = [
                {
                    'timestamp': base_time.isoformat(),
                    'session_id': 'session_1',
                    'log_level': 'INFO',
                    'message': 'Message 1'
                },
                {
                    'timestamp': (base_time + timedelta(seconds=10)).isoformat(),
                    'session_id': 'session_2',
                    'log_level': 'INFO',
                    'message': 'Message 2'
                },
            ]
            
            # Should still work and use session_id as fallback
            sessions = self.grouper.group_by_session(log_entries)
            
            assert len(sessions) == 2
            session_ids = [s['session_id'] for s in sessions]
            assert 'session_1' in session_ids
            assert 'session_2' in session_ids
