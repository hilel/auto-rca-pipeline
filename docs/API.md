# API Documentation

## Base URL

http://localhost:8000

## Interactive Documentation

Visit http://localhost:8000/docs for Swagger UI documentation.

## Architecture

The API is organized into modular route files for better maintainability:

```
src/auto_rca/api/
├── __init__.py          # Module exports
├── main.py              # FastAPI app initialization
├── schemas.py           # Pydantic request/response models
├── dependencies.py      # Shared dependencies (pipeline instance)
└── routes/
    ├── __init__.py      # Router exports
    ├── health.py        # Health check endpoints
    ├── processing.py    # Log upload and processing
    ├── training.py      # Model training
    ├── analysis.py      # Root cause analysis
    └── models.py        # Model management
```

## Key Endpoints

### Health Endpoints
- `GET /` - Root endpoint with API status
- `GET /health` - Health check

### Processing Endpoints
- `POST /upload-logs` - Upload and process logs

### Training Endpoints
- `POST /train` - Train the LSTM model

### Analysis Endpoints
- `POST /analyze` - Analyze logs for RCA
- `POST /analyze-upload` - Upload and analyze in one step

### Model Endpoints
- `POST /load-model` - Load a pre-trained model
- `GET /model-info` - Get model information

## Request/Response Schemas

All schemas are defined in `src/auto_rca/api/schemas.py`:

- `HealthResponse` - Health check response
- `AnalysisRequest` - Request for log analysis
- `AnalysisResponse` - Analysis results
- `UploadResponse` - File upload response
- `TrainingResponse` - Training results
- `ModelInfoResponse` - Model information
- `LoadModelResponse` - Model loading status

See the Swagger UI for detailed request/response schemas.
