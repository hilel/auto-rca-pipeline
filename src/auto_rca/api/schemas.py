"""Pydantic models for API request/response schemas"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any


class HealthResponse(BaseModel):
    """Health check response"""
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra={
            "example": {
                "status": "healthy",
                "version": "0.1.0",
                "model_trained": True
            }
        }
    )
    
    status: str = Field(..., description="Current status of the API service")
    version: str = Field(..., description="API version")
    model_trained: bool = Field(..., description="Whether the LSTM model is trained and ready")


class AnalysisRequest(BaseModel):
    """Request model for log analysis"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "log_path": "data/raw/sample_logs.json",
                "is_directory": False
            }
        }
    )
    
    log_path: str = Field(..., description="Path to log file or directory on the server")
    is_directory: bool = Field(False, description="Set to true if log_path points to a directory")


class AnalysisResponse(BaseModel):
    """Response model for log analysis"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Analysis completed successfully",
                "data": {
                    "session_count": 42,
                    "root_cause_analysis": {
                        "total_analyzed": 42,
                        "error_sessions_count": 8,
                        "error_rate": 0.19,
                        "top_exceptions": [
                            ["DatabaseConnectionException: Connection timeout", 3],
                            ["NullPointerException: Object reference not set", 2]
                        ]
                    }
                }
            }
        }
    )
    
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Human-readable message about the operation")
    data: Optional[Dict[str, Any]] = Field(None, description="Analysis results and detailed data")


class UploadResponse(BaseModel):
    """Response model for file upload operations"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Logs processed successfully",
                "data": {
                    "raw_log_count": 150,
                    "parsed_log_count": 148,
                    "session_count": 12,
                    "session_statistics": {
                        "total_sessions": 12,
                        "error_sessions": 3,
                        "error_rate": 0.25
                    }
                }
            }
        }
    )
    
    success: bool = Field(..., description="Whether the upload was successful")
    message: str = Field(..., description="Status message")
    data: Dict[str, Any] = Field(..., description="Processing results including session statistics")


class TrainingResponse(BaseModel):
    """Response model for model training operations"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Model trained successfully",
                "data": {
                    "training_samples": 1000,
                    "epochs_trained": 50,
                    "metrics": {
                        "final_loss": 0.2134,
                        "final_accuracy": 0.9456,
                        "final_val_loss": 0.2567,
                        "final_val_accuracy": 0.9234
                    },
                    "model_paths": {
                        "vectorizer": "data/models/vectorizer.pkl",
                        "lstm_model": "data/models/lstm_model.h5"
                    }
                }
            }
        }
    )
    
    success: bool = Field(..., description="Whether training was successful")
    message: str = Field(..., description="Training status message")
    data: Dict[str, Any] = Field(..., description="Training results and model paths")


class ModelInfoResponse(BaseModel):
    """Response model for model information"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Model information retrieved",
                "data": {
                    "model_trained": True,
                    "config": {
                        "vocab_size": 10000,
                        "embedding_dim": 128,
                        "lstm_units": 128,
                        "lstm_layers": 2,
                        "sequence_length": 100
                    }
                }
            }
        }
    )
    
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Status message")
    data: Dict[str, Any] = Field(..., description="Model configuration and status")


class LoadModelResponse(BaseModel):
    """Response model for model loading operations"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Model loaded successfully",
                "data": {
                    "model_trained": True
                }
            }
        }
    )
    
    success: bool = Field(..., description="Whether the load was successful")
    message: str = Field(..., description="Load status message")
    data: Dict[str, Any] = Field(..., description="Model status after loading")
