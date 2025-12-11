"""Log parsing module for converting unstructured logs to structured format"""

import re
from datetime import datetime
from typing import Dict, Any, List, Optional
from dateutil import parser as date_parser


class LogParser:
    """Parses logs into structured format with extracted fields"""
    
    # Common log patterns
    PATTERNS = {
        'timestamp': [
            r'\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?',
            r'\d{2}/[A-Za-z]{3}/\d{4}:\d{2}:\d{2}:\d{2}\s[+-]\d{4}',
            r'\[?\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}\]?',
        ],
        'log_level': r'\b(DEBUG|INFO|WARN|WARNING|ERROR|CRITICAL|FATAL|TRACE)\b',
        'ip_address': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
        'user_id': r'(?:user[_-]?id|uid|user)[:\s=]+([a-zA-Z0-9_-]+)',
        'request_id': r'(?:request[_-]?id|req[_-]?id|trace[_-]?id)[:\s=]+([a-zA-Z0-9_-]+)',
        'session_id': r'(?:session[_-]?id|sid)[:\s=]+([a-zA-Z0-9_-]+)',
        'http_method': r'\b(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\b',
        'status_code': r'\b[1-5]\d{2}\b',
        'exception': r'(?:Exception|Error):\s*(.+?)(?:\n|$)',
    }
    
    def __init__(self):
        self.compiled_patterns = {
            key: [re.compile(p, re.IGNORECASE) if isinstance(p, str) else [re.compile(pp, re.IGNORECASE) for pp in p]]
            for key, p in self.PATTERNS.items()
        }
    
    def parse_log(self, log_entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse a single log entry into structured format
        
        Args:
            log_entry: Raw log entry from ingestion
            
        Returns:
            Structured log entry with extracted fields
        """
        parsed = {
            'original': log_entry,
            'timestamp': None,
            'log_level': None,
            'message': None,
            'ip_address': None,
            'user_id': None,
            'request_id': None,
            'session_id': None,
            'http_method': None,
            'status_code': None,
            'exception': None,
            'metadata': {}
        }
        
        # Get the text content to parse
        if log_entry.get('format') == 'json':
            text = self._extract_json_fields(log_entry, parsed)
        elif log_entry.get('format') == 'xml':
            text = self._extract_xml_fields(log_entry, parsed)
        else:
            text = log_entry.get('raw_text', '')
        
        # Extract fields using regex patterns
        if text:
            self._extract_timestamp(text, parsed)
            self._extract_log_level(text, parsed)
            self._extract_identifiers(text, parsed)
            self._extract_http_info(text, parsed)
            self._extract_exception(text, parsed)
            
            # The message is the cleaned text
            parsed['message'] = text
        
        return parsed
    
    def _extract_json_fields(self, log_entry: Dict[str, Any], parsed: Dict[str, Any]) -> str:
        """Extract fields from JSON log entry"""
        # Try common JSON field names
        timestamp_fields = ['timestamp', 'time', 'datetime', '@timestamp', 'ts']
        level_fields = ['level', 'severity', 'log_level', 'loglevel']
        message_fields = ['message', 'msg', 'text', 'log']
        
        for field in timestamp_fields:
            if field in log_entry and log_entry[field]:
                parsed['timestamp'] = self._parse_timestamp(log_entry[field])
        
        for field in level_fields:
            if field in log_entry and log_entry[field]:
                parsed['log_level'] = str(log_entry[field]).upper()
        
        for field in message_fields:
            if field in log_entry and log_entry[field]:
                return str(log_entry[field])
        
        # If no message field found, return string representation
        return str(log_entry)
    
    def _extract_xml_fields(self, log_entry: Dict[str, Any], parsed: Dict[str, Any]) -> str:
        """Extract fields from XML log entry"""
        # Similar to JSON, try common XML field names
        if 'timestamp' in log_entry:
            parsed['timestamp'] = self._parse_timestamp(log_entry['timestamp'])
        
        if 'level' in log_entry:
            parsed['log_level'] = str(log_entry['level']).upper()
        
        if 'message' in log_entry:
            return str(log_entry['message'])
        
        return str(log_entry)
    
    def _extract_timestamp(self, text: str, parsed: Dict[str, Any]) -> None:
        """Extract timestamp from text"""
        if parsed['timestamp']:  # Already extracted from structured data
            return
        
        for pattern in self.PATTERNS['timestamp']:
            match = re.search(pattern, text)
            if match:
                try:
                    parsed['timestamp'] = self._parse_timestamp(match.group(0))
                    return
                except:
                    continue
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[str]:
        """Parse timestamp string to ISO format"""
        try:
            # Remove brackets if present
            timestamp_str = timestamp_str.strip('[]')
            dt = date_parser.parse(timestamp_str)
            return dt.isoformat()
        except:
            return None
    
    def _extract_log_level(self, text: str, parsed: Dict[str, Any]) -> None:
        """Extract log level from text"""
        if parsed['log_level']:  # Already extracted
            return
        
        match = re.search(self.PATTERNS['log_level'], text, re.IGNORECASE)
        if match:
            parsed['log_level'] = match.group(1).upper()
    
    def _extract_identifiers(self, text: str, parsed: Dict[str, Any]) -> None:
        """Extract various identifiers from text"""
        # IP Address
        match = re.search(self.PATTERNS['ip_address'], text)
        if match:
            parsed['ip_address'] = match.group(0)
        
        # User ID
        match = re.search(self.PATTERNS['user_id'], text, re.IGNORECASE)
        if match:
            parsed['user_id'] = match.group(1)
        
        # Request ID
        match = re.search(self.PATTERNS['request_id'], text, re.IGNORECASE)
        if match:
            parsed['request_id'] = match.group(1)
        
        # Session ID
        match = re.search(self.PATTERNS['session_id'], text, re.IGNORECASE)
        if match:
            parsed['session_id'] = match.group(1)
    
    def _extract_http_info(self, text: str, parsed: Dict[str, Any]) -> None:
        """Extract HTTP-related information"""
        # HTTP Method
        match = re.search(self.PATTERNS['http_method'], text)
        if match:
            parsed['http_method'] = match.group(1)
        
        # Status Code
        match = re.search(self.PATTERNS['status_code'], text)
        if match:
            parsed['status_code'] = int(match.group(0))
    
    def _extract_exception(self, text: str, parsed: Dict[str, Any]) -> None:
        """Extract exception information"""
        match = re.search(self.PATTERNS['exception'], text)
        if match:
            parsed['exception'] = match.group(1).strip()
    
    def parse_logs(self, log_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Parse multiple log entries
        
        Args:
            log_entries: List of raw log entries
            
        Returns:
            List of structured log entries
        """
        return [self.parse_log(entry) for entry in log_entries]
