#!/usr/bin/env python3
"""
Example: Complete end-to-end pipeline demonstration
This example shows all 5 stages of the Auto-RCA pipeline
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from auto_rca.pipeline import RCAPipeline
from auto_rca.utils.synthetic_data import SyntheticLogGenerator


def main():
    print("=" * 80)
    print("Auto-RCA Pipeline - Complete Example")
    print("=" * 80)
    
    # Step 1: Generate synthetic data
    print("\n[1/5] INGESTION: Generating synthetic log data...")
    generator = SyntheticLogGenerator()
    log_paths = generator.save_logs(
        output_dir='data/raw',
        num_logs=300,
        error_rate=0.2  # 20% error rate
    )
    print(f"  ✓ Generated logs in data/raw/")
    
    # Step 2: Initialize pipeline
    print("\n[2/5] PARSING: Initializing pipeline...")
    pipeline = RCAPipeline()
    
    # Step 3: Process logs (Ingestion + Parsing + Sessionization)
    print("\n[3/5] SESSIONIZATION: Processing logs...")
    process_results = pipeline.process_logs('data/raw', is_directory=True)
    print(f"  ✓ Processed {process_results['raw_log_count']} raw logs")
    print(f"  ✓ Parsed {process_results['parsed_log_count']} logs")
    print(f"  ✓ Created {process_results['session_count']} sessions")
    
    # Display session statistics
    stats = process_results['session_statistics']
    print(f"\n  Session Statistics:")
    print(f"    - Total sessions: {stats['total_sessions']}")
    print(f"    - Error sessions: {stats['error_sessions']}")
    print(f"    - Error rate: {stats['error_rate']:.1%}")
    print(f"    - Avg duration: {stats['avg_duration_seconds']:.2f}s")
    print(f"    - Avg logs/session: {stats['avg_logs_per_session']:.1f}")
    
    # Step 4: Train model (Vectorization + ML Training)
    print("\n[4/5] VECTORIZATION & ML TRAINING: Training LSTM model...")
    sessions = process_results['sessions']
    
    training_results = pipeline.train_model(
        sessions,
        epochs=10,  # Using fewer epochs for demo
        batch_size=32
    )
    
    print(f"  ✓ Trained on {training_results['training_samples']} samples")
    print(f"  ✓ Completed {training_results['epochs_trained']} epochs")
    print(f"\n  Final Training Metrics:")
    for metric, value in training_results['metrics'].items():
        print(f"    - {metric}: {value:.4f}")
    
    # Save models
    print("\n  Saving models...")
    saved_paths = pipeline.save_models('data/models')
    print(f"  ✓ Models saved to data/models/")
    
    # Step 5: Analyze new logs
    print("\n[5/5] ML ANALYSIS: Analyzing logs for root causes...")
    
    # Generate new test data
    test_paths = generator.save_logs(
        output_dir='data/test',
        num_logs=100,
        error_rate=0.25  # Higher error rate for testing
    )
    
    analysis_results = pipeline.analyze_logs('data/test', is_directory=True)
    
    rca = analysis_results['root_cause_analysis']
    print(f"  ✓ Analyzed {rca['total_analyzed']} sessions")
    print(f"  ✓ Detected {rca['error_sessions_count']} error sessions")
    print(f"  ✓ Error rate: {rca['error_rate']:.1%}")
    
    if rca['top_exceptions']:
        print(f"\n  Top Root Causes (Exceptions):")
        for i, (exc, count) in enumerate(rca['top_exceptions'][:3], 1):
            print(f"    {i}. {exc}")
            print(f"       Occurrences: {count}")
    
    if rca['top_error_status_codes']:
        print(f"\n  Top Error Status Codes:")
        for code, count in rca['top_error_status_codes'][:3]:
            print(f"    - HTTP {code}: {count} times")
    
    # Display sample analyzed sessions
    print(f"\n  Sample Analyzed Sessions:")
    for session in analysis_results['analyzed_sessions'][:3]:
        analysis = session['analysis']
        print(f"\n    Session: {session['session_id']}")
        print(f"      - Logs: {session['log_count']}")
        print(f"      - Error Probability: {analysis['error_probability']:.1%}")
        print(f"      - Severity: {analysis['severity']}")
        print(f"      - Has Anomaly: {analysis['has_anomaly']}")
    
    print("\n" + "=" * 80)
    print("Pipeline execution completed successfully!")
    print("=" * 80)
    
    print("\nNext Steps:")
    print("  1. Start the API server: python src/cli.py serve")
    print("  2. Access API docs at: http://localhost:8000/docs")
    print("  3. Upload logs via API for real-time analysis")


if __name__ == '__main__':
    main()
