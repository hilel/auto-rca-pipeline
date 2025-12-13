"""Synthetic log data generator for testing and demonstration"""

import random
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
from pathlib import Path


class SyntheticLogGenerator:
    """Generates synthetic log data in various formats"""
    
    def __init__(self):
        self.log_levels = ['DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL']
        self.http_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
        self.status_codes = [200, 201, 400, 401, 403, 404, 500, 502, 503]
        self.endpoints = [
            '/api/users', '/api/products', '/api/orders', '/api/payments',
            '/api/login', '/api/logout', '/api/dashboard', '/api/search'
        ]
        self.exceptions = [
            'NullPointerException: Object reference not set',
            'DatabaseConnectionException: Connection timeout',
            'AuthenticationException: Invalid credentials',
            'ValidationException: Invalid input parameters',
            'TimeoutException: Request timeout after 30s',
            'OutOfMemoryException: Heap space exhausted'
        ]
        self.messages = [
            'Processing request',
            'Request completed successfully',
            'Starting transaction',
            'Committing transaction',
            'Rolling back transaction',
            'Validating input parameters',
            'Querying database',
            'Cache miss, fetching from database',
            'Cache hit',
            'Sending notification'
        ]
    
    def generate_text_logs(
        self,
        num_logs: int = 100,
        error_rate: float = 0.15
    ) -> List[str]:
        """
        Generate text format logs
        
        Args:
            num_logs: Number of log entries to generate
            error_rate: Probability of generating error logs
            
        Returns:
            List of log strings
        """
        logs = []
        start_time = datetime.now() - timedelta(hours=1)
        
        for i in range(num_logs):
            timestamp = start_time + timedelta(seconds=i * random.randint(1, 10))
            
            # Determine if this is an error log
            is_error = random.random() < error_rate
            
            if is_error:
                log_level = random.choice(['ERROR', 'CRITICAL'])
                message = random.choice(self.exceptions)
            else:
                log_level = random.choice(['DEBUG', 'INFO', 'WARN'])
                message = random.choice(self.messages)
            
            # Format: [timestamp] LEVEL message
            log = f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {log_level} - {message}"
            logs.append(log)
        
        return logs
    
    def generate_json_logs(
        self,
        num_logs: int = 100,
        error_rate: float = 0.15
    ) -> List[Dict[str, Any]]:
        """
        Generate JSON format logs
        
        Args:
            num_logs: Number of log entries to generate
            error_rate: Probability of generating error logs
            
        Returns:
            List of log dictionaries
        """
        logs = []
        start_time = datetime.now() - timedelta(hours=1)
        
        user_ids = [f"user_{i}" for i in range(1, 11)]
        session_ids = [f"session_{i}" for i in range(1, 6)]
        
        for i in range(num_logs):
            timestamp = start_time + timedelta(seconds=i * random.randint(1, 10))
            
            # Determine if this is an error log
            is_error = random.random() < error_rate
            
            log = {
                'timestamp': timestamp.isoformat(),
                'user_id': random.choice(user_ids),
                'session_id': random.choice(session_ids),
                'request_id': f"req_{i}",
                'ip_address': f"192.168.1.{random.randint(1, 255)}"
            }
            
            if is_error:
                log['level'] = random.choice(['ERROR', 'CRITICAL'])
                log['message'] = random.choice(self.exceptions)
                log['http_method'] = random.choice(self.http_methods)
                log['endpoint'] = random.choice(self.endpoints)
                log['status_code'] = random.choice([400, 401, 403, 404, 500, 502, 503])
            else:
                log['level'] = random.choice(['DEBUG', 'INFO', 'WARN'])
                log['message'] = random.choice(self.messages)
                log['http_method'] = random.choice(self.http_methods)
                log['endpoint'] = random.choice(self.endpoints)
                log['status_code'] = random.choice([200, 201, 204])
            
            logs.append(log)
        
        return logs
    
    def generate_xml_logs(
        self,
        num_logs: int = 100,
        error_rate: float = 0.15
    ) -> str:
        """
        Generate XML format logs
        
        Args:
            num_logs: Number of log entries to generate
            error_rate: Probability of generating error logs
            
        Returns:
            XML string
        """
        logs_xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<logs>']
        start_time = datetime.now() - timedelta(hours=1)
        
        user_ids = [f"user_{i}" for i in range(1, 11)]
        session_ids = [f"session_{i}" for i in range(1, 6)]
        
        for i in range(num_logs):
            timestamp = start_time + timedelta(seconds=i * random.randint(1, 10))
            
            # Determine if this is an error log
            is_error = random.random() < error_rate
            
            if is_error:
                log_level = random.choice(['ERROR', 'CRITICAL'])
                message = random.choice(self.exceptions)
                status_code = random.choice([400, 401, 403, 404, 500, 502, 503])
            else:
                log_level = random.choice(['DEBUG', 'INFO', 'WARN'])
                message = random.choice(self.messages)
                status_code = random.choice([200, 201, 204])
            
            log_xml = f"""  <log>
    <timestamp>{timestamp.isoformat()}</timestamp>
    <level>{log_level}</level>
    <message>{message}</message>
    <user_id>{random.choice(user_ids)}</user_id>
    <session_id>{random.choice(session_ids)}</session_id>
    <request_id>req_{i}</request_id>
    <http_method>{random.choice(self.http_methods)}</http_method>
    <endpoint>{random.choice(self.endpoints)}</endpoint>
    <status_code>{status_code}</status_code>
    <ip_address>192.168.1.{random.randint(1, 255)}</ip_address>
  </log>"""
            
            logs_xml.append(log_xml)
        
        logs_xml.append('</logs>')
        return '\n'.join(logs_xml)
    
    def save_logs(
        self,
        output_dir: str,
        num_logs: int = 100,
        error_rate: float = 0.15
    ) -> Dict[str, str]:
        """
        Generate and save logs in all formats
        
        Args:
            output_dir: Directory to save logs
            num_logs: Number of log entries per format
            error_rate: Probability of generating error logs
            
        Returns:
            Dictionary with paths to saved files
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate and save text logs
        text_logs = self.generate_text_logs(num_logs, error_rate)
        text_path = output_dir / 'sample_logs.txt'
        with open(text_path, 'w') as f:
            f.write('\n'.join(text_logs))
        
        # Generate and save JSON logs
        json_logs = self.generate_json_logs(num_logs, error_rate)
        json_path = output_dir / 'sample_logs.json'
        with open(json_path, 'w') as f:
            json.dump(json_logs, f, indent=2)
        
        # Generate and save XML logs
        xml_logs = self.generate_xml_logs(num_logs, error_rate)
        xml_path = output_dir / 'sample_logs.xml'
        with open(xml_path, 'w') as f:
            f.write(xml_logs)
        
        return {
            'text': str(text_path),
            'json': str(json_path),
            'xml': str(xml_path)
        }


def main():
    """Generate sample logs"""
    generator = SyntheticLogGenerator()
    
    # Generate logs with 15% error rate
    print("Generating synthetic logs...")
    paths = generator.save_logs(
        output_dir='data/raw',
        num_logs=200,
        error_rate=0.15
    )
    
    print("\nGenerated log files:")
    for format_type, path in paths.items():
        print(f"  {format_type}: {path}")


if __name__ == '__main__':
    main()
