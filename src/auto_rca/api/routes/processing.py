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
    description="""Upload a log file for preprocessing and feature engineering.
    
    **ML Pipeline Stages:**
    
    1. **Ingestion** - Raw data loading from multiple formats (.txt, .log, .json, .xml)
    2. **Parsing** - Feature extraction: timestamps, log levels, messages, session IDs, exceptions
    3. **Sessionization** - Temporal grouping of related events (critical for sequence learning)
    
    **Why Sessionization Matters for ML:**
    LSTM networks learn from sequences, not individual log lines. Sessionization creates meaningful
    sequences by grouping related logs based on session identifiers and temporal proximity. This
    transforms unstructured log streams into structured sequential data that the LSTM can process.
    
    **Feature Engineering:**
    The parsing stage extracts structured features that will later be vectorized (converted to numbers)
    for neural network input. Key features include:
    - Log level (INFO, WARN, ERROR) - indicates severity
    - Exception types - strong predictors of failures
    - Message patterns - learned through embeddings
    - Temporal order - preserved for sequence learning
    
    **Note:** This endpoint performs data preprocessing only, not ML inference. Use `/analyze-upload`
    for end-to-end analysis with model predictions.
    
    **Learn More:**
    - [Feature Engineering for ML](https://developers.google.com/machine-learning/crash-course/representation/feature-engineering)
    - [Time Series Preprocessing](https://machinelearningmastery.com/time-series-data-preparation/)
    - [Log Sessionization Techniques](https://www.elastic.co/blog/how-to-sessionize-logs)
    - [Sequence Data for RNNs](https://www.tensorflow.org/guide/keras/rnn)
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
