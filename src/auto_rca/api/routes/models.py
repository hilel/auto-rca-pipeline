"""Model management endpoints"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from auto_rca.api.schemas import ModelInfoResponse, LoadModelResponse
from auto_rca.api.dependencies import get_pipeline
from auto_rca.config import settings

router = APIRouter(tags=["Models"])


@router.post(
    "/load-model",
    response_model=LoadModelResponse,
    summary="Load pre-trained model",
    description="""Load a previously trained LSTM model and its vectorizer from disk into memory.
    
    **Model Persistence in ML Systems:**
    
    After training, two critical components are saved:
    
    1. **Neural Network Weights** (`lstm_model.h5`):
       - Layer architectures (Embedding, LSTM, Dense)
       - Learned weight matrices and bias vectors
       - Model configuration and hyperparameters
       - Format: HDF5 (Hierarchical Data Format)
       - Size: Typically 1-50 MB depending on architecture
    
    2. **Text Vectorizer** (`vectorizer.pkl`):
       - Token-to-ID mapping (vocabulary)
       - Tokenization configuration
       - Sequence length parameters
       - Format: Python pickle
       - Size: Typically < 1 MB
    
    **Why Both Are Required:**
    The neural network alone cannot process text - it only understands numbers. The vectorizer
    translates text logs into numerical sequences that the LSTM can process. Using a different
    vectorizer than the one used during training will produce nonsensical predictions because
    token IDs won't match the learned embeddings.
    
    **Loading Process:**
    1. Locate model files in specified directory
    2. Deserialize neural network architecture and weights (Keras loader)
    3. Load vectorizer and vocabulary (pickle loader)
    4. Validate model integrity (check for corruption)
    5. Store in memory for fast inference
    
    **Memory Considerations:**
    - Models are loaded into RAM for fast inference
    - Typical memory usage: 50-500 MB
    - Single model instance shared across all requests (thread-safe)
    - Model stays loaded until server restart or explicit reload
    
    **Model Versioning:**
    You can maintain multiple trained models for different purposes:
    - Different applications or services
    - Different environments (dev, staging, prod)
    - A/B testing scenarios
    - Fallback models for robustness
    
    **Use Cases:**
    - **Server Restart**: Restore model state after API server restart
    - **Model Switching**: Load different models trained for specific applications
    - **Deployment**: Use pre-trained models in production without retraining
    - **Experimentation**: Test different model versions
    
    **Default Location:** `data/models/` (configurable via model_dir parameter)
    
    **Error Handling:**
    - **File not found**: Verify both .h5 and .pkl files exist
    - **Version mismatch**: Ensure Keras/TensorFlow versions match training environment
    - **Corrupted file**: Model file may be incomplete or damaged
    - **Memory error**: Insufficient RAM for model size
    
    **Learn More:**
    - [Keras Model Serialization](https://keras.io/api/models/model_saving_apis/) - Save/load mechanisms
    - [ML Model Deployment](https://ml-ops.org/content/phase-three) - Production best practices
    - [Model Versioning](https://dvc.org/doc/use-cases/versioning-data-and-model-files) - Version control for ML
    - [HDF5 Format](https://www.hdfgroup.org/solutions/hdf5/) - Understanding the storage format
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
    description="""Retrieve comprehensive information about the loaded LSTM model architecture and configuration.
    
    **Model Architecture Components:**
    
    1. **Embedding Layer:**
       - **Purpose**: Convert token IDs → dense vector representations
       - **Input**: Integer token IDs (e.g., 42, 137, 5)
       - **Output**: Dense vectors (e.g., 128-dimensional embeddings)
       - **Learning**: Embeddings are learned during training to capture semantic similarity
       - **Example**: Similar log patterns get similar embeddings in vector space
    
    2. **LSTM Layer(s):**
       - **Purpose**: Learn sequential patterns and temporal dependencies
       - **Architecture**:
         - Input gate: Controls what new information to store
         - Forget gate: Controls what information to discard
         - Output gate: Controls what information to output
         - Cell state: Long-term memory across sequence
         - Hidden state: Short-term memory for current position
       - **Units**: Number of LSTM cells (more = more capacity, slower)
       - **Stacking**: Multiple LSTM layers = deeper network, more complex patterns
    
    3. **Dense Output Layer:**
       - **Purpose**: Binary classification (error vs. normal)
       - **Activation**: Sigmoid (outputs probability 0-1)
       - **Loss Function**: Binary cross-entropy
       - **Single neuron**: Outputs single probability value
    
    **Hyperparameters Explained:**
    
    - **vocab_size**: Total unique tokens in vocabulary
      - Larger = handles more diverse logs
      - Typical range: 1,000 - 50,000
      - Unknown tokens mapped to UNK
    
    - **embedding_dim**: Dimensionality of word embeddings
      - Higher = more expressive representations
      - Typical range: 50 - 300
      - Trade-off: expressiveness vs. training time
    
    - **lstm_units**: Number of LSTM cells per layer
      - More units = more learning capacity
      - Typical range: 64 - 512
      - Trade-off: capacity vs. overfitting risk
    
    - **lstm_layers**: Number of stacked LSTM layers
      - Deeper = can learn more complex patterns
      - Typical range: 1 - 3
      - Diminishing returns beyond 3 layers for most tasks
    
    - **sequence_length**: Maximum input sequence length
      - Longer = more context per session
      - Typical range: 50 - 500
      - Trade-off: context vs. computation time
    
    **Model Capacity:**
    Total parameters = Trainable weights in the network
    - More parameters = more learning capacity
    - Risk of overfitting if parameters >> training samples
    - Rule of thumb: Need ~10 training examples per parameter
    
    **Architecture Choices:**
    - **Why LSTM over Simple RNN**: Solves vanishing gradient problem for long sequences
    - **Why Bidirectional**: Not used here (logs are causal - future doesn't affect past)
    - **Why Stacking**: Allows hierarchical feature learning (low-level → high-level patterns)
    - **Why Embedding**: Converts discrete tokens to continuous space for gradient-based learning
    
    **Returns:**
    - Complete layer-by-layer architecture breakdown
    - Input/output shapes for each layer
    - Parameter counts (total and trainable)
    - Hyperparameter configuration
    - Training status and model readiness
    
    **Use Cases:**
    - **Debugging**: Verify correct model is loaded
    - **Documentation**: Generate model cards for production systems
    - **Optimization**: Identify architecture bottlenecks
    - **Comparison**: Compare different model configurations
    - **Validation**: Ensure model meets requirements before deployment
    
    **Learn More:**
    - [LSTM Architecture Deep Dive](https://colah.github.io/posts/2015-08-Understanding-LSTMs/) - Visual explanations
    - [Word Embeddings](https://jalammar.github.io/illustrated-word2vec/) - Understanding embeddings
    - [Neural Network Architectures](https://www.deeplearningbook.org/contents/mlp.html) - Foundational theory
    - [Hyperparameter Tuning](https://cs231n.github.io/neural-networks-3/#hyper) - Optimization strategies
    - [Model Cards](https://arxiv.org/abs/1810.03993) - Documentation best practices
    - [Keras Model API](https://keras.io/api/models/) - Implementation details
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
            return ModelInfoResponse(
                success=True,
                message="No model loaded",
                data={
                    "model_trained": False
                }
            )
        
        model_summary = pipeline.analyzer.get_model_summary()
        
        return ModelInfoResponse(
            success=True,
            message="Model information retrieved",
            data={
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
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
