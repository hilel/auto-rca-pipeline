# API Documentation

## Base URL

http://localhost:8000

## Interactive Documentation

Visit http://localhost:8000/docs for Swagger UI documentation.

**Learn more about API documentation:**
- [Swagger/OpenAPI Specification](https://swagger.io/specification/) - Industry standard for REST API documentation
- [FastAPI Documentation](https://fastapi.tiangolo.com/tutorial/) - Comprehensive FastAPI framework guide

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

**Why this architecture?**
- **Modularity**: Each route file handles a specific domain (health, processing, training, etc.), making the codebase easier to navigate and maintain
- **Separation of Concerns**: Business logic is separated from API routing, schemas define data contracts, and dependencies manage shared state
- **Scalability**: New endpoints can be added without affecting existing ones, and each module can be tested independently
- **RESTful Design**: Follows REST principles with clear resource-based endpoints and standard HTTP methods

**Learn more about API architecture:**
- [REST API Design Best Practices](https://stackoverflow.blog/2020/03/02/best-practices-for-rest-api-design/)
- [FastAPI Project Structure](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
- [Microservices Architecture](https://microservices.io/patterns/microservices.html)

---

## Detailed Endpoint Documentation

### Health Endpoints

#### `GET /` - Root Endpoint
**What it does:** Returns basic API information including version and model training status. This is the entry point for checking if the API is running.

**Why use it:** 
- Quick verification that the API server is responsive
- Check model readiness before making analysis requests
- Useful for load balancers and monitoring systems

**Response Example:**
```json
{
  "status": "running",
  "version": "0.1.0",
  "model_trained": true
}
```

**Learn more:**
- [REST API Versioning](https://restfulapi.net/versioning/)
- [Health Check Patterns](https://microservices.io/patterns/observability/health-check-api.html)

---

#### `GET /health` - Health Check
**What it does:** Provides a dedicated health check endpoint that returns the operational status of the API and its components.

**Why use it:**
- **Monitoring**: Used by monitoring tools (Prometheus, Datadog, etc.) to track API availability
- **Orchestration**: Kubernetes and Docker Swarm use health checks for container management
- **Load Balancing**: Load balancers route traffic only to healthy instances
- **DevOps**: Essential for CI/CD pipelines to verify deployment success

**Response Example:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "model_trained": true
}
```

**Best Practices:**
- Health checks should be lightweight and fast (< 100ms)
- Should verify critical dependencies (database, models, etc.)
- Return appropriate HTTP status codes (200 for healthy, 503 for unhealthy)

**Learn more:**
- [Health Check API Pattern](https://docs.microsoft.com/en-us/azure/architecture/patterns/health-endpoint-monitoring)
- [Kubernetes Liveness and Readiness Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)

---

### Processing Endpoints

#### `POST /upload-logs` - Upload and Process Logs
**What it does:** Accepts log files and processes them through the ingestion, parsing, and sessionization pipeline stages. This endpoint prepares logs for training or analysis but does NOT perform ML analysis.

**Why use it:**
- **Data Preparation**: Transform raw logs into structured, sessionized data
- **Validation**: Verify that logs can be parsed correctly before training
- **Preprocessing**: Clean and organize logs for downstream processing
- **Inspection**: See how many sessions are created from your log data

**Pipeline Stages Explained:**
1. **Ingestion**: Reads the uploaded file (supports .txt, .log, .json, .xml formats)
2. **Parsing**: Extracts structured fields (timestamp, log level, message, session ID, etc.)
3. **Sessionization**: Groups related log entries into sessions based on session IDs and time windows

**Supported File Formats:**
- `.txt`, `.log` - Plain text log files with standard log formatting
- `.json` - Structured JSON logs (one object per line or array of objects)
- `.xml` - XML formatted logs with structured elements

**Request:**
```bash
curl -X POST "http://localhost:8000/upload-logs" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/logs.txt"
```

**Response Example:**
```json
{
  "success": true,
  "message": "Logs processed successfully",
  "data": {
    "raw_log_count": 150,
    "session_count": 12
  }
}
```

**When to use:**
- Before training: To verify your logs are properly formatted
- Data exploration: To understand session distribution in your logs
- Troubleshooting: To test parsing rules on sample data

**Learn more:**
- [Log Processing Best Practices](https://www.datadoghq.com/blog/log-management-best-practices/)
- [FastAPI File Uploads](https://fastapi.tiangolo.com/tutorial/request-files/)
- [Sessionization in Log Analysis](https://www.elastic.co/blog/how-to-sessionize-logs)

---

### Training Endpoints

#### `POST /train` - Train LSTM Model
**What it does:** Trains a Long Short-Term Memory (LSTM) neural network on your log data to learn patterns that distinguish normal operations from errors and anomalies.

**Why use it:**
- **Pattern Learning**: The LSTM learns temporal patterns in log sequences to identify anomalies
- **Predictive Analysis**: Once trained, the model can predict error probability for new log sequences
- **Root Cause Detection**: Identifies which log patterns are most strongly associated with failures
- **Customization**: Train on your specific application logs for tailored analysis

**Training Process Explained:**

1. **Data Loading**: Reads logs from the specified path
2. **Preprocessing**: 
   - Parses logs into structured format
   - Groups into sessions
   - Extracts relevant features
3. **Vectorization**: 
   - Converts text to numerical sequences
   - Creates vocabulary from unique log tokens
   - Pads sequences to uniform length
4. **Model Training**:
   - Feeds sequences to LSTM network
   - Network learns to predict error likelihood
   - Adjusts weights through backpropagation
5. **Model Persistence**: Saves trained model and vectorizer to disk

**What is an LSTM?**
Long Short-Term Memory networks are a type of Recurrent Neural Network (RNN) designed to learn from sequential data. They excel at:
- Understanding temporal dependencies (what happened before affects what happens next)
- Maintaining context over long sequences
- Detecting patterns in time-series data like logs

**Request:**
```bash
curl -X POST "http://localhost:8000/train?log_path=/path/to/training/logs&epochs=50&batch_size=32"
```

**Query Parameters:**
- `log_path` (required): Path to training logs on the server
- `is_directory` (optional, default: false): Set to true if log_path contains multiple log files
- `epochs` (optional, default: 50): Number of complete passes through the training data
  - More epochs = longer training but potentially better learning
  - Too many epochs can lead to overfitting
- `batch_size` (optional, default: 32): Number of samples processed before model update
  - Larger batches = faster training but more memory usage
  - Smaller batches = more stable learning but slower

**Response Example:**
```json
{
  "success": true,
  "message": "Model trained successfully",
  "data": {
    "final_loss": 0.234,
    "final_accuracy": 0.92,
    "training_time": "2m 34s",
    "epochs_completed": 50,
    "model_paths": {
      "model": "data/models/lstm_model.h5",
      "vectorizer": "data/models/vectorizer.pkl"
    }
  }
}
```

**Training Tips:**
- Start with 10,000+ log entries for meaningful patterns
- Include both normal and error logs in training data (aim for 10-30% error rate)
- Training time scales with data size and epochs
- Monitor the loss value - it should decrease steadily
- If accuracy is low (< 70%), you may need more diverse training data

**When to use:**
- Initial setup: Train on representative sample of your application logs
- After log format changes: Retrain when your application's logging structure changes
- Periodic updates: Retrain monthly or quarterly with fresh data to adapt to new patterns
- Different environments: Train separate models for dev, staging, and production if they differ

**Learn more:**
- [Understanding LSTM Networks](https://colah.github.io/posts/2015-08-Understanding-LSTMs/)
- [Neural Networks and Deep Learning](http://neuralnetworksanddeeplearning.com/)
- [Keras LSTM Documentation](https://keras.io/api/layers/recurrent_layers/lstm/)
- [Training Neural Networks Best Practices](https://cs231n.github.io/neural-networks-3/)

---

### Analysis Endpoints

#### `POST /analyze` - Analyze Logs for Root Causes
**What it does:** Uses the trained LSTM model to analyze log files and identify root causes of errors, anomalies, and potential failures. This is the core endpoint for automated Root Cause Analysis (RCA).

**Why use it:**
- **Incident Response**: Quickly identify what went wrong during production incidents
- **Proactive Monitoring**: Detect anomalous patterns before they cause major issues
- **Pattern Recognition**: Discover recurring error patterns across sessions
- **Time Savings**: Automate the manual process of sifting through logs

**How RCA Works:**

1. **Log Processing**: Parses and sessionizes the input logs
2. **Sequence Vectorization**: Converts log text to numerical sequences using the trained vocabulary
3. **LSTM Prediction**: 
   - Model processes each session sequence
   - Outputs error probability (0.0 to 1.0) for each session
   - Higher probability indicates likely error or anomaly
4. **Root Cause Extraction**:
   - Identifies top exceptions and error messages
   - Finds common patterns in failed sessions
   - Ranks causes by frequency and correlation with errors
5. **Result Aggregation**: Compiles insights into actionable report

**Request:**
```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{"log_path": "/path/to/logs.txt", "is_directory": false}'
```

**Request Body:**
```json
{
  "log_path": "/path/to/logs/to/analyze.txt",
  "is_directory": false
}
```

**Response Example:**
```json
{
  "success": true,
  "message": "Analysis completed successfully",
  "data": {
    "total_sessions": 45,
    "error_sessions": 12,
    "error_rate": 0.267,
    "predictions": [
      {
        "session_id": "sess_001",
        "error_probability": 0.89,
        "classification": "error"
      },
      {
        "session_id": "sess_002",
        "error_probability": 0.12,
        "classification": "normal"
      }
    ],
    "top_root_causes": [
      {
        "exception": "NullPointerException",
        "count": 8,
        "affected_sessions": ["sess_001", "sess_003", "sess_007"]
      },
      {
        "exception": "ConnectionTimeoutException",
        "count": 4,
        "affected_sessions": ["sess_012", "sess_034"]
      }
    ],
    "common_patterns": [
      {
        "pattern": "Failed to connect to database",
        "frequency": 6,
        "correlation_with_errors": 0.95
      }
    ]
  }
}
```

**Interpreting Results:**
- **error_probability**: Ranges from 0.0 (definitely normal) to 1.0 (definitely error)
  - < 0.3: Normal operation
  - 0.3-0.7: Suspicious, investigate if unexpected
  - > 0.7: Likely error or anomaly
- **top_root_causes**: Ranked list of exceptions and errors found in failed sessions
- **common_patterns**: Recurring log messages associated with failures

**Prerequisites:**
- Model must be trained first (use `/train` endpoint)
- Log format should match training data format
- Logs must contain session identifiers or be sessionizable by time

**Use Cases:**
- **Production Incident Analysis**: "What caused the 3 AM outage?"
- **Pattern Recognition**: "Are there recurring issues we're missing?"
- **Anomaly Detection**: "Which sessions look abnormal?"
- **Predictive Failure Analysis**: "Which sessions are likely to fail next?"

**Learn more:**
- [Root Cause Analysis in Software](https://www.atlassian.com/incident-management/postmortem/root-cause-analysis)
- [Log Analysis Best Practices](https://www.sumologic.com/blog/log-analysis/)
- [Machine Learning for AIOps](https://research.google/pubs/pub43438/)

---

#### `POST /analyze-upload` - Upload and Analyze in One Step
**What it does:** Combines file upload and analysis into a single API call. This is a convenience endpoint that internally calls both the upload processing and analysis logic.

**Why use it:**
- **Convenience**: One-step operation instead of upload-then-analyze
- **Efficiency**: Reduces network round trips
- **Simplicity**: Easier integration for client applications
- **Temporary Analysis**: Analyze logs without persisting them on the server

**Workflow:**
1. Client uploads log file via multipart/form-data
2. Server saves file temporarily
3. Server processes logs (ingestion, parsing, sessionization)
4. Server runs LSTM analysis
5. Server returns results and cleans up temporary file

**Request:**
```bash
curl -X POST "http://localhost:8000/analyze-upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/production-logs.txt"
```

**Response Example:**
Same format as `/analyze` endpoint - see above.

**When to use:**
- **Ad-hoc Analysis**: Quickly analyze a log file without storing it
- **External Logs**: Analyze logs from client machines or remote systems
- **One-time Investigation**: When you don't need to keep the logs on the server
- **API Integration**: Simpler for clients that already have file uploads

**Comparison with `/analyze`:**
- `/analyze`: Requires logs already on server, good for batch processing or scheduled analysis
- `/analyze-upload`: Takes uploaded file, good for interactive or on-demand analysis

**Learn more:**
- [RESTful API Design for File Uploads](https://www.rfc-editor.org/rfc/rfc2388)
- [Multipart Form Data](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods/POST)

---

### Model Management Endpoints

#### `POST /load-model` - Load Pre-trained Model
**What it does:** Loads a previously trained LSTM model and its associated vectorizer from disk into memory, making them available for analysis operations.

**Why use it:**
- **Server Restart**: Restore model state after API server restart
- **Model Switching**: Load different models trained for different environments or applications
- **Deployment**: Load production-ready models without retraining
- **Persistence**: Use models trained in previous sessions

**How Models are Stored:**
Models are saved as two files:
1. **LSTM Model** (`lstm_model.h5`): Neural network weights and architecture in HDF5 format
2. **Vectorizer** (`vectorizer.pkl`): Vocabulary and text-to-sequence mappings in pickle format

Both files must be present in the same directory to load successfully.

**Request:**
```bash
# Load from default location (data/models/)
curl -X POST "http://localhost:8000/load-model"

# Load from custom location
curl -X POST "http://localhost:8000/load-model?model_dir=/path/to/custom/models"
```

**Query Parameters:**
- `model_dir` (optional, default: "data/models/"): Directory containing saved model files

**Response Example:**
```json
{
  "success": true,
  "message": "Model loaded successfully",
  "data": {
    "model_trained": true
  }
}
```

**When to use:**
- After server restart to restore model state
- When switching between different trained models
- In production environments where retraining is not desired
- When deploying pre-trained models to new environments

**Troubleshooting:**
- **File not found**: Verify model_dir path and that both .h5 and .pkl files exist
- **Corrupted model**: Model may be incompatible if trained with different library versions
- **Memory errors**: Large models require sufficient RAM

**Learn more:**
- [Keras Model Serialization](https://keras.io/api/models/model_saving_apis/)
- [Python Pickle Module](https://docs.python.org/3/library/pickle.html)
- [Model Deployment Best Practices](https://ml-ops.org/content/phase-three)

---

#### `GET /model-info` - Get Model Information
**What it does:** Retrieves detailed information about the currently loaded LSTM model, including architecture, hyperparameters, configuration, and training status.

**Why use it:**
- **Debugging**: Verify that the correct model is loaded
- **Documentation**: Generate reports on model configurations
- **Monitoring**: Track model versions in production
- **Validation**: Ensure model parameters match requirements

**Response Example:**
```json
{
  "success": true,
  "message": "Model information retrieved",
  "data": {
    "model_trained": true,
    "model_summary": {
      "total_params": 145678,
      "trainable_params": 145678,
      "layers": [
        {
          "name": "embedding",
          "type": "Embedding",
          "output_shape": [null, 100, 128]
        },
        {
          "name": "lstm_1",
          "type": "LSTM",
          "output_shape": [null, 100, 256],
          "units": 256
        },
        {
          "name": "lstm_2",
          "type": "LSTM",
          "output_shape": [null, 256],
          "units": 256
        },
        {
          "name": "dense_output",
          "type": "Dense",
          "output_shape": [null, 1],
          "activation": "sigmoid"
        }
      ]
    },
    "config": {
      "vocab_size": 10000,
      "embedding_dim": 128,
      "lstm_units": 256,
      "lstm_layers": 2,
      "sequence_length": 100
    }
  }
}
```

**Configuration Parameters Explained:**
- **vocab_size**: Number of unique tokens in the vocabulary (more = handles more diverse logs)
- **embedding_dim**: Dimensionality of word embeddings (higher = more expressive but slower)
- **lstm_units**: Number of LSTM units per layer (more = more capacity but requires more data)
- **lstm_layers**: Number of stacked LSTM layers (deeper = can learn more complex patterns)
- **sequence_length**: Maximum length of input sequences (longer = more context but slower)

**Model Architecture:**
1. **Embedding Layer**: Converts token IDs to dense vectors
2. **LSTM Layers**: Process sequences and learn temporal patterns
3. **Dense Output Layer**: Binary classification (error vs. normal) with sigmoid activation

**When to use:**
- Before analysis to verify model is loaded
- When documenting system architecture
- For troubleshooting unexpected model behavior
- When comparing different model versions

**Learn more:**
- [Understanding Neural Network Architectures](https://www.deeplearningbook.org/)
- [LSTM Architecture Explained](https://towardsdatascience.com/illustrated-guide-to-lstms-and-gru-s-a-step-by-step-explanation-44e9eb85bf21)
- [Keras Model Summary](https://keras.io/api/models/model/#summary-method)

---

## Request/Response Schemas

All schemas are defined in `src/auto_rca/api/schemas.py` using Pydantic models:

- `HealthResponse` - Health check response with status and version
- `AnalysisRequest` - Request for log analysis with path and options
- `AnalysisResponse` - Analysis results with predictions and root causes
- `UploadResponse` - File upload response with processing statistics
- `TrainingResponse` - Training results with metrics and model paths
- `ModelInfoResponse` - Model information with architecture and config
- `LoadModelResponse` - Model loading status

**Why Pydantic?**
- **Validation**: Automatically validates request data types and constraints
- **Documentation**: Schemas are automatically included in OpenAPI/Swagger docs
- **Type Safety**: Provides Python type hints for better IDE support
- **Serialization**: Handles JSON conversion and data transformation

See the Swagger UI at http://localhost:8000/docs for interactive schema exploration.

**Learn more:**
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Data Validation in APIs](https://nordicapis.com/data-validation-for-rest-apis/)
- [JSON Schema](https://json-schema.org/)

---

## Common Workflows

### 1. First-Time Setup and Training
```bash
# 1. Check API health
curl http://localhost:8000/health

# 2. Upload and process training logs
curl -X POST "http://localhost:8000/upload-logs" \
  -F "file=@training_logs.txt"

# 3. Train the model
curl -X POST "http://localhost:8000/train?log_path=/path/to/training_logs.txt&epochs=50"

# 4. Verify model is ready
curl http://localhost:8000/model-info
```

### 2. Production Analysis
```bash
# Load pre-trained model (after server restart)
curl -X POST "http://localhost:8000/load-model"

# Analyze production logs
curl -X POST "http://localhost:8000/analyze-upload" \
  -F "file=@production_incident.log"
```

### 3. Continuous Monitoring
```bash
# Scheduled analysis of daily logs
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{"log_path": "/var/logs/app/today.log", "is_directory": false}'
```

---

## Error Handling

All endpoints follow consistent error response format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Common HTTP Status Codes:**
- `200 OK`: Request succeeded
- `400 Bad Request`: Invalid input or model not trained
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error in request body
- `500 Internal Server Error`: Server-side error during processing

**Learn more:**
- [HTTP Status Codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status)
- [REST API Error Handling](https://blog.logrocket.com/rest-api-error-handling-best-practices/)

---

## Additional Resources

### FastAPI & REST APIs
- [FastAPI Official Documentation](https://fastapi.tiangolo.com/)
- [REST API Tutorial](https://restfulapi.net/)
- [HTTP Protocol Basics](https://developer.mozilla.org/en-US/docs/Web/HTTP)

### Machine Learning & LSTM
- [Deep Learning Specialization](https://www.coursera.org/specializations/deep-learning)
- [TensorFlow/Keras Documentation](https://www.tensorflow.org/guide/keras)
- [Understanding LSTM Networks](https://colah.github.io/posts/2015-08-Understanding-LSTMs/)

### Log Analysis & AIOps
- [AIOps Concepts](https://www.gartner.com/en/information-technology/glossary/aiops-artificial-intelligence-operations)
- [Log Management Best Practices](https://www.splunk.com/en_us/blog/learn/log-management.html)
- [Observability Engineering](https://www.oreilly.com/library/view/observability-engineering/9781492076438/)

### Production Deployment
- [Docker Documentation](https://docs.docker.com/)
- [Kubernetes Basics](https://kubernetes.io/docs/tutorials/kubernetes-basics/)
- [API Security Best Practices](https://owasp.org/www-project-api-security/)
