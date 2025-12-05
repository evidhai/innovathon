#!/usr/bin/env python3
"""
Local test script for migration agent without AWS dependencies
"""
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test basic imports"""
    try:
        import streamlit
        print("✅ Streamlit imported successfully")
        
        import boto3
        print("✅ Boto3 imported successfully")
        
        from strands import Agent
        print("✅ Strands Agent imported successfully")
        
        from PIL import Image
        print("✅ PIL imported successfully")
        
        print("\n🎉 All basic imports successful!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality without AWS calls"""
    try:
        # Test basic Python functionality
        import json
        import base64
        
        # Test JSON handling
        test_data = {"test": "data", "number": 123}
        json_str = json.dumps(test_data)
        parsed = json.loads(json_str)
        assert parsed == test_data
        print("✅ JSON handling works")
        
        # Test base64 encoding
        test_string = "Hello, World!"
        encoded = base64.b64encode(test_string.encode()).decode()
        decoded = base64.b64decode(encoded).decode()
        assert decoded == test_string
        print("✅ Base64 encoding/decoding works")
        
        print("\n🎉 Basic functionality tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Functionality test error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Migration Agent Setup...")
    print("=" * 50)
    
    success = True
    
    print("\n📦 Testing Imports...")
    success &= test_imports()
    
    print("\n⚙️ Testing Basic Functionality...")
    success &= test_basic_functionality()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! Your environment is ready.")
        print("\n📝 Next steps:")
        print("1. Configure AWS credentials in .env file")
        print("2. Run: venv_new\\Scripts\\streamlit.exe run app.py")
    else:
        print("❌ Some tests failed. Please check the errors above.")