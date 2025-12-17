#!/usr/bin/env python
"""
Demonstration of Dynamic Session Identifier Configuration

This script shows how to use the dynamic session identifier configuration feature
to change which field is used to group logs into sessions.
"""

import requests
import json
from datetime import datetime, timedelta

API_BASE_URL = "http://localhost:8000"


def print_section(title):
    """Print a section header"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}\n")


def get_session_field():
    """Get the current session identifier field"""
    response = requests.get(f"{API_BASE_URL}/config/session-field")
    return response.json()


def set_session_field(field_name):
    """Set the session identifier field"""
    response = requests.post(
        f"{API_BASE_URL}/config/session-field",
        json={"session_field": field_name}
    )
    return response.json()


def demonstrate_configuration():
    """Demonstrate the configuration API"""
    
    print_section("Step 1: Check Current Configuration")
    config = get_session_field()
    print(f"Current session field: {config['data']['session_field']}")
    
    print_section("Step 2: Update to Use 'token' Field")
    result = set_session_field("token")
    print(f"Update result: {result['message']}")
    print(f"New session field: {result['data']['session_field']}")
    
    print_section("Step 3: Verify Configuration Persisted")
    config = get_session_field()
    print(f"Verified session field: {config['data']['session_field']}")
    
    print_section("Step 4: Try Different Field - 'order_id'")
    result = set_session_field("order_id")
    print(f"Update result: {result['message']}")
    print(f"New session field: {result['data']['session_field']}")
    
    print_section("Step 5: Reset to Default 'session_id'")
    result = set_session_field("session_id")
    print(f"Update result: {result['message']}")
    print(f"New session field: {result['data']['session_field']}")
    
    print_section("Example Use Cases")
    print("Common session identifier fields:")
    print("  • session_id    - Traditional web sessions")
    print("  • token         - Token-based authentication")
    print("  • order_id      - E-commerce transactions")
    print("  • transaction_id - Banking/payment systems")
    print("  • correlation_id - Distributed tracing")
    print("  • request_id    - HTTP request tracking")
    print("  • user_id       - User activity tracking")


def main():
    """Main demonstration function"""
    try:
        print("\n" + "="*60)
        print(" Dynamic Session Identifier Configuration Demo")
        print("="*60)
        print("\nMake sure the API server is running on localhost:8000")
        print("Start with: python -m uvicorn auto_rca.api.main:app --host 127.0.0.1 --port 8000")
        print("\nPress Enter to continue or Ctrl+C to exit...")
        input()
        
        demonstrate_configuration()
        
        print_section("Demo Complete!")
        print("The session identifier configuration is now persisted in data/config.db")
        print("This setting will be used by the SessionGrouper when processing logs.")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to API server")
        print("Please start the server first:")
        print("  python -m uvicorn auto_rca.api.main:app --host 127.0.0.1 --port 8000")
    except KeyboardInterrupt:
        print("\n\nDemo cancelled by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
