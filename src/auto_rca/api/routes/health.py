"""Health check endpoints"""

from fastapi import APIRouter

from auto_rca.api.schemas import HealthResponse
from auto_rca.api.dependencies import get_pipeline

router = APIRouter(tags=["Health"])


@router.get(
    "/",
    response_model=HealthResponse,
    summary="Root endpoint",
    description="Get API information and current status",
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
    description="Check if the API is healthy and operational",
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
