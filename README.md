# Auto-RCA Pipeline

Automated root cause analysis pipeline that transforms chaotic production logs into actionable insights using LSTM deep learning.

## 🚀 Overview

Auto-RCA Pipeline is a 5-stage ETL-A (Extract, Transform, Load, Analyze) system that automates the process of analyzing mixed-format logs (text/XML/JSON) to identify root causes of failures and anomalies. It uses LSTM (Long Short-Term Memory) neural networks to learn patterns from historical logs and predict potential issues in new log data.

### Key Features

- **Multi-Format Support**: Ingests text, XML, and JSON log formats
- **Intelligent Parsing**: Automatically extracts timestamps, log levels, user IDs, exceptions, and more
- **Session Correlation**: Groups logs into user journeys for contextual analysis
- **Deep Learning**: LSTM-based model for pattern recognition and anomaly detection
- **FastAPI Service**: RESTful API for real-time log analysis
- **Synthetic Data**: Built-in generator for testing and demonstration

## 📋 Architecture

The pipeline consists of 5 stages:

```
┌─────────────┐    ┌──────────┐    ┌────────────────┐    ┌───────────────┐    ┌─────────────┐
│ 1. Ingestion│ -> │2. Parsing│ -> │3.Sessionization│ -> │4.Vectorization│ -> │5. ML Analysis│
└─────────────┘    └──────────┘    └────────────────┘    └───────────────┘    └─────────────┘
     Multi-         Unstructured      Group Related         Text to             LSTM-based
    Format Logs  ->   Structured   ->   User Journeys  ->   Sequences     ->    Root Cause
   (TXT/XML/JSON)      Data              Sessions            Vectors            Detection
```

### Stage Details

1. **Ingestion**: Reads logs from files in multiple formats (text, XML, JSON)
2. **Parsing**: Extracts structured information (timestamps, levels, IDs, exceptions)
3. **Sessionization**: Groups logs into sessions based on user/request IDs and time gaps
4. **Vectorization**: Converts text into numerical sequences for ML processing
5. **ML Analysis**: LSTM model predicts error probability and identifies root causes

## 🛠️ Installation

### Prerequisites

- Python 3.9 or higher
- pip

### Setup

1. Clone the repository:
```bash
git clone https://github.com/hilel/auto-rca-pipeline.git
cd auto-rca-pipeline
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

**Note for Windows users**: If you encounter an error about Python 2.7, use one of these alternatives:
```powershell
# Option 1: Use python -m pip (recommended)
# -m runs pip as a module, ensuring it uses the correct Python interpreter
python -m pip install -r requirements.txt

# Option 2: Use the virtual environment's Python directly (no activation needed)
# Specifies the full path to the virtual environment's Python executable
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# Option 3: Activate virtual environment first
# Activates the .venv environment, then use pip normally
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Parameter explanations**:
- `-m pip`: Runs pip as a Python module using the current Python interpreter
- `-r requirements.txt`: Installs all packages listed in the requirements.txt file (`-r` means "requirements")

## 📖 Usage

### Command Line Interface

The CLI provides commands for all pipeline operations:

#### 1. Generate Synthetic Data

```bash
python src/cli.py generate --num-logs 200 --error-rate 0.15 --output-dir data/raw
```

#### 2. Process Logs

```bash
python src/cli.py process data/raw/sample_logs.json
python src/cli.py process data/raw --directory
```

#### 3. Train Model

```bash
python src/cli.py train data/raw --directory --epochs 50 --batch-size 32
```

#### 4. Analyze Logs

```bash
python src/cli.py analyze data/test --directory --model-dir data/models
```

#### 5. Start API Server

```bash
python src/cli.py serve --host 0.0.0.0 --port 8000
```

### Python API

```python
from auto_rca.pipeline import RCAPipeline

# Initialize pipeline
pipeline = RCAPipeline()

# Process logs
results = pipeline.process_logs('data/raw', is_directory=True)

# Train model
training_results = pipeline.train_model(
    sessions=results['sessions'],
    epochs=50
)

# Save models
pipeline.save_models('data/models')

# Analyze new logs
analysis = pipeline.analyze_logs('data/test', is_directory=True)
print(analysis['root_cause_analysis'])
```

### REST API

Start the server:
```bash
python src/cli.py serve
```

Access the interactive API documentation at `http://localhost:8000/docs`

#### API Endpoints

- `GET /health` - Health check
- `POST /upload-logs` - Upload and process logs
- `POST /train` - Train the model
- `POST /analyze` - Analyze logs for root causes
- `POST /analyze-upload` - Upload and analyze in one request
- `GET /model-info` - Get model information

Example API usage:

```bash
# Check health
curl http://localhost:8000/health

# Train model
curl -X POST "http://localhost:8000/train?log_path=data/raw&is_directory=true&epochs=10"

# Analyze logs
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{"log_path": "data/test", "is_directory": true}'
```

## 📚 Examples

### Complete End-to-End Example

```bash
python examples/complete_example.py
```

This example demonstrates:
1. Generating synthetic log data
2. Processing logs through all 5 stages
3. Training the LSTM model
4. Analyzing new logs for root causes
5. Displaying detailed results

### API Client Example

```bash
# First, start the server in one terminal
python src/cli.py serve

# Then, in another terminal, run the API example
python examples/api_example.py
```

## 🧪 Testing

Run tests (when available):
```bash
pytest tests/
```

## 📊 Model Configuration

Key parameters can be configured in `src/auto_rca/config.py` or via environment variables:

- `VOCAB_SIZE`: Size of vocabulary (default: 10000)
- `SEQUENCE_LENGTH`: Fixed sequence length (default: 100)
- `LSTM_UNITS`: LSTM units per layer (default: 128)
- `LSTM_LAYERS`: Number of LSTM layers (default: 2)
- `EMBEDDING_DIM`: Embedding dimension (default: 128)
- `DROPOUT_RATE`: Dropout rate (default: 0.2)
- `EPOCHS`: Training epochs (default: 50)
- `BATCH_SIZE`: Batch size (default: 32)

## 🎯 Current Status

**Proof of Concept** with synthetic data

### What's Implemented ✅
- ✅ 5-stage ETL-A pipeline
- ✅ Multi-format log ingestion (text/XML/JSON)
- ✅ Intelligent log parsing
- ✅ Session grouping and correlation
- ✅ Text vectorization for LSTM
- ✅ LSTM-based anomaly detection
- ✅ FastAPI RESTful service
- ✅ CLI interface
- ✅ Synthetic data generator
- ✅ Comprehensive examples

### Vision: Production-Ready Features 🚧
- ⏳ Real-time log streaming
- ⏳ ELK Stack integration (Elasticsearch, Logstash, Kibana)
- ⏳ SQL database integration
- ⏳ Interactive web UI for visualization
- ⏳ Real production log data support
- ⏳ Advanced model fine-tuning
- ⏳ Multi-model ensemble
- ⏳ Alert notifications
- ⏳ Dashboard with metrics

## 🤝 Contributing

Contributions are welcome! Areas for contribution:
- Add support for more log formats
- Improve parsing patterns
- Enhance ML model architecture
- Add integration tests
- Implement streaming capabilities
- Build web UI
- Add ELK/SQL connectors

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details

## 🔗 Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [TensorFlow/Keras Documentation](https://www.tensorflow.org/)
- [LSTM Networks Overview](https://colah.github.io/posts/2015-08-Understanding-LSTMs/)

## 💡 Use Cases

- Automated incident root cause analysis
- Log anomaly detection
- Pattern recognition in system logs
- Predictive failure analysis
- DevOps automation
- SRE tooling
