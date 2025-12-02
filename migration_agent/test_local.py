#!/usr/bin/env python3
"""Test migration_agent locally without Bedrock Agent Core"""

import sys
import os

# Set up path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("LOCAL TEST: migration_agent")
print("=" * 80)
print()

# Import after path is set
from migration_agent import migration_agent

# Test query
query = "Recommend AWS services for the HLD file appa.jpeg"
print(f"Query: {query}")
print()
print("Calling migration_agent directly (not through Bedrock Agent Core)...")
print()

try:
    # Call the agent directly
    response = migration_agent(query)
    
    # Extract response text
    if hasattr(response, 'message'):
        result = response.message['content'][0]['text']
    else:
        result = str(response)
    
    print("=" * 80)
    print("AGENT RESPONSE:")
    print("=" * 80)
    print(result)
    print()
    
    # Check if input_agent was called
    if "input_agent" in result.lower() or "analyzed" in result.lower():
        print("✓ Looks like input_agent was called!")
    else:
        print("✗ input_agent might not have been called")
        
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)
