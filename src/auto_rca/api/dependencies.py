"""Shared dependencies for API routes"""

from auto_rca.pipeline import RCAPipeline

# Global pipeline instance
pipeline = RCAPipeline()


def get_pipeline() -> RCAPipeline:
    """Get the global pipeline instance"""
    return pipeline
