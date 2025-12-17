"""API routes module"""

from .health import router as health_router
from .processing import router as processing_router
from .training import router as training_router
from .analysis import router as analysis_router
from .models import router as models_router
from .configuration import router as configuration_router

__all__ = [
    "health_router",
    "processing_router",
    "training_router",
    "analysis_router",
    "models_router",
    "configuration_router",
]
