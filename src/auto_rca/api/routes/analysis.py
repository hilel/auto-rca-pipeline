"""Analysis endpoints"""

from fastapi import APIRouter, File, UploadFile, HTTPException
from pathlib import Path
import tempfile
import shutil

from auto_rca.api.schemas import AnalysisRequest, AnalysisResponse
from auto_rca.api.dependencies import get_pipeline

router = APIRouter(tags=["Analysis"])


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    summary="Analyze logs for root causes",
    description="""Perform ML-powered root cause analysis using trained LSTM model.
    
    **Machine Learning Inference Pipeline:**
    
    1. **Data Preprocessing:**
       - Parse raw logs into structured format
       - Group into sessions (same as training preprocessing)
       - Extract features: timestamps, levels, messages, exceptions
    
    2. **Text Vectorization:**
       - Tokenize log messages using trained vocabulary
       - Convert tokens to numerical sequences
       - Pad sequences to match training length (sequence_length parameter)
       - Unknown tokens → UNK token (handles previously unseen words)
    
    3. **LSTM Inference (Forward Pass):**
       - Feed vectorized sequences through embedding layer
       - Process through trained LSTM layers
         - Each LSTM cell maintains hidden state (context)
         - Cell state carries information across the sequence
       - Output layer produces probability via sigmoid activation
    
    4. **Probability Interpretation:**
       - Output: Float between 0.0 (normal) and 1.0 (error)
       - Model learned decision boundary during training (typically ~0.5)
       - Calibration: Higher probability = higher confidence in error prediction
    
    5. **Root Cause Extraction:**
       - Analyze high-probability error sessions
       - Extract common patterns using statistical analysis:
         - Exception frequency (which errors appear most)
         - Temporal correlation (when errors occur together)
         - Message similarity (clustering of error messages)
       - Rank causes by impact and frequency
    
    **Anomaly Detection:**
    The LSTM doesn't just classify known errors - it detects anomalies. If a session has unusual
    patterns (different from training data), the model may flag it as suspicious even without
    explicit error labels. This is because the model learned what "normal" looks like during training.
    
    **Understanding Predictions:**
    
    - **0.0 - 0.3 (Low)**: Normal operation, model is confident this is healthy
    - **0.3 - 0.7 (Medium)**: Uncertain region, may indicate unusual but not necessarily bad patterns
    - **0.7 - 1.0 (High)**: Likely error or anomaly, model detected failure patterns
    
    **Why LSTM for Log Analysis?**
    
    1. **Temporal Dependencies**: Logs are sequential - what happens at time T depends on T-1, T-2, etc.
       LSTMs explicitly model these dependencies through their memory cells.
    
    2. **Variable-Length Sequences**: Sessions have different lengths. LSTMs naturally handle this
       (though we pad for batch processing).
    
    3. **Long-Term Context**: Errors often have precursors minutes earlier. LSTM's cell state can
       maintain relevant context across long sequences (unlike simple RNNs which suffer from
       vanishing gradients).
    
    4. **Pattern Learning**: The model learns that sequences like "connection timeout → retry →
       database error → service crash" indicate a cascading failure, not just isolated events.
    
    **Model Confidence:**
    The probability output reflects the model's confidence based on:
    - How similar the input sequence is to training data
    - Strength of learned error patterns in the sequence
    - Consistency of predictions across similar sequences
    
    **Limitations:**
    - Requires trained model (no zero-shot learning)
    - Performance depends on training data quality and diversity
    - May not detect novel error types not seen during training
    - Computational cost scales with sequence length
    
    **Prerequisites:**
    - Model must be trained first (`/train`) or loaded (`/load-model`)
    - Log format should match training data format
    - Logs must be sessionizable (have session IDs or temporal structure)
    
    **Use Cases:**
    - **Incident Response**: "What caused the 3 AM outage?" - Identify root causes in production logs
    - **Proactive Monitoring**: "Are there anomalies in today's logs?" - Detect issues before they escalate
    - **Pattern Discovery**: "What failure patterns exist?" - Find recurring problems in historical data
    - **Predictive Analysis**: "Which sessions are likely to fail?" - Identify at-risk operations early
    
    **Learn More:**
    - [RNN Inference Explained](https://www.tensorflow.org/guide/keras/rnn#cross-batch_statefulness) - How inference works
    - [Anomaly Detection with Deep Learning](https://arxiv.org/abs/1901.03407) - Research overview
    - [Log Analysis with Machine Learning](https://www.usenix.org/conference/osdi18/presentation/du) - Academic paper
    - [Understanding Model Predictions](https://christophm.github.io/interpretable-ml-book/) - Interpretation techniques
    - [AIOps: Root Cause Analysis](https://research.google/pubs/pub43438/) - Industry applications
    - [Sequence Classification](https://machinelearningmastery.com/sequence-classification-lstm-recurrent-neural-networks-python-keras/) - Implementation guide
    """,
    response_description="Root cause analysis results",
    responses={
        200: {"description": "Analysis completed successfully"},
        400: {"description": "Model not trained - train first"},
        500: {"description": "Internal server error during analysis"}
    }
)
async def analyze_logs(request: AnalysisRequest):
    """
    Analyze logs and provide root cause analysis
    
    Args:
        request: Analysis request with log path
        
    Returns:
        Root cause analysis results
    """
    try:
        pipeline = get_pipeline()
        
        if not pipeline.is_trained:
            raise HTTPException(
                status_code=400,
                detail="Model not trained. Please train the model first using /train endpoint"
            )
        
        # Analyze logs
        results = pipeline.analyze_logs(request.log_path, request.is_directory)
        
        return {
            "success": True,
            "message": "Analysis completed successfully",
            "data": results
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/analyze-upload",
    response_model=AnalysisResponse,
    summary="Upload and analyze logs",
    description="""Upload log file and perform end-to-end ML inference in one operation.
    
    **Complete ML Pipeline:**
    This endpoint combines preprocessing and inference into a single atomic operation:
    
    1. **File Upload** → Temporary storage
    2. **Preprocessing** → Feature extraction and sessionization
    3. **Vectorization** → Text to numerical sequences (NLP)
    4. **LSTM Inference** → Neural network forward pass
    5. **Post-processing** → Root cause extraction and ranking
    6. **Cleanup** → Remove temporary files
    
    **Why Combine Upload + Analysis?**
    - **Convenience**: Single API call for complete analysis
    - **Atomic Operation**: Ensures preprocessing matches inference expectations
    - **Stateless**: Doesn't persist data on server (good for privacy/compliance)
    - **Client-Side Logs**: Analyze logs from user machines or external systems
    
    **ML Context:**
    The trained LSTM model performs inference on the uploaded data using the same vectorization
    and feature engineering pipeline used during training. This consistency is crucial - if
    preprocessing differs between training and inference, model accuracy degrades significantly
    (known as "training-serving skew" in ML systems).
    
    **Data Format Requirements:**
    - **Supported**: .txt, .log, .json, .xml
    - **Structure**: Should match training data format
    - **Encoding**: UTF-8 recommended
    - **Size**: Limited by server memory (typically < 100MB)
    
    **Prerequisites:**
    - Model must be trained (`/train`) or loaded (`/load-model`)
    - Vocabulary must match training vocabulary (automatically handled)
    - Log format should be consistent with training data
    
    **Learn More:**
    - [ML Model Serving](https://ml-ops.org/content/phase-three) - Production inference patterns
    - [Training-Serving Skew](https://developers.google.com/machine-learning/guides/rules-of-ml#training-serving_skew) - Common ML pitfall
    - [RESTful ML APIs](https://cloud.google.com/architecture/mlops-continuous-delivery-and-automation-pipelines-in-machine-learning) - Best practices
    """,
    response_description="Analysis results with root cause insights",
    responses={
        200: {"description": "Analysis completed successfully"},
        400: {"description": "Model not trained"},
        500: {"description": "Internal server error"}
    }
)
async def analyze_uploaded_logs(
    file: UploadFile = File(
        ...,
        description="Log file to analyze (text, JSON, or XML format)"
    )
):
    """
    Upload and analyze a log file
    
    Args:
        file: Log file to analyze
        
    Returns:
        Root cause analysis results
    """
    try:
        pipeline = get_pipeline()
        
        if not pipeline.is_trained:
            raise HTTPException(
                status_code=400,
                detail="Model not trained. Please train the model first using /train endpoint"
            )
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            tmp_path = tmp_file.name
        
        # Analyze logs
        results = pipeline.analyze_logs(tmp_path, is_directory=False)
        
        # Clean up
        Path(tmp_path).unlink()
        
        return AnalysisResponse(
            success=True,
            message="Analysis completed successfully",
            data=results
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
