"""ML Analysis module with LSTM for root cause analysis"""

import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, models
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint


class LSTMAnalyzer:
    """LSTM-based analyzer for root cause analysis"""
    
    def __init__(
        self,
        vocab_size: int = 10000,
        embedding_dim: int = 128,
        lstm_units: int = 128,
        lstm_layers: int = 2,
        dropout_rate: float = 0.2,
        sequence_length: int = 100
    ):
        """
        Initialize LSTM Analyzer
        
        Args:
            vocab_size: Size of vocabulary
            embedding_dim: Dimension of word embeddings
            lstm_units: Number of LSTM units per layer
            lstm_layers: Number of LSTM layers
            dropout_rate: Dropout rate for regularization
            sequence_length: Length of input sequences
        """
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.lstm_units = lstm_units
        self.lstm_layers = lstm_layers
        self.dropout_rate = dropout_rate
        self.sequence_length = sequence_length
        self.model = None
        self.history = None
    
    def build_model(self) -> keras.Model:
        """Build LSTM model architecture"""
        model = models.Sequential([
            # Embedding layer
            layers.Embedding(
                input_dim=self.vocab_size,
                output_dim=self.embedding_dim,
                input_length=self.sequence_length,
                name='embedding'
            ),
            
            # LSTM layers
            *self._create_lstm_layers(),
            
            # Dense layers
            layers.Dense(64, activation='relu', name='dense_1'),
            layers.Dropout(self.dropout_rate, name='dropout_dense'),
            layers.Dense(32, activation='relu', name='dense_2'),
            
            # Output layer (binary classification: error or not)
            layers.Dense(1, activation='sigmoid', name='output')
        ])
        
        self.model = model
        return model
    
    def _create_lstm_layers(self) -> List[layers.Layer]:
        """Create LSTM layers based on configuration"""
        lstm_layers_list = []
        
        for i in range(self.lstm_layers):
            # Return sequences for all layers except the last one
            return_sequences = (i < self.lstm_layers - 1)
            
            lstm_layers_list.append(
                layers.LSTM(
                    self.lstm_units,
                    return_sequences=return_sequences,
                    dropout=self.dropout_rate,
                    recurrent_dropout=self.dropout_rate,
                    name=f'lstm_{i+1}'
                )
            )
        
        return lstm_layers_list
    
    def compile_model(self, learning_rate: float = 0.001) -> None:
        """Compile the model with optimizer and loss function"""
        if self.model is None:
            self.build_model()
        
        self.model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=learning_rate),
            loss='binary_crossentropy',
            metrics=['accuracy', keras.metrics.Precision(), keras.metrics.Recall()]
        )
    
    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None,
        epochs: int = 50,
        batch_size: int = 32,
        validation_split: float = 0.2
    ) -> keras.callbacks.History:
        """
        Train the LSTM model
        
        Args:
            X_train: Training sequences
            y_train: Training labels
            X_val: Validation sequences (optional)
            y_val: Validation labels (optional)
            epochs: Number of training epochs
            batch_size: Batch size for training
            validation_split: Validation split if X_val not provided
            
        Returns:
            Training history
        """
        if self.model is None:
            self.compile_model()
        
        # Prepare validation data
        validation_data = None
        if X_val is not None and y_val is not None:
            validation_data = (X_val, y_val)
            validation_split = 0.0
        
        # Callbacks
        callbacks = [
            EarlyStopping(
                monitor='val_loss',
                patience=5,
                restore_best_weights=True,
                verbose=1
            )
        ]
        
        # Train model
        self.history = self.model.fit(
            X_train,
            y_train,
            validation_data=validation_data,
            validation_split=validation_split,
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=1
        )
        
        return self.history
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict error probability for sequences
        
        Args:
            X: Input sequences
            
        Returns:
            Predicted probabilities
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        return self.model.predict(X)
    
    def analyze_session(self, session_sequence: np.ndarray) -> Dict[str, Any]:
        """
        Analyze a single session and provide root cause insights
        
        Args:
            session_sequence: Vectorized session sequence
            
        Returns:
            Analysis results with error probability and insights
        """
        # Reshape for single prediction
        if len(session_sequence.shape) == 1:
            session_sequence = session_sequence.reshape(1, -1)
        
        # Get prediction
        error_prob = float(self.predict(session_sequence)[0][0])
        
        # Determine severity
        if error_prob > 0.8:
            severity = "CRITICAL"
        elif error_prob > 0.6:
            severity = "HIGH"
        elif error_prob > 0.4:
            severity = "MEDIUM"
        else:
            severity = "LOW"
        
        return {
            'error_probability': error_prob,
            'severity': severity,
            'has_anomaly': error_prob > 0.5,
            'confidence': max(error_prob, 1 - error_prob)
        }
    
    def analyze_root_causes(
        self,
        sessions: List[Dict[str, Any]],
        predictions: np.ndarray
    ) -> Dict[str, Any]:
        """
        Analyze root causes across multiple sessions
        
        Args:
            sessions: List of session objects
            predictions: Model predictions for sessions
            
        Returns:
            Root cause analysis summary
        """
        # Identify error sessions
        error_threshold = 0.5
        error_sessions = []
        
        for i, (session, pred) in enumerate(zip(sessions, predictions)):
            if pred[0] > error_threshold:
                error_sessions.append({
                    'session_id': session.get('session_id'),
                    'error_probability': float(pred[0]),
                    'exceptions': session.get('exceptions', []),
                    'log_level_counts': session.get('log_level_counts', {}),
                    'status_codes': session.get('status_codes', [])
                })
        
        # Aggregate common patterns
        common_exceptions = {}
        common_status_codes = {}
        
        for error_session in error_sessions:
            for exception in error_session['exceptions']:
                common_exceptions[exception] = common_exceptions.get(exception, 0) + 1
            
            for status_code in error_session['status_codes']:
                common_status_codes[status_code] = common_status_codes.get(status_code, 0) + 1
        
        # Sort by frequency
        top_exceptions = sorted(common_exceptions.items(), key=lambda x: x[1], reverse=True)[:5]
        top_status_codes = sorted(common_status_codes.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'total_analyzed': len(sessions),
            'error_sessions_count': len(error_sessions),
            'error_rate': len(error_sessions) / len(sessions) if sessions else 0,
            'top_exceptions': top_exceptions,
            'top_error_status_codes': top_status_codes,
            'error_sessions': error_sessions[:10]  # Top 10 error sessions
        }
    
    def save_model(self, path: str) -> None:
        """Save model to disk"""
        if self.model is None:
            raise ValueError("No model to save")
        
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.model.save(path)
    
    def load_model(self, path: str) -> None:
        """Load model from disk"""
        self.model = keras.models.load_model(path)
    
    def get_model_summary(self) -> str:
        """Get model architecture summary"""
        if self.model is None:
            return "Model not built yet"
        
        import io
        stream = io.StringIO()
        self.model.summary(print_fn=lambda x: stream.write(x + '\n'))
        return stream.getvalue()
