"""Unit tests for vectorization module"""

import pytest
import numpy as np

from auto_rca.vectorization import TextVectorizer


class TestTextVectorizer:
    """Test cases for TextVectorizer class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.vectorizer = TextVectorizer(vocab_size=100, sequence_length=50)
    
    def create_session(self, messages, has_errors=False):
        """Helper to create a session"""
        logs = [{'message': msg} for msg in messages]
        return {
            'logs': logs,
            'has_errors': has_errors
        }
    
    def test_fit_builds_vocabulary(self):
        """Test that fit builds vocabulary"""
        sessions = [
            self.create_session(['hello world', 'test message']),
            self.create_session(['another test', 'hello again'])
        ]
        
        self.vectorizer.fit(sessions)
        
        assert self.vectorizer.is_fitted
        assert len(self.vectorizer.word_to_index) > 4  # Special tokens + words
        assert 'hello' in self.vectorizer.word_to_index
        assert 'test' in self.vectorizer.word_to_index
    
    def test_transform_sessions(self):
        """Test transforming sessions to sequences"""
        sessions = [
            self.create_session(['error occurred'], has_errors=True),
            self.create_session(['success message'], has_errors=False)
        ]
        
        self.vectorizer.fit(sessions)
        X, y = self.vectorizer.transform_sessions(sessions)
        
        assert X.shape == (2, 50)  # 2 sessions, sequence_length=50
        assert y.shape == (2,)
        assert y[0] == 1  # First session has errors
        assert y[1] == 0  # Second session does not
    
    def test_sequence_padding(self):
        """Test that sequences are padded correctly"""
        sessions = [
            self.create_session(['short']),
        ]
        
        self.vectorizer.fit(sessions)
        X, _ = self.vectorizer.transform_sessions(sessions)
        
        # Should be padded to sequence_length
        assert X.shape[1] == 50
        # Padding should contain PAD tokens (index 0)
        assert 0 in X[0]
    
    def test_sequence_truncation(self):
        """Test that long sequences are truncated"""
        # Create a long message
        long_message = ' '.join(['word'] * 100)
        sessions = [
            self.create_session([long_message]),
        ]
        
        self.vectorizer.fit(sessions)
        X, _ = self.vectorizer.transform_sessions(sessions)
        
        # Should be truncated to sequence_length
        assert X.shape[1] == 50
    
    def test_unknown_words(self):
        """Test handling of unknown words"""
        sessions_train = [
            self.create_session(['known words']),
        ]
        
        self.vectorizer.fit(sessions_train)
        
        sessions_test = [
            self.create_session(['unknown words']),
        ]
        
        X, _ = self.vectorizer.transform_sessions(sessions_test)
        
        # Unknown words should be mapped to <UNK> token
        assert self.vectorizer.word_to_index['<UNK>'] in X[0]
    
    def test_vectorize_session_features(self):
        """Test extracting session features"""
        session = {
            'duration_seconds': 120,
            'log_count': 10,
            'log_level_counts': {
                'ERROR': 2,
                'INFO': 8
            },
            'has_errors': True,
            'exceptions': ['Exception 1'],
            'http_methods': ['GET', 'POST'],
            'status_codes': [200, 500]
        }
        
        features = self.vectorizer.vectorize_session_features(session)
        
        assert isinstance(features, np.ndarray)
        assert features.shape[0] > 0
        assert features[0] == 120  # duration_seconds
        assert features[1] == 10   # log_count
