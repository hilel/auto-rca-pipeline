"""Vectorization module for converting text to sequences for LSTM"""

import numpy as np
import re
from typing import List, Dict, Any, Optional, Tuple
import pickle
from pathlib import Path


class TextVectorizer:
    """Converts text logs into numerical sequences for LSTM processing"""
    
    def __init__(self, vocab_size: int = 10000, sequence_length: int = 100):
        """
        Initialize text vectorizer
        
        Args:
            vocab_size: Maximum vocabulary size
            sequence_length: Fixed length for sequences (padding/truncation)
        """
        self.vocab_size = vocab_size
        self.sequence_length = sequence_length
        self.word_to_index = {'<PAD>': 0, '<UNK>': 1, '<START>': 2, '<END>': 3}
        self.index_to_word = {0: '<PAD>', 1: '<UNK>', 2: '<START>', 3: '<END>'}
        self.word_counts = {}
        self.is_fitted = False
    
    def fit(self, sessions: List[Dict[str, Any]]) -> 'TextVectorizer':
        """
        Build vocabulary from sessions
        
        Args:
            sessions: List of session objects with logs
            
        Returns:
            Self for method chaining
        """
        # Collect all text
        all_texts = []
        for session in sessions:
            for log in session.get('logs', []):
                message = log.get('message', '')
                if message:
                    all_texts.append(message)
        
        # Count words
        for text in all_texts:
            words = self._tokenize(text)
            for word in words:
                self.word_counts[word] = self.word_counts.get(word, 0) + 1
        
        # Build vocabulary from most common words
        sorted_words = sorted(self.word_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Reserve first few indices for special tokens
        next_index = len(self.word_to_index)
        
        for word, count in sorted_words[:self.vocab_size - len(self.word_to_index)]:
            self.word_to_index[word] = next_index
            self.index_to_word[next_index] = word
            next_index += 1
        
        self.is_fitted = True
        return self
    
    def transform_sessions(self, sessions: List[Dict[str, Any]]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Transform sessions into sequences and labels
        
        Args:
            sessions: List of session objects
            
        Returns:
            Tuple of (sequences, labels) as numpy arrays
        """
        if not self.is_fitted:
            raise ValueError("Vectorizer must be fitted before transform. Call fit() first.")
        
        sequences = []
        labels = []
        
        for session in sessions:
            # Create sequence from session logs
            session_sequence = self._session_to_sequence(session)
            sequences.append(session_sequence)
            
            # Label: 1 if session has errors, 0 otherwise
            label = 1 if session.get('has_errors', False) else 0
            labels.append(label)
        
        return np.array(sequences), np.array(labels)
    
    def _session_to_sequence(self, session: Dict[str, Any]) -> np.ndarray:
        """Convert a session to a padded/truncated sequence"""
        # Combine all log messages in the session
        session_text = []
        for log in session.get('logs', []):
            message = log.get('message', '')
            if message:
                session_text.append(message)
        
        # Tokenize and convert to indices
        combined_text = ' '.join(session_text)
        words = self._tokenize(combined_text)
        
        # Convert words to indices
        indices = [self.word_to_index.get(word, self.word_to_index['<UNK>']) for word in words]
        
        # Pad or truncate to sequence_length
        if len(indices) < self.sequence_length:
            # Pad with <PAD> token
            indices = indices + [self.word_to_index['<PAD>']] * (self.sequence_length - len(indices))
        else:
            # Truncate
            indices = indices[:self.sequence_length]
        
        return np.array(indices)
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization (can be improved with better tokenizers)"""
        # Convert to lowercase and split by whitespace and common punctuation
        text = text.lower()
        # Keep alphanumeric and common separators
        tokens = re.findall(r'\w+', text)
        return tokens
    
    def vectorize_session_features(self, session: Dict[str, Any]) -> np.ndarray:
        """
        Create additional feature vector from session metadata
        
        Args:
            session: Session object
            
        Returns:
            Feature vector as numpy array
        """
        features = []
        
        # Numeric features
        features.append(session.get('duration_seconds', 0))
        features.append(session.get('log_count', 0))
        
        # Log level counts
        log_level_counts = session.get('log_level_counts', {})
        features.append(log_level_counts.get('DEBUG', 0))
        features.append(log_level_counts.get('INFO', 0))
        features.append(log_level_counts.get('WARN', 0))
        features.append(log_level_counts.get('WARNING', 0))
        features.append(log_level_counts.get('ERROR', 0))
        features.append(log_level_counts.get('CRITICAL', 0))
        
        # Boolean features
        features.append(1 if session.get('has_errors') else 0)
        features.append(len(session.get('exceptions', [])))
        features.append(len(session.get('http_methods', [])))
        features.append(len(session.get('status_codes', [])))
        
        return np.array(features, dtype=np.float32)
    
    def save(self, path: str) -> None:
        """Save vectorizer to disk"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'wb') as f:
            pickle.dump({
                'vocab_size': self.vocab_size,
                'sequence_length': self.sequence_length,
                'word_to_index': self.word_to_index,
                'index_to_word': self.index_to_word,
                'word_counts': self.word_counts,
                'is_fitted': self.is_fitted
            }, f)
    
    @classmethod
    def load(cls, path: str) -> 'TextVectorizer':
        """Load vectorizer from disk"""
        with open(path, 'rb') as f:
            data = pickle.load(f)
        
        vectorizer = cls(
            vocab_size=data['vocab_size'],
            sequence_length=data['sequence_length']
        )
        vectorizer.word_to_index = data['word_to_index']
        vectorizer.index_to_word = data['index_to_word']
        vectorizer.word_counts = data['word_counts']
        vectorizer.is_fitted = data['is_fitted']
        
        return vectorizer
