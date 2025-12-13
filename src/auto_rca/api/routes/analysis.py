"""Analysis endpoints"""

from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import tempfile
import shutil

from auto_rca.api.schemas import AnalysisRequest, AnalysisResponse
from auto_rca.api.dependencies import get_pipeline

router = APIRouter(tags=["Analysis"])


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
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
        pipeline = get_pipeline()
        
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


@router.post(
    "/analyze-upload",
    response_model=AnalysisResponse,
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
        pipeline = get_pipeline()
        
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
