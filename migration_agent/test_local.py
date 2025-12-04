#!/usr/bin/env python3
"""
Local test script for migration_agent without AWS deployment
"""
from migration_agent import migration_assistant

def test_simple_query():
    """Test with a simple migration query"""
    print("=" * 80)
    print("Test 1: Simple migration query")
    print("=" * 80)
    
    payload = {
        "input": "Help me migrate a 3-tier web application to AWS",
        "user_id": "test_user",
        "context": {}
    }
    
    try:
        response = migration_assistant(payload)
        print("\n✅ Response:")
        print(response)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

def test_diagram_generation():
    """Test architecture diagram generation"""
    print("\n" + "=" * 80)
    print("Test 2: Architecture diagram generation")
    print("=" * 80)
    
    payload = {
        "input": "Create an AWS architecture diagram for a 3-tier web application with CloudFront, ALB, EC2 Auto Scaling, and RDS. Include VPC, public and private subnets, NAT Gateway, and security groups. Generate as PNG.",
        "user_id": "test_user_diagram",
        "context": {}
    }
    
    try:
        response = migration_assistant(payload)
        print("\n✅ Response:")
        print(response)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

def test_simple_diagram():
    """Test simple S3 CloudFront diagram"""
    print("\n" + "=" * 80)
    print("Test 3: Simple S3 + CloudFront diagram")
    print("=" * 80)
    
    payload = {
        "input": "Generate 3 tier architecture for a web application include db vpc and public ec2 flow.",
        "user_id": "test_user_simple",
        "context": {}
    }
    
    try:
        response = migration_assistant(payload)
        print("\n✅ Response:")
        print(response)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧪 Testing migration_agent locally\n")
    
    # Run tests - comment out tests you don't want to run
    # test_simple_query()
    # test_diagram_generation()
    test_simple_diagram()
    
    print("\n" + "=" * 80)
    print("✅ Test completed!")
    print("=" * 80)