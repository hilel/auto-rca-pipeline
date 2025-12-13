"""Model training endpoints"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from auto_rca.api.schemas import TrainingResponse
from auto_rca.api.dependencies import get_pipeline

router = APIRouter(tags=["Training"])


@router.post(
    "/train",
    response_model=TrainingResponse,
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
        pipeline = get_pipeline()
        
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
