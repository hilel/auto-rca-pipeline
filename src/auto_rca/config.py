"""Configuration settings for Auto-RCA Pipeline"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = False
    
    # Model Settings
    lstm_units: int = 128
    lstm_layers: int = 2
    dropout_rate: float = 0.2
    sequence_length: int = 100
    vocab_size: int = 10000
    embedding_dim: int = 128
    
    # Training Settings
    batch_size: int = 32
    epochs: int = 50
    learning_rate: float = 0.001
    validation_split: float = 0.2
    
    # Data Settings
    max_log_length: int = 1000
    min_session_gap_seconds: int = 300  # 5 minutes
    
    # Paths
    data_dir: str = "data"
    models_dir: str = "data/models"
    raw_logs_dir: str = "data/raw"
    processed_logs_dir: str = "data/processed"
    
    # Feature flags (for future production features)
    enable_streaming: bool = False
    enable_elk_integration: bool = False
    enable_sql_integration: bool = False
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
