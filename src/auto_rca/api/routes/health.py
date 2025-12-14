"""Health check endpoints"""

from fastapi import APIRouter

from auto_rca.api.schemas import HealthResponse
from auto_rca.api.dependencies import get_pipeline

router = APIRouter(tags=["Health"])


@router.get(
    "/",
    response_model=HealthResponse,
    summary="Root endpoint",
    description="""Get API information and current status.
    
    **Machine Learning Context:**
    The `model_trained` field indicates whether the LSTM (Long Short-Term Memory) neural network
    has been trained and is ready to perform root cause analysis. An untrained model cannot make
    predictions and will return errors if analysis endpoints are called.
    
    **Learn More:**
    - [LSTM Networks Explained](https://colah.github.io/posts/2015-08-Understanding-LSTMs/)
    - [Neural Network Training Basics](https://cs231n.github.io/neural-networks-3/)
    """,
    response_description="Current API status and model readiness"
)
async def root():
    """Root endpoint with API information"""
    pipeline = get_pipeline()
    return {
        "status": "running",
        "version": "0.1.0",
        "model_trained": pipeline.is_trained
    }


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="""Check if the API is healthy and operational.
    
    **ML Model State:**
    This endpoint verifies that the machine learning pipeline is properly initialized and reports
    whether the LSTM model is loaded in memory and ready for inference. The model state persists
    across requests but is lost on server restart (use `/load-model` to restore).
    
    **Learn More:**
    - [ML Model Serving Best Practices](https://ml-ops.org/content/phase-three)
    - [Health Checks in ML Systems](https://martinfowler.com/articles/cd4ml.html)
    """,
    response_description="Health status including model training state"
)
async def health_check():
    """Health check endpoint"""
    pipeline = get_pipeline()
    return {
        "status": "healthy",
        "version": "0.1.0",
        "model_trained": pipeline.is_trained
    }
