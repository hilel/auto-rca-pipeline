#!/usr/bin/env python3
"""
Example: Using the FastAPI server
This example demonstrates how to interact with the API
"""

import requests
import json
from pathlib import Path


def main():
    # Base URL for the API
    base_url = "http://localhost:8000"
    
    print("=" * 80)
    print("Auto-RCA Pipeline - API Example")
    print("=" * 80)
    print("\nNOTE: Make sure the API server is running first:")
    print("  python src/cli.py serve")
    print("\n" + "=" * 80)
    
    # Check health
    print("\n[1] Checking API health...")
    try:
        response = requests.get(f"{base_url}/health")
        health = response.json()
        print(f"  ✓ Status: {health['status']}")
        print(f"  ✓ Version: {health['version']}")
        print(f"  ✓ Model trained: {health['model_trained']}")
    except requests.exceptions.ConnectionError:
        print("  ✗ Error: Could not connect to API server")
        print("  Please start the server with: python src/cli.py serve")
        return
    
    # Train model if not already trained
    if not health['model_trained']:
        print("\n[2] Training model...")
        print("  (This may take a few minutes...)")
        
        train_data = {
            "log_path": "data/raw",
            "is_directory": True,
            "epochs": 10
        }
        
        response = requests.post(f"{base_url}/train", params=train_data)
        if response.status_code == 200:
            result = response.json()
            print(f"  ✓ Model trained successfully")
            print(f"  ✓ Training samples: {result['data']['training_samples']}")
        else:
            print(f"  ✗ Training failed: {response.json()['detail']}")
            return
    
    # Get model info
    print("\n[3] Getting model information...")
    response = requests.get(f"{base_url}/model-info")
    if response.status_code == 200:
        info = response.json()
        config = info['data']['config']
        print(f"  ✓ Model configuration:")
        print(f"    - Vocab size: {config['vocab_size']}")
        print(f"    - LSTM units: {config['lstm_units']}")
        print(f"    - Sequence length: {config['sequence_length']}")
    
    # Analyze logs
    print("\n[4] Analyzing logs...")
    
    analyze_data = {
        "log_path": "data/raw",
        "is_directory": True
    }
    
    response = requests.post(
        f"{base_url}/analyze",
        json=analyze_data
    )
    
    if response.status_code == 200:
        result = response.json()
        data = result['data']
        rca = data['root_cause_analysis']
        
        print(f"  ✓ Analysis completed")
        print(f"  ✓ Sessions analyzed: {rca['total_analyzed']}")
        print(f"  ✓ Error sessions: {rca['error_sessions_count']}")
        print(f"  ✓ Error rate: {rca['error_rate']:.1%}")
        
        if rca['top_exceptions']:
            print(f"\n  Top Root Causes:")
            for exc, count in rca['top_exceptions'][:3]:
                print(f"    - {exc}: {count} times")
    else:
        error = response.json()
        print(f"  ✗ Analysis failed: {error['detail']}")
    
    # Upload and analyze a file
    print("\n[5] Uploading a log file for analysis...")
    
    log_file = Path("data/raw/sample_logs.json")
    if log_file.exists():
        with open(log_file, 'rb') as f:
            files = {'file': (log_file.name, f, 'application/json')}
            response = requests.post(f"{base_url}/analyze-upload", files=files)
        
        if response.status_code == 200:
            result = response.json()
            data = result['data']
            print(f"  ✓ File analyzed successfully")
            print(f"  ✓ Sessions found: {data['session_count']}")
        else:
            print(f"  ✗ Upload failed: {response.json()['detail']}")
    else:
        print(f"  ✗ Sample log file not found: {log_file}")
    
    print("\n" + "=" * 80)
    print("API interaction completed!")
    print("=" * 80)
    print("\nFor interactive API documentation, visit:")
    print(f"  {base_url}/docs")


if __name__ == '__main__':
    main()
