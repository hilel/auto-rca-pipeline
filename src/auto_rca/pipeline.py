"""Pipeline orchestrator for coordinating all stages"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import numpy as np

from auto_rca.ingestion import LogReader
from auto_rca.parsing import LogParser
from auto_rca.sessionization import SessionGrouper
from auto_rca.vectorization import TextVectorizer
from auto_rca.ml_analysis import LSTMAnalyzer
from auto_rca.config import settings


class RCAPipeline:
    """Main pipeline orchestrator for Root Cause Analysis"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize RCA Pipeline
        
        Args:
            config: Optional configuration dictionary
        """
        # Initialize components
        self.log_reader = LogReader()
        self.log_parser = LogParser()
        self.session_grouper = SessionGrouper(
            session_gap_seconds=settings.min_session_gap_seconds
        )
        self.vectorizer = TextVectorizer(
            vocab_size=settings.vocab_size,
            sequence_length=settings.sequence_length
        )
        self.analyzer = LSTMAnalyzer(
            vocab_size=settings.vocab_size,
            embedding_dim=settings.embedding_dim,
            lstm_units=settings.lstm_units,
            lstm_layers=settings.lstm_layers,
            dropout_rate=settings.dropout_rate,
            sequence_length=settings.sequence_length
        )
        
        self.is_trained = False
    
    def process_logs(
        self,
        log_source: str,
        is_directory: bool = False
    ) -> Dict[str, Any]:
        """
        Process logs through the entire pipeline
        
        Args:
            log_source: Path to log file or directory
            is_directory: Whether the source is a directory
            
        Returns:
            Processing results with sessions and analysis
        """
        # Stage 1: Ingestion
        if is_directory:
            raw_logs = self.log_reader.read_directory(log_source)
        else:
            raw_logs = self.log_reader.read_file(log_source)
        
        # Stage 2: Parsing
        parsed_logs = self.log_parser.parse_logs(raw_logs)
        
        # Stage 3: Sessionization
        sessions = self.session_grouper.group_by_session(parsed_logs)
        session_stats = self.session_grouper.analyze_sessions(sessions)
        
        return {
            'raw_log_count': len(raw_logs),
            'parsed_log_count': len(parsed_logs),
            'session_count': len(sessions),
            'session_statistics': session_stats,
            'sessions': sessions
        }
    
    def train_model(
        self,
        sessions: List[Dict[str, Any]],
        epochs: int = None,
        batch_size: int = None,
        validation_split: float = None
    ) -> Dict[str, Any]:
        """
        Train the LSTM model on sessions
        
        Args:
            sessions: List of session objects
            epochs: Number of training epochs
            batch_size: Batch size for training
            validation_split: Validation split ratio
            
        Returns:
            Training results
        """
        # Stage 4: Vectorization
        self.vectorizer.fit(sessions)
        X, y = self.vectorizer.transform_sessions(sessions)
        
        # Stage 5: ML Training
        epochs = epochs or settings.epochs
        batch_size = batch_size or settings.batch_size
        validation_split = validation_split or settings.validation_split
        
        history = self.analyzer.train(
            X, y,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split
        )
        
        self.is_trained = True
        
        # Get final metrics
        final_metrics = {
            'final_loss': float(history.history['loss'][-1]),
            'final_accuracy': float(history.history['accuracy'][-1]),
        }
        
        if 'val_loss' in history.history:
            final_metrics['final_val_loss'] = float(history.history['val_loss'][-1])
            final_metrics['final_val_accuracy'] = float(history.history['val_accuracy'][-1])
        
        return {
            'training_samples': len(X),
            'epochs_trained': len(history.history['loss']),
            'metrics': final_metrics
        }
    
    def analyze_logs(
        self,
        log_source: str,
        is_directory: bool = False
    ) -> Dict[str, Any]:
        """
        Analyze logs and provide root cause analysis
        
        Args:
            log_source: Path to log file or directory
            is_directory: Whether the source is a directory
            
        Returns:
            Complete analysis results
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Train the model first using train_model()")
        
        # Process logs through stages 1-3
        process_results = self.process_logs(log_source, is_directory)
        sessions = process_results['sessions']
        
        if not sessions:
            return {
                **process_results,
                'analysis': {
                    'message': 'No sessions to analyze'
                }
            }
        
        # Stage 4: Vectorization
        X, _ = self.vectorizer.transform_sessions(sessions)
        
        # Stage 5: ML Analysis
        predictions = self.analyzer.predict(X)
        root_cause_analysis = self.analyzer.analyze_root_causes(sessions, predictions)
        
        # Add detailed predictions to sessions
        analyzed_sessions = []
        for session, pred in zip(sessions, predictions):
            session_analysis = self.analyzer.analyze_session(
                self.vectorizer._session_to_sequence(session)
            )
            analyzed_sessions.append({
                'session_id': session.get('session_id'),
                'start_time': session.get('start_time'),
                'end_time': session.get('end_time'),
                'log_count': session.get('log_count'),
                'has_errors': session.get('has_errors'),
                'analysis': session_analysis
            })
        
        return {
            **process_results,
            'analyzed_sessions': analyzed_sessions,
            'root_cause_analysis': root_cause_analysis
        }
    
    def save_models(self, model_dir: str = None) -> Dict[str, str]:
        """
        Save trained models to disk
        
        Args:
            model_dir: Directory to save models
            
        Returns:
            Paths to saved models
        """
        model_dir = model_dir or settings.models_dir
        model_dir = Path(model_dir)
        model_dir.mkdir(parents=True, exist_ok=True)
        
        # Save vectorizer
        vectorizer_path = model_dir / "vectorizer.pkl"
        self.vectorizer.save(str(vectorizer_path))
        
        # Save LSTM model
        model_path = model_dir / "lstm_model.h5"
        self.analyzer.save_model(str(model_path))
        
        return {
            'vectorizer': str(vectorizer_path),
            'lstm_model': str(model_path)
        }
    
    def load_models(self, model_dir: str = None) -> None:
        """
        Load trained models from disk
        
        Args:
            model_dir: Directory containing saved models
        """
        model_dir = model_dir or settings.models_dir
        model_dir = Path(model_dir)
        
        # Load vectorizer
        vectorizer_path = model_dir / "vectorizer.pkl"
        if vectorizer_path.exists():
            self.vectorizer = TextVectorizer.load(str(vectorizer_path))
        
        # Load LSTM model
        model_path = model_dir / "lstm_model.h5"
        if model_path.exists():
            self.analyzer.load_model(str(model_path))
            self.is_trained = True
