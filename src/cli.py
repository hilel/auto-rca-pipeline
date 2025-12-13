"""Command-line interface for Auto-RCA Pipeline"""

import argparse
import sys
from pathlib import Path

# Add src to path for local imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from auto_rca.pipeline import RCAPipeline
from auto_rca.utils.synthetic_data import SyntheticLogGenerator
from auto_rca.config import settings
import json


def generate_data(args):
    """Generate synthetic log data"""
    print(f"Generating {args.num_logs} synthetic logs with {args.error_rate*100}% error rate...")
    
    generator = SyntheticLogGenerator()
    paths = generator.save_logs(
        output_dir=args.output_dir,
        num_logs=args.num_logs,
        error_rate=args.error_rate
    )
    
    print("\nGenerated log files:")
    for format_type, path in paths.items():
        print(f"  {format_type}: {path}")


def process_logs(args):
    """Process logs through the pipeline"""
    print(f"Processing logs from: {args.input}")
    
    pipeline = RCAPipeline()
    results = pipeline.process_logs(args.input, args.directory)
    
    print(f"\nProcessing Results:")
    print(f"  Raw logs: {results['raw_log_count']}")
    print(f"  Parsed logs: {results['parsed_log_count']}")
    print(f"  Sessions: {results['session_count']}")
    print(f"\nSession Statistics:")
    stats = results['session_statistics']
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Save results if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nResults saved to: {args.output}")


def train(args):
    """Train the LSTM model"""
    print(f"Training model on logs from: {args.input}")
    
    pipeline = RCAPipeline()
    
    # Process logs
    print("Processing logs...")
    process_results = pipeline.process_logs(args.input, args.directory)
    sessions = process_results['sessions']
    
    print(f"Found {len(sessions)} sessions")
    
    if len(sessions) < 10:
        print("Warning: Very few sessions found. Consider using more training data.")
    
    # Train model
    print(f"\nTraining model for {args.epochs} epochs...")
    training_results = pipeline.train_model(
        sessions,
        epochs=args.epochs,
        batch_size=args.batch_size
    )
    
    print("\nTraining Results:")
    print(f"  Training samples: {training_results['training_samples']}")
    print(f"  Epochs trained: {training_results['epochs_trained']}")
    print(f"  Final metrics:")
    for key, value in training_results['metrics'].items():
        print(f"    {key}: {value:.4f}")
    
    # Save models
    print(f"\nSaving models to: {args.model_dir}")
    saved_paths = pipeline.save_models(args.model_dir)
    print("Saved:")
    for key, path in saved_paths.items():
        print(f"  {key}: {path}")


def analyze(args):
    """Analyze logs using trained model"""
    print(f"Analyzing logs from: {args.input}")
    
    pipeline = RCAPipeline()
    
    # Load model
    print(f"Loading model from: {args.model_dir}")
    pipeline.load_models(args.model_dir)
    
    # Analyze logs
    print("Analyzing logs...")
    results = pipeline.analyze_logs(args.input, args.directory)
    
    print(f"\nAnalysis Results:")
    print(f"  Total sessions: {results['session_count']}")
    
    rca = results['root_cause_analysis']
    print(f"\nRoot Cause Analysis:")
    print(f"  Total analyzed: {rca['total_analyzed']}")
    print(f"  Error sessions: {rca['error_sessions_count']}")
    print(f"  Error rate: {rca['error_rate']:.2%}")
    
    if rca['top_exceptions']:
        print(f"\n  Top Exceptions:")
        for exc, count in rca['top_exceptions']:
            print(f"    - {exc}: {count} occurrences")
    
    if rca['top_error_status_codes']:
        print(f"\n  Top Error Status Codes:")
        for code, count in rca['top_error_status_codes']:
            print(f"    - {code}: {count} occurrences")
    
    # Save results if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nResults saved to: {args.output}")


def serve(args):
    """Start the FastAPI server"""
    import uvicorn
    
    print(f"Starting Auto-RCA Pipeline API server...")
    print(f"  Host: {args.host}")
    print(f"  Port: {args.port}")
    print(f"  Reload: {args.reload}")
    print(f"\nAPI will be available at: http://{args.host}:{args.port}")
    print(f"API documentation: http://{args.host}:{args.port}/docs")
    
    uvicorn.run(
        "auto_rca.api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Auto-RCA Pipeline: Automated Root Cause Analysis using LSTM"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Generate data command
    gen_parser = subparsers.add_parser('generate', help='Generate synthetic log data')
    gen_parser.add_argument('--output-dir', default='data/raw', help='Output directory')
    gen_parser.add_argument('--num-logs', type=int, default=200, help='Number of logs to generate')
    gen_parser.add_argument('--error-rate', type=float, default=0.15, help='Error rate (0.0-1.0)')
    gen_parser.set_defaults(func=generate_data)
    
    # Process logs command
    process_parser = subparsers.add_parser('process', help='Process logs through pipeline')
    process_parser.add_argument('input', help='Input log file or directory')
    process_parser.add_argument('--directory', action='store_true', help='Input is a directory')
    process_parser.add_argument('--output', help='Output file for results (JSON)')
    process_parser.set_defaults(func=process_logs)
    
    # Train command
    train_parser = subparsers.add_parser('train', help='Train LSTM model')
    train_parser.add_argument('input', help='Input log file or directory')
    train_parser.add_argument('--directory', action='store_true', help='Input is a directory')
    train_parser.add_argument('--epochs', type=int, default=settings.epochs, help='Training epochs')
    train_parser.add_argument('--batch-size', type=int, default=settings.batch_size, help='Batch size')
    train_parser.add_argument('--model-dir', default=settings.models_dir, help='Model save directory')
    train_parser.set_defaults(func=train)
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze logs using trained model')
    analyze_parser.add_argument('input', help='Input log file or directory')
    analyze_parser.add_argument('--directory', action='store_true', help='Input is a directory')
    analyze_parser.add_argument('--model-dir', default=settings.models_dir, help='Model directory')
    analyze_parser.add_argument('--output', help='Output file for results (JSON)')
    analyze_parser.set_defaults(func=analyze)
    
    # Serve command
    serve_parser = subparsers.add_parser('serve', help='Start API server')
    serve_parser.add_argument('--host', default=settings.api_host, help='API host')
    serve_parser.add_argument('--port', type=int, default=settings.api_port, help='API port')
    serve_parser.add_argument('--reload', action='store_true', help='Enable auto-reload')
    serve_parser.set_defaults(func=serve)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    args.func(args)


if __name__ == '__main__':
    main()
