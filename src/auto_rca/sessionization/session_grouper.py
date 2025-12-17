"""Sessionization module for grouping log entries into user journeys/sessions"""

from typing import List, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict

from auto_rca.repositories import get_session_field


class SessionGrouper:
    """Groups log entries into sessions based on user/request IDs and timestamps"""
    
    def __init__(self, session_gap_seconds: int = 300):
        """
        Initialize session grouper
        
        Args:
            session_gap_seconds: Time gap in seconds to consider as session boundary (default: 5 minutes)
        """
        self.session_gap_seconds = session_gap_seconds
    
    def group_by_session(self, log_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Group log entries into sessions
        
        Args:
            log_entries: List of parsed log entries
            
        Returns:
            List of session objects containing grouped logs
        """
        if not log_entries:
            return []
        
        # Sort logs by timestamp
        sorted_logs = sorted(
            [log for log in log_entries if log.get('timestamp')],
            key=lambda x: x['timestamp']
        )
        
        # Group by identifiers (session_id, request_id, user_id, ip_address)
        identifier_groups = self._group_by_identifier(sorted_logs)
        
        # Further split by time gaps
        sessions = []
        for identifier, logs in identifier_groups.items():
            time_based_sessions = self._split_by_time_gap(logs)
            for session_logs in time_based_sessions:
                session = self._create_session(session_logs, identifier)
                sessions.append(session)
        
        return sessions
    
    def _group_by_identifier(self, log_entries: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group logs by session/request/user/IP identifiers"""
        groups = defaultdict(list)
        
        # Get the configured session field dynamically
        try:
            configured_field = get_session_field()
        except Exception:
            # Fallback to default if database access fails
            configured_field = 'session_id'
        
        for log in log_entries:
            # Priority: configured_field > session_id > request_id > user_id > ip_address
            identifier = (
                log.get(configured_field) or
                log.get('session_id') or
                log.get('request_id') or
                log.get('user_id') or
                log.get('ip_address') or
                'unknown'
            )
            groups[identifier].append(log)
        
        return groups
    
    def _split_by_time_gap(self, log_entries: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Split logs into separate sessions based on time gaps"""
        if not log_entries:
            return []
        
        sessions = []
        current_session = [log_entries[0]]
        
        for log in log_entries[1:]:
            prev_timestamp = datetime.fromisoformat(current_session[-1]['timestamp'])
            curr_timestamp = datetime.fromisoformat(log['timestamp'])
            
            time_diff = (curr_timestamp - prev_timestamp).total_seconds()
            
            if time_diff > self.session_gap_seconds:
                # Start new session
                sessions.append(current_session)
                current_session = [log]
            else:
                # Add to current session
                current_session.append(log)
        
        # Add the last session
        if current_session:
            sessions.append(current_session)
        
        return sessions
    
    def _create_session(self, log_entries: List[Dict[str, Any]], identifier: str) -> Dict[str, Any]:
        """Create a session object from grouped logs"""
        if not log_entries:
            return {}
        
        # Extract session metadata
        start_time = log_entries[0]['timestamp']
        end_time = log_entries[-1]['timestamp']
        
        # Calculate duration
        start_dt = datetime.fromisoformat(start_time)
        end_dt = datetime.fromisoformat(end_time)
        duration_seconds = (end_dt - start_dt).total_seconds()
        
        # Count log levels
        log_level_counts = defaultdict(int)
        for log in log_entries:
            level = log.get('log_level', 'UNKNOWN')
            log_level_counts[level] += 1
        
        # Determine if session has errors
        has_errors = (
            log_level_counts.get('ERROR', 0) > 0 or
            log_level_counts.get('CRITICAL', 0) > 0 or
            log_level_counts.get('FATAL', 0) > 0
        )
        
        # Extract exceptions
        exceptions = [
            log.get('exception')
            for log in log_entries
            if log.get('exception')
        ]
        
        # Collect unique HTTP methods and status codes
        http_methods = list(set(log.get('http_method') for log in log_entries if log.get('http_method')))
        status_codes = list(set(log.get('status_code') for log in log_entries if log.get('status_code')))
        
        return {
            'session_id': identifier,
            'start_time': start_time,
            'end_time': end_time,
            'duration_seconds': duration_seconds,
            'log_count': len(log_entries),
            'log_level_counts': dict(log_level_counts),
            'has_errors': has_errors,
            'exceptions': exceptions,
            'http_methods': http_methods,
            'status_codes': status_codes,
            'logs': log_entries,
            'user_journey': self._extract_user_journey(log_entries)
        }
    
    def _extract_user_journey(self, log_entries: List[Dict[str, Any]]) -> List[str]:
        """Extract a simplified user journey from logs"""
        journey = []
        
        for log in log_entries:
            # Create a simple journey step
            step_parts = []
            
            if log.get('http_method'):
                step_parts.append(log['http_method'])
            
            if log.get('message'):
                # Take first 100 chars of message
                msg = log['message'][:100]
                step_parts.append(msg)
            
            if log.get('log_level'):
                step_parts.append(f"[{log['log_level']}]")
            
            if step_parts:
                journey.append(' '.join(step_parts))
        
        return journey
    
    def analyze_sessions(self, sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze sessions to provide summary statistics
        
        Args:
            sessions: List of session objects
            
        Returns:
            Dictionary with session analytics
        """
        if not sessions:
            return {
                'total_sessions': 0,
                'error_sessions': 0,
                'avg_duration_seconds': 0,
                'avg_logs_per_session': 0
            }
        
        error_sessions = sum(1 for s in sessions if s.get('has_errors'))
        total_duration = sum(s.get('duration_seconds', 0) for s in sessions)
        total_logs = sum(s.get('log_count', 0) for s in sessions)
        
        return {
            'total_sessions': len(sessions),
            'error_sessions': error_sessions,
            'error_rate': error_sessions / len(sessions) if sessions else 0,
            'avg_duration_seconds': total_duration / len(sessions),
            'avg_logs_per_session': total_logs / len(sessions),
            'total_logs': total_logs
        }
