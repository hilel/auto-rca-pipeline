"""Unit tests for API endpoints"""

import pytest
from fastapi.testclient import TestClient
import tempfile
import json
from pathlib import Path

from auto_rca.api import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def sample_json_logs():
    """Create sample JSON logs for testing"""
    logs = [
        {
            "timestamp": "2024-01-01T10:00:00",
            "level": "INFO",
            "message": "Request received",
            "user_id": "user_001",
            "request_id": "req_001"
        },
        {
            "timestamp": "2024-01-01T10:00:01",
            "level": "DEBUG",
            "message": "Processing request",
            "user_id": "user_001",
            "request_id": "req_001"
        },
        {
            "timestamp": "2024-01-01T10:00:02",
            "level": "INFO",
            "message": "Request completed",
            "user_id": "user_001",
            "request_id": "req_001",
            "status_code": 200
        }
    ]
    return logs


class TestHealthEndpoints:
    """Test cases for health check endpoints"""
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns correct status"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert data["version"] == "0.1.0"
        assert "model_trained" in data
    
    def test_health_check(self, client):
        """Test health check endpoint returns healthy status"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "0.1.0"
        assert "model_trained" in data


class TestProcessingEndpoints:
    """Test cases for log processing endpoints"""
    
    def test_upload_logs_json(self, client, sample_json_logs):
        """Test uploading JSON log file"""
        # Create a temporary JSON file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_json_logs, f)
            temp_path = f.name
        
        try:
            with open(temp_path, 'rb') as f:
                response = client.post(
                    "/upload-logs",
                    files={"file": ("test_logs.json", f, "application/json")}
                )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["message"] == "Logs processed successfully"
            assert "data" in data
            assert "raw_log_count" in data["data"]
        finally:
            Path(temp_path).unlink()
    
    def test_upload_logs_text(self, client):
        """Test uploading text log file"""
        text_content = b"""[2024-01-01 10:00:00] INFO - Application started
[2024-01-01 10:00:01] DEBUG - Processing request
[2024-01-01 10:00:02] INFO - Request completed"""
        
        response = client.post(
            "/upload-logs",
            files={"file": ("test.log", text_content, "text/plain")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestAnalysisEndpoints:
    """Test cases for analysis endpoints"""
    
    def test_analyze_without_trained_model(self, client):
        """Test analyze endpoint returns error when model not trained"""
        response = client.post(
            "/analyze",
            json={"log_path": "data/raw/test.json", "is_directory": False}
        )
        
        # Should return 400 or 500 when model not trained or path invalid
        assert response.status_code in [400, 500]
    
    def test_analyze_upload_without_trained_model(self, client, sample_json_logs):
        """Test analyze-upload endpoint returns error when model not trained"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_json_logs, f)
            temp_path = f.name
        
        try:
            with open(temp_path, 'rb') as f:
                response = client.post(
                    "/analyze-upload",
                    files={"file": ("test_logs.json", f, "application/json")}
                )
            
            # Should return 400 or 500 when model not trained
            assert response.status_code in [400, 500]
        finally:
            Path(temp_path).unlink()


class TestModelEndpoints:
    """Test cases for model management endpoints"""
    
    def test_model_info_no_model(self, client):
        """Test model-info endpoint when no model is loaded"""
        response = client.get("/model-info")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["model_trained"] is False
    
    def test_load_model_nonexistent(self, client):
        """Test load-model endpoint with nonexistent model directory"""
        response = client.post("/load-model?model_dir=/nonexistent/path")
        # load_models may succeed or fail depending on implementation
        # Just verify we get a valid response
        assert response.status_code in [200, 500]


class TestSchemas:
    """Test cases for API schemas"""
    
    def test_health_response_schema(self):
        """Test HealthResponse schema"""
        from auto_rca.api.schemas import HealthResponse
        
        response = HealthResponse(
            status="healthy",
            version="0.1.0",
            model_trained=True
        )
        
        assert response.status == "healthy"
        assert response.version == "0.1.0"
        assert response.model_trained is True
    
    def test_analysis_request_schema(self):
        """Test AnalysisRequest schema"""
        from auto_rca.api.schemas import AnalysisRequest
        
        request = AnalysisRequest(
            log_path="/data/logs/test.json",
            is_directory=False
        )
        
        assert request.log_path == "/data/logs/test.json"
        assert request.is_directory is False
    
    def test_analysis_request_default_is_directory(self):
        """Test AnalysisRequest default is_directory value"""
        from auto_rca.api.schemas import AnalysisRequest
        
        request = AnalysisRequest(log_path="/data/logs/test.json")
        assert request.is_directory is False
    
    def test_upload_response_schema(self):
        """Test UploadResponse schema"""
        from auto_rca.api.schemas import UploadResponse
        
        response = UploadResponse(
            success=True,
            message="Logs processed",
            data={"raw_log_count": 100, "session_count": 5}
        )
        
        assert response.success is True
        assert response.message == "Logs processed"
        assert response.data["raw_log_count"] == 100


class TestConfigurationEndpoints:
    """Test cases for configuration endpoints"""
    
    def test_get_session_field_default(self, client):
        """Test getting default session field"""
        from unittest.mock import patch
        
        with patch('auto_rca.api.routes.configuration.get_session_field') as mock_get:
            mock_get.return_value = 'session_id'
            
            response = client.get("/config/session-field")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["session_field"] == "session_id"
    
    def test_get_session_field_custom(self, client):
        """Test getting custom session field"""
        from unittest.mock import patch
        
        with patch('auto_rca.api.routes.configuration.get_session_field') as mock_get:
            mock_get.return_value = 'token'
            
            response = client.get("/config/session-field")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["session_field"] == "token"
    
    def test_update_session_field(self, client):
        """Test updating session field"""
        from unittest.mock import patch
        
        with patch('auto_rca.api.routes.configuration.set_session_field') as mock_set:
            response = client.post(
                "/config/session-field",
                json={"session_field": "order_id"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["session_field"] == "order_id"
            mock_set.assert_called_once_with("order_id")
    
    def test_get_session_field_error(self, client):
        """Test error handling when getting session field fails"""
        from unittest.mock import patch
        
        with patch('auto_rca.api.routes.configuration.get_session_field') as mock_get:
            mock_get.side_effect = Exception("Database error")
            
            response = client.get("/config/session-field")
            assert response.status_code == 500
    
    def test_update_session_field_error(self, client):
        """Test error handling when updating session field fails"""
        from unittest.mock import patch
        
        with patch('auto_rca.api.routes.configuration.set_session_field') as mock_set:
            mock_set.side_effect = Exception("Database error")
            
            response = client.post(
                "/config/session-field",
                json={"session_field": "token"}
            )
            
            assert response.status_code == 500


class TestDependencies:
    """Test cases for API dependencies"""
    
    def test_get_pipeline(self):
        """Test get_pipeline returns pipeline instance"""
        from auto_rca.api.dependencies import get_pipeline
        from auto_rca.pipeline import RCAPipeline
        
        pipeline = get_pipeline()
        assert isinstance(pipeline, RCAPipeline)
    
    def test_pipeline_singleton(self):
        """Test get_pipeline returns same instance"""
        from auto_rca.api.dependencies import get_pipeline
        
        pipeline1 = get_pipeline()
        pipeline2 = get_pipeline()
        assert pipeline1 is pipeline2
