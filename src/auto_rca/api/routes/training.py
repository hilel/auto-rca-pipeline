"""Model training endpoints"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from auto_rca.api.schemas import TrainingResponse
from auto_rca.api.dependencies import get_pipeline

router = APIRouter(tags=["Training"])


@router.post(
    "/train",
    response_model=TrainingResponse,
    summary="Train LSTM model",
    description="""Train a deep learning LSTM (Long Short-Term Memory) model for automated root cause analysis.
    
    **What is LSTM?**
    LSTM is a type of Recurrent Neural Network (RNN) specifically designed to learn from sequential
    data with long-term dependencies. Unlike traditional models, LSTMs maintain "memory cells" that
    can remember important information across many time steps, making them ideal for log analysis
    where context from previous events matters.
    
    **Training Process - Deep Dive:**
    
    1. **Data Preprocessing:**
       - Logs → Parsing → Sessions (sequences of related events)
       - Each session becomes a training example
    
    2. **Text Vectorization (NLP):**
       - Build vocabulary from unique log tokens (words/patterns)
       - Convert text to numerical token IDs using tokenization
       - Pad/truncate sequences to uniform length (required for batch processing)
       - Creates dense word embeddings (learned representations)
    
    3. **Neural Network Architecture:**
       - **Embedding Layer**: Converts token IDs → dense vectors (word embeddings)
       - **LSTM Layers**: Learn temporal patterns and dependencies
         - Hidden state: short-term memory of recent events
         - Cell state: long-term memory of important patterns
       - **Dense Output**: Binary classification (normal vs. error)
         - Sigmoid activation outputs probability [0, 1]
    
    4. **Training Algorithm (Backpropagation Through Time):**
       - Forward pass: Process each session sequence through network
       - Loss calculation: Binary cross-entropy between predictions and actual labels
       - Backward pass: Compute gradients and update weights
       - Optimizer (Adam): Adaptive learning rate for efficient training
    
    5. **Model Persistence:**
       - Save trained weights (HDF5 format)
       - Save vectorizer vocabulary (pickle format)
       - Both required for inference
    
    **Hyperparameters Explained:**
    
    - **epochs**: Number of complete passes through training data
      - More epochs = more learning, but risk of overfitting
      - Use validation loss to determine optimal number
      - Default: 50 (good starting point for most datasets)
    
    - **batch_size**: Number of samples processed before weight update
      - Larger batches: Faster training, more memory, less noisy gradients
      - Smaller batches: Slower training, less memory, better generalization
      - Default: 32 (balance between speed and stability)
    
    **Data Requirements:**
    - Minimum: 1,000+ log entries (preferably 10,000+)
    - Balanced dataset: 10-30% error logs, 70-90% normal logs
    - Diverse patterns: Multiple types of errors for better generalization
    - Representative data: Should match production log characteristics
    
    **Training Time Complexity:**
    - O(n * e * s) where n=samples, e=epochs, s=sequence_length
    - Typically 1-10 minutes for small datasets (< 50K logs)
    - GPU acceleration can reduce training time by 10-100x
    
    **Evaluation Metrics:**
    - **Loss**: Binary cross-entropy (lower is better)
      - Measures how far predictions are from true labels
      - Should decrease steadily during training
    - **Accuracy**: Percentage of correct predictions
      - > 90% is excellent for log analysis
      - < 70% indicates need for more/better training data
    
    **Overfitting Prevention:**
    - Model uses dropout (randomly disables neurons during training)
    - Early stopping monitors validation loss
    - Regularization prevents over-reliance on specific features
    
    **Note:** Training overwrites existing models. Consider backing up important models first.
    
    **Learn More:**
    - [Understanding LSTM Networks](https://colah.github.io/posts/2015-08-Understanding-LSTMs/) - Visual explanation
    - [Deep Learning Book - RNNs](https://www.deeplearningbook.org/contents/rnn.html) - Theoretical foundation
    - [Keras LSTM Tutorial](https://keras.io/api/layers/recurrent_layers/lstm/) - Implementation details
    - [Text Classification with RNNs](https://www.tensorflow.org/tutorials/text/text_classification_rnn) - Similar use case
    - [Word Embeddings Explained](https://jalammar.github.io/illustrated-word2vec/) - Understanding embeddings
    - [Backpropagation Through Time](https://machinelearningmastery.com/gentle-introduction-backpropagation-time/) - Training algorithm
    - [Hyperparameter Tuning](https://cs231n.github.io/neural-networks-3/#hyper) - Optimization strategies
    """,
    response_description="Training results and saved model paths",
    responses={
        200: {"description": "Model trained successfully"},
        400: {"description": "Bad request - no sessions found in logs"},
        500: {"description": "Internal server error during training"}
    }
)
async def train_model(
    log_path: str = Query(..., description="Path to training logs on the server"),
    is_directory: bool = Query(False, description="Set to true if log_path is a directory"),
    epochs: Optional[int] = Query(None, description="Number of training epochs (default: 50)"),
    batch_size: Optional[int] = Query(None, description="Batch size for training (default: 32)")
):
    """
    Train the LSTM model on provided logs
    
    Args:
        log_path: Path to training logs
        is_directory: Whether the path is a directory
        epochs: Number of training epochs
        batch_size: Batch size for training
        
    Returns:
        Training status
    """
    try:
        pipeline = get_pipeline()
        
        # Process logs
        process_results = pipeline.process_logs(log_path, is_directory)
        sessions = process_results['sessions']
        
        if not sessions:
            raise HTTPException(status_code=400, detail="No sessions found in logs")
        
        # Train model
        training_results = pipeline.train_model(
            sessions,
            epochs=epochs,
            batch_size=batch_size
        )
        
        # Save models
        saved_paths = pipeline.save_models()
        
        return TrainingResponse(
            success=True,
            message="Model trained successfully",
            data={
                **training_results,
                "model_paths": saved_paths
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
