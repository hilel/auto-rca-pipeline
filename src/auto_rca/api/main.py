"""FastAPI application for Auto-RCA Pipeline"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import tempfile
import shutil
from pathlib import Path

from ..pipeline import RCAPipeline
from ..config import settings

# Initialize FastAPI app
app = FastAPI(
    title="Auto-RCA Pipeline API",
    description="Automated Root Cause Analysis Pipeline using LSTM Deep Learning",
    version="0.1.0"
)

# Global pipeline instance
pipeline = RCAPipeline()


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    model_trained: bool


class AnalysisRequest(BaseModel):
    """Request model for log analysis"""
    log_path: str
    is_directory: bool = False


class AnalysisResponse(BaseModel):
    """Response model for log analysis"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint with API information"""
    return {
        "status": "running",
        "version": "0.1.0",
        "model_trained": pipeline.is_trained
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "model_trained": pipeline.is_trained
    }


@app.post("/upload-logs")
async def upload_logs(file: UploadFile = File(...)):
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
        
        return JSONResponse(content={
            "success": True,
            "message": "Logs processed successfully",
            "data": results
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/train")
async def train_model(
    background_tasks: BackgroundTasks,
    log_path: str,
    is_directory: bool = False,
    epochs: Optional[int] = None,
    batch_size: Optional[int] = None
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
        
        return JSONResponse(content={
            "success": True,
            "message": "Model trained successfully",
            "data": {
                **training_results,
                "model_paths": saved_paths
            }
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze", response_model=AnalysisResponse)
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


@app.post("/analyze-upload")
async def analyze_uploaded_logs(file: UploadFile = File(...)):
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


@app.post("/load-model")
async def load_model(model_dir: Optional[str] = None):
    """
    Load a pre-trained model
    
    Args:
        model_dir: Directory containing saved models
        
    Returns:
        Load status
    """
    try:
        pipeline.load_models(model_dir)
        
        return JSONResponse(content={
            "success": True,
            "message": "Model loaded successfully",
            "data": {
                "model_trained": pipeline.is_trained
            }
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/model-info")
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
