"""Model management endpoints"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional

from auto_rca.api.schemas import ModelInfoResponse, LoadModelResponse
from auto_rca.api.dependencies import get_pipeline
from auto_rca.config import settings

router = APIRouter(tags=["Models"])


@router.post(
    "/load-model",
    response_model=LoadModelResponse,
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
        pipeline = get_pipeline()
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


@router.get(
    "/model-info",
    response_model=ModelInfoResponse,
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
        pipeline = get_pipeline()
        
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
