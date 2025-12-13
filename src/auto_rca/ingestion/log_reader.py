"""Log ingestion module for reading logs from various sources"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any, Union
import xmltodict


class LogReader:
    """Reads and ingests logs from multiple formats (text, XML, JSON)"""
    
    def __init__(self):
        self.supported_formats = ['.txt', '.log', '.xml', '.json']
    
    def read_file(self, file_path: Union[str, Path]) -> List[Dict[str, Any]]:
        """
        Read logs from a file and return structured data
        
        Args:
            file_path: Path to the log file
            
        Returns:
            List of log entries as dictionaries
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        suffix = file_path.suffix.lower()
        
        if suffix not in self.supported_formats:
            raise ValueError(f"Unsupported file format: {suffix}. Supported: {self.supported_formats}")
        
        if suffix == '.json':
            return self._read_json(file_path)
        elif suffix == '.xml':
            return self._read_xml(file_path)
        else:  # .txt or .log
            return self._read_text(file_path)
    
    def _read_text(self, file_path: Path) -> List[Dict[str, Any]]:
        """Read plain text or log file"""
        logs = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line:  # Skip empty lines
                    logs.append({
                        'raw_text': line,
                        'line_number': line_num,
                        'source_file': str(file_path),
                        'format': 'text'
                    })
        return logs
    
    def _read_json(self, file_path: Path) -> List[Dict[str, Any]]:
        """Read JSON log file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle both single object and array of objects
        if isinstance(data, list):
            logs = data
        else:
            logs = [data]
        
        # Ensure each log has metadata
        for i, log in enumerate(logs):
            if not isinstance(log, dict):
                logs[i] = {'raw_text': str(log)}
            logs[i]['source_file'] = str(file_path)
            logs[i]['format'] = 'json'
        
        return logs
    
    def _read_xml(self, file_path: Path) -> List[Dict[str, Any]]:
        """Read XML log file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        # Parse XML to dictionary
        data = xmltodict.parse(xml_content)
        
        # Extract logs (assuming root element contains log entries)
        logs = []
        
        # Handle common XML structures
        if 'logs' in data and 'log' in data['logs']:
            log_entries = data['logs']['log']
            if not isinstance(log_entries, list):
                log_entries = [log_entries]
            logs = log_entries
        elif 'events' in data and 'event' in data['events']:
            log_entries = data['events']['event']
            if not isinstance(log_entries, list):
                log_entries = [log_entries]
            logs = log_entries
        else:
            # If no standard structure, wrap the entire parsed XML
            logs = [data]
        
        # Add metadata
        for log in logs:
            log['source_file'] = str(file_path)
            log['format'] = 'xml'
        
        return logs
    
    def read_directory(self, dir_path: Union[str, Path]) -> List[Dict[str, Any]]:
        """
        Read all supported log files from a directory
        
        Args:
            dir_path: Path to the directory
            
        Returns:
            List of all log entries from all files
        """
        dir_path = Path(dir_path)
        
        if not dir_path.is_dir():
            raise NotADirectoryError(f"Not a directory: {dir_path}")
        
        all_logs = []
        for file_path in dir_path.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in self.supported_formats:
                try:
                    logs = self.read_file(file_path)
                    all_logs.extend(logs)
                except Exception as e:
                    print(f"Warning: Failed to read {file_path}: {e}")
        
        return all_logs
