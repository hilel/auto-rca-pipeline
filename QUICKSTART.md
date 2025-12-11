# Quick Start Guide

## Installation

```bash
# Clone the repository
git clone https://github.com/hilel/auto-rca-pipeline.git
cd auto-rca-pipeline

# Install dependencies
pip install -r requirements.txt
```

## 5-Minute Quick Start

### 1. Generate Sample Data

```bash
python src/cli.py generate --num-logs 200 --error-rate 0.15
```

### 2. Process Logs

```bash
python src/cli.py process data/raw --directory
```

### 3. Train Model

```bash
python src/cli.py train data/raw --directory --epochs 20
```

### 4. Analyze New Logs

```bash
# Generate test data
python src/cli.py generate --num-logs 100 --error-rate 0.25 --output-dir data/test

# Analyze it
python src/cli.py analyze data/test --directory
```

### 5. Start API Server

```bash
python src/cli.py serve
```

Then visit http://localhost:8000/docs for interactive API documentation.

## Complete Example

Run the comprehensive example:

```bash
python examples/complete_example.py
```

This demonstrates all 5 stages end-to-end with synthetic data.

## API Usage

### Using curl

```bash
# Health check
curl http://localhost:8000/health

# Train model
curl -X POST "http://localhost:8000/train?log_path=data/raw&is_directory=true&epochs=20"

# Analyze logs
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{"log_path": "data/test", "is_directory": true}'
```

### Using Python

```python
import requests

# Analyze uploaded file
with open('my_logs.json', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/analyze-upload',
        files={'file': f}
    )
    print(response.json())
```

## Python API

```python
from auto_rca.pipeline import RCAPipeline

# Initialize
pipeline = RCAPipeline()

# Process and train
results = pipeline.process_logs('data/raw', is_directory=True)
pipeline.train_model(results['sessions'], epochs=20)

# Save models
pipeline.save_models('data/models')

# Analyze new logs
analysis = pipeline.analyze_logs('data/test', is_directory=True)
print(analysis['root_cause_analysis'])
```

## Configuration

Edit `src/auto_rca/config.py` or set environment variables:

```bash
export LSTM_UNITS=256
export EPOCHS=100
export BATCH_SIZE=64
```

## Troubleshooting

### TensorFlow Warnings

Ignore CUDA warnings if running on CPU:

```bash
export TF_CPP_MIN_LOG_LEVEL=2
```

### Import Errors

Ensure you're running from the repository root:

```bash
cd /path/to/auto-rca-pipeline
python src/cli.py ...
```

Or add to PYTHONPATH:

```bash
export PYTHONPATH="${PYTHONPATH}:/path/to/auto-rca-pipeline/src"
```

## Next Steps

- Customize log parsing patterns in `src/auto_rca/parsing/log_parser.py`
- Adjust LSTM architecture in `src/auto_rca/ml_analysis/lstm_analyzer.py`
- Add custom log formats in `src/auto_rca/ingestion/log_reader.py`
- Integrate with your log management system
- Deploy as a containerized service
