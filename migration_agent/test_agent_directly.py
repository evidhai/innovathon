#!/usr/bin/env python3
"""Direct test of migration_agent to verify tool calling"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("Testing migration_agent tool calling behavior")
print("=" * 80)

# Import the agent
from migration_agent import migration_agent, input_agent

# Test 1: Direct tool call (should work if credentials are valid)
print("\n" + "=" * 80)
print("Test 1: Direct input_agent call")
print("=" * 80)
result = input_agent("appa.jpeg")
print(f"\nDirect tool result:\n{result}")

# Test 2: Agent invocation
print("\n" + "=" * 80)
print("Test 2: Agent invocation with file mention")
print("=" * 80)

test_query = "Recommend AWS services for the HLD file appa.jpeg"
print(f"Query: {test_query}\n")

try:
    # Enable debug mode
    import logging
    logging.getLogger("strands").setLevel(logging.DEBUG)
    
    response = migration_agent(test_query)
    
    print("\n--- Agent Response ---")
    print(response.message['content'][0]['text'])
    
    # Check if tool was called
    print("\n--- Tool Usage Analysis ---")
    if hasattr(response, 'tool_calls') or 'tool_calls' in str(response):
        print("✓ Tools were called!")
    else:
        print("✗ No tool calls detected in response")
        print(f"\nFull response object: {response}")
        
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
