"""Log processing endpoints"""

from fastapi import APIRouter, File, UploadFile, HTTPException
from pathlib import Path
import tempfile
import shutil

from auto_rca.api.schemas import UploadResponse
from auto_rca.api.dependencies import get_pipeline

router = APIRouter(tags=["Processing"])


@router.post(
    "/upload-logs",
    response_model=UploadResponse,
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
        pipeline = get_pipeline()
        
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
