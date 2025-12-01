#!/usr/bin/env python3
"""Test S3 access and input_agent function"""

import boto3
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("Step 1: Testing S3 Access")
print("=" * 80)

bucket = "innovathon-poc-docs-anz"
filename = "appa.jpeg"

try:
    s3_client = boto3.client("s3", region_name="us-east-1")
    
    # List bucket contents
    print(f"\nListing files in bucket '{bucket}':")
    response = s3_client.list_objects_v2(Bucket=bucket, MaxKeys=20)
    
    if 'Contents' in response:
        for obj in response['Contents']:
            size_kb = obj['Size'] / 1024
            print(f"  - {obj['Key']} ({size_kb:.2f} KB)")
    else:
        print("  No files found in bucket")
    
    # Check if specific file exists
    print(f"\nChecking for file '{filename}':")
    try:
        head = s3_client.head_object(Bucket=bucket, Key=filename)
        print(f"  ✓ File exists!")
        print(f"  - Size: {head['ContentLength']} bytes")
        print(f"  - Content-Type: {head.get('ContentType', 'unknown')}")
        print(f"  - Last Modified: {head['LastModified']}")
    except s3_client.exceptions.NoSuchKey:
        print(f"  ✗ File '{filename}' NOT found in bucket")
        print(f"  Available files listed above")
        sys.exit(1)
    except Exception as e:
        print(f"  ✗ Error checking file: {e}")
        sys.exit(1)
    
except Exception as e:
    print(f"\n✗ S3 Access Error: {e}")
    print(f"Error Type: {type(e).__name__}")
    sys.exit(1)

print("\n" + "=" * 80)
print("Step 2: Testing input_agent function")
print("=" * 80)

try:
    from migration_agent import input_agent
    
    print(f"\nCalling input_agent with query: 'analyze {filename}'")
    result = input_agent(f"analyze {filename}")
    
    print("\n--- Raw Result ---")
    print(result)
    
    print("\n--- Parsed JSON ---")
    result_json = json.loads(result)
    print(json.dumps(result_json, indent=2))
    
    if result_json.get("status") == "success":
        print("\n✓ SUCCESS: File analyzed successfully!")
    else:
        print(f"\n✗ ERROR: {result_json.get('message', 'Unknown error')}")
        
except Exception as e:
    print(f"\n✗ Function Test Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 80)
print("All tests completed")
print("=" * 80)
