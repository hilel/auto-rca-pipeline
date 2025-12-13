"""FastAPI application for Auto-RCA Pipeline"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
import tempfile
import shutil
from pathlib import Path

from auto_rca.pipeline import RCAPipeline
from auto_rca.config import settings

# Initialize FastAPI app with enhanced OpenAPI metadata
app = FastAPI(
    title="Auto-RCA Pipeline API",
    description="""
## Automated Root Cause Analysis Pipeline using LSTM Deep Learning

Transform chaotic production logs into actionable insights with our 5-stage ETL-A pipeline:

1. **Ingestion** - Multi-format log reading (text/XML/JSON)
2. **Parsing** - Extract structured information from unstructured logs
3. **Sessionization** - Group logs into user journeys
4. **Vectorization** - Convert text to numerical sequences
5. **ML Analysis** - LSTM-based root cause detection

### Features
- Multi-format support (text, XML, JSON)
- Intelligent parsing with regex patterns
- Session correlation and grouping
- Deep learning anomaly detection
- Real-time analysis via REST API
    """,
    version="0.1.0",
    contact={
        "name": "Auto-RCA Team",
        "url": "https://github.com/hilel/auto-rca-pipeline",
        "email": "support@example.com"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    },
    openapi_tags=[
        {
            "name": "Health",
            "description": "Health check and status endpoints"
        },
        {
            "name": "Processing",
            "description": "Log processing and upload operations"
        },
        {
            "name": "Training",
            "description": "Model training operations"
        },
        {
            "name": "Analysis",
            "description": "Root cause analysis operations"
        },
        {
            "name": "Models",
            "description": "Model management and information"
        }
    ]
)

# Global pipeline instance
pipeline = RCAPipeline()


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


@app.get(
    "/",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Root endpoint",
    description="Get API information and current status",
    response_description="Current API status and model readiness"
)
async def root():
    """Root endpoint with API information"""
    return {
        "status": "running",
        "version": "0.1.0",
        "model_trained": pipeline.is_trained
    }


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Health check",
    description="Check if the API is healthy and operational",
    response_description="Health status including model training state"
)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "model_trained": pipeline.is_trained
    }


@app.post(
    "/upload-logs",
    response_model=UploadResponse,
    tags=["Processing"],
    summary="Upload and process logs",
    description="""
    Upload a log file for processing through the pipeline stages:
    1. Ingestion - Read the uploaded file
    2. Parsing - Extract structured information
    3. Sessionization - Group logs into sessions
    
    **Supported formats:** .txt, .log, .json, .xml
    
    **Note:** This endpoint does NOT perform ML analysis. Use `/analyze-upload` for analysis.
    """,
    response_description="Processing results with session statistics",
    responses={
        200: {
            "description": "Logs processed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Logs processed successfully",
                        "data": {
                            "raw_log_count": 150,
                            "session_count": 12
                        }
                    }
                }
            }
        },
        500: {
            "description": "Internal server error during processing",
            "content": {
                "application/json": {
                    "example": {"detail": "Error message"}
                }
            }
        }
    }
)
async def upload_logs(
    file: UploadFile = File(
        ...,
        description="Log file to upload (text, JSON, or XML format)"
    )
):
    """
    Upload a log file for processing
    
    Args:
        file: Log file to upload
        
    Returns:
        Processing results
    """
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            tmp_path = tmp_file.name
        
        # Process logs
        results = pipeline.process_logs(tmp_path, is_directory=False)
        
        # Clean up
        Path(tmp_path).unlink()
        
        return UploadResponse(
            success=True,
            message="Logs processed successfully",
            data=results
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/train",
    response_model=TrainingResponse,
    tags=["Training"],
    summary="Train LSTM model",
    description="""
    Train the LSTM model on provided logs for root cause analysis.
    
    **Process:**
    1. Load logs from the specified path
    2. Process through ingestion, parsing, and sessionization
    3. Vectorize sessions into numerical sequences
    4. Train LSTM neural network
    5. Save trained models to disk
    
    **Training time:** Depends on data size and epochs (typically 1-10 minutes for small datasets)
    
    **Note:** This will overwrite any existing trained models.
    """,
    response_description="Training results and saved model paths",
    responses={
        200: {"description": "Model trained successfully"},
        400: {"description": "Bad request - no sessions found in logs"},
        500: {"description": "Internal server error during training"}
    }
)
async def train_model(
    background_tasks: BackgroundTasks,
    log_path: str = Query(..., description="Path to training logs on the server"),
    is_directory: bool = Query(False, description="Set to true if log_path is a directory"),
    epochs: Optional[int] = Query(None, description="Number of training epochs (default: 50)"),
    batch_size: Optional[int] = Query(None, description="Batch size for training (default: 32)")
):
    """
    Train the LSTM model on provided logs
    
    Args:
        log_path: Path to training logs
        is_directory: Whether the path is a directory
        epochs: Number of training epochs
        batch_size: Batch size for training
        
    Returns:
        Training status
    """
    try:
        # Process logs
        process_results = pipeline.process_logs(log_path, is_directory)
        sessions = process_results['sessions']
        
        if not sessions:
            raise HTTPException(status_code=400, detail="No sessions found in logs")
        
        # Train model
        training_results = pipeline.train_model(
            sessions,
            epochs=epochs,
            batch_size=batch_size
        )
        
        # Save models
        saved_paths = pipeline.save_models()
        
        return TrainingResponse(
            success=True,
            message="Model trained successfully",
            data={
                **training_results,
                "model_paths": saved_paths
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/analyze",
    response_model=AnalysisResponse,
    tags=["Analysis"],
    summary="Analyze logs for root causes",
    description="""
    Analyze logs using the trained LSTM model to identify root causes of errors and anomalies.
    
    **Requirements:**
    - Model must be trained first (use `/train` endpoint or `/load-model`)
    
    **Returns:**
    - Error probability for each session
    - Top exceptions causing failures
    - Common error patterns
    - Session-level anomaly detection
    
    **Use cases:**
    - Production incident analysis
    - Pattern recognition in logs
    - Anomaly detection
    - Predictive failure analysis
    """,
    response_description="Root cause analysis results",
    responses={
        200: {"description": "Analysis completed successfully"},
        400: {"description": "Model not trained - train first"},
        500: {"description": "Internal server error during analysis"}
    }
)
async def analyze_logs(request: AnalysisRequest):
    """
    Analyze logs and provide root cause analysis
    
    Args:
        request: Analysis request with log path
        
    Returns:
        Root cause analysis results
    """
    try:
        if not pipeline.is_trained:
            raise HTTPException(
                status_code=400,
                detail="Model not trained. Please train the model first using /train endpoint"
            )
        
        # Analyze logs
        results = pipeline.analyze_logs(request.log_path, request.is_directory)
        
        return {
            "success": True,
            "message": "Analysis completed successfully",
            "data": results
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/analyze-upload",
    response_model=AnalysisResponse,
    tags=["Analysis"],
    summary="Upload and analyze logs",
    description="""
    Upload a log file and analyze it for root causes in one operation.
    
    **Combines:** `/upload-logs` + `/analyze` into a single endpoint
    
    **Requirements:**
    - Model must be trained first
    
    **Supported formats:** .txt, .log, .json, .xml
    """,
    response_description="Analysis results with root cause insights",
    responses={
        200: {"description": "Analysis completed successfully"},
        400: {"description": "Model not trained"},
        500: {"description": "Internal server error"}
    }
)
async def analyze_uploaded_logs(
    file: UploadFile = File(
        ...,
        description="Log file to analyze (text, JSON, or XML format)"
    )
):
    """
    Upload and analyze a log file
    
    Args:
        file: Log file to analyze
        
    Returns:
        Root cause analysis results
    """
    try:
        if not pipeline.is_trained:
            raise HTTPException(
                status_code=400,
                detail="Model not trained. Please train the model first using /train endpoint"
            )
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            tmp_path = tmp_file.name
        
        # Analyze logs
        results = pipeline.analyze_logs(tmp_path, is_directory=False)
        
        # Clean up
        Path(tmp_path).unlink()
        
        return JSONResponse(content={
            "success": True,
            "message": "Analysis completed successfully",
            "data": results
        })
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/load-model",
    response_model=LoadModelResponse,
    tags=["Models"],
    summary="Load pre-trained model",
    description="""
    Load a previously trained model from disk.
    
    **Use cases:**
    - Load models after server restart
    - Switch between different trained models
    - Use pre-trained models without retraining
    
    **Default location:** `data/models/`
    """,
    response_description="Load status",
    responses={
        200: {"description": "Model loaded successfully"},
        500: {"description": "Failed to load model - file not found or corrupted"}
    }
)
async def load_model(
    model_dir: Optional[str] = Query(
        None,
        description="Directory containing saved models (default: data/models/)"
    )
):
    """
    Load a pre-trained model
    
    Args:
        model_dir: Directory containing saved models
        
    Returns:
        Load status
    """
    try:
        pipeline.load_models(model_dir)
        
        return LoadModelResponse(
            success=True,
            message="Model loaded successfully",
            data={
                "model_trained": pipeline.is_trained
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/model-info",
    response_model=ModelInfoResponse,
    tags=["Models"],
    summary="Get model information",
    description="""
    Get detailed information about the current LSTM model.
    
    **Returns:**
    - Model architecture summary
    - Configuration parameters
    - Training status
    - Model hyperparameters
    """,
    response_description="Model configuration and status",
    responses={
        200: {"description": "Model information retrieved successfully"},
        500: {"description": "Error retrieving model information"}
    }
)
async def get_model_info():
    """Get information about the current model"""
    try:
        if not pipeline.analyzer.model:
            return JSONResponse(content={
                "success": True,
                "message": "No model loaded",
                "data": {
                    "model_trained": False
                }
            })
        
        model_summary = pipeline.analyzer.get_model_summary()
        
        return JSONResponse(content={
            "success": True,
            "message": "Model information retrieved",
            "data": {
                "model_trained": pipeline.is_trained,
                "model_summary": model_summary,
                "config": {
                    "vocab_size": settings.vocab_size,
                    "embedding_dim": settings.embedding_dim,
                    "lstm_units": settings.lstm_units,
                    "lstm_layers": settings.lstm_layers,
                    "sequence_length": settings.sequence_length
                }
            }
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "auto_rca.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload
    )
