"""Unit tests for log ingestion module"""

import pytest
from pathlib import Path
import tempfile
import json

from auto_rca.ingestion import LogReader


class TestLogReader:
    """Test cases for LogReader class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.reader = LogReader()
        self.temp_dir = tempfile.mkdtemp()
    
    def test_read_text_file(self):
        """Test reading text log file"""
        # Create a temporary text file
        text_content = """[2024-01-01 10:00:00] INFO - Application started
[2024-01-01 10:00:01] ERROR - Connection failed
[2024-01-01 10:00:02] DEBUG - Retrying connection"""
        
        temp_file = Path(self.temp_dir) / "test.log"
        temp_file.write_text(text_content)
        
        # Read the file
        logs = self.reader.read_file(temp_file)
        
        assert len(logs) == 3
        assert logs[0]['format'] == 'text'
        assert logs[0]['raw_text'] == '[2024-01-01 10:00:00] INFO - Application started'
        assert logs[0]['line_number'] == 1
    
    def test_read_json_file(self):
        """Test reading JSON log file"""
        # Create a temporary JSON file
        json_content = [
            {"timestamp": "2024-01-01T10:00:00", "level": "INFO", "message": "Started"},
            {"timestamp": "2024-01-01T10:00:01", "level": "ERROR", "message": "Failed"}
        ]
        
        temp_file = Path(self.temp_dir) / "test.json"
        temp_file.write_text(json.dumps(json_content))
        
        # Read the file
        logs = self.reader.read_file(temp_file)
        
        assert len(logs) == 2
        assert logs[0]['format'] == 'json'
        assert logs[0]['timestamp'] == "2024-01-01T10:00:00"
    
    def test_read_xml_file(self):
        """Test reading XML log file"""
        # Create a temporary XML file
        xml_content = """<?xml version="1.0"?>
<logs>
    <log>
        <timestamp>2024-01-01T10:00:00</timestamp>
        <level>INFO</level>
        <message>Started</message>
    </log>
    <log>
        <timestamp>2024-01-01T10:00:01</timestamp>
        <level>ERROR</level>
        <message>Failed</message>
    </log>
</logs>"""
        
        temp_file = Path(self.temp_dir) / "test.xml"
        temp_file.write_text(xml_content)
        
        # Read the file
        logs = self.reader.read_file(temp_file)
        
        assert len(logs) == 2
        assert logs[0]['format'] == 'xml'
    
    def test_unsupported_format(self):
        """Test error handling for unsupported formats"""
        temp_file = Path(self.temp_dir) / "test.pdf"
        temp_file.write_text("dummy content")
        
        with pytest.raises(ValueError, match="Unsupported file format"):
            self.reader.read_file(temp_file)
    
    def test_file_not_found(self):
        """Test error handling for non-existent files"""
        with pytest.raises(FileNotFoundError):
            self.reader.read_file("nonexistent.log")
