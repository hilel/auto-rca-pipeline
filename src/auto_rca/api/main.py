"""FastAPI application for Auto-RCA Pipeline"""

from fastapi import FastAPI

from auto_rca.config import settings
from auto_rca.database import init_db
from auto_rca.api.routes import (
    health_router,
    processing_router,
    training_router,
    analysis_router,
    models_router,
    configuration_router,
)

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
        },
        {
            "name": "Configuration",
            "description": "Configuration management endpoints"
        }
    ]
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database and other startup tasks"""
    init_db()

# Include routers
app.include_router(health_router)
app.include_router(processing_router)
app.include_router(training_router)
app.include_router(analysis_router)
app.include_router(models_router)
app.include_router(configuration_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "auto_rca.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload
    )
