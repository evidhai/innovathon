#!/usr/bin/env python3
"""
AWS Setup Helper Script
"""
import os
import subprocess
import sys

def check_aws_cli():
    """Check if AWS CLI is available"""
    aws_paths = [
        "C:\\Program Files\\Amazon\\AWSCLIV2\\aws.exe",
        "aws"
    ]
    
    for aws_path in aws_paths:
        try:
            result = subprocess.run([aws_path, "--version"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"✅ AWS CLI found: {aws_path}")
                print(f"Version: {result.stdout.strip()}")
                return aws_path
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            continue
    
    print("❌ AWS CLI not found")
    return None

def check_aws_config():
    """Check current AWS configuration"""
    aws_path = check_aws_cli()
    if not aws_path:
        return False
    
    try:
        result = subprocess.run([aws_path, "configure", "list"], 
                              capture_output=True, text=True, timeout=10)
        print("\n📋 Current AWS Configuration:")
        print(result.stdout)
        
        if "not set" in result.stdout.lower():
            return False
        return True
    except Exception as e:
        print(f"❌ Error checking AWS config: {e}")
        return False

def setup_aws_region():
    """Set up AWS region"""
    aws_path = check_aws_cli()
    if not aws_path:
        return False
    
    try:
        # Set region
        subprocess.run([aws_path, "configure", "set", "region", "us-east-1"], 
                      timeout=10, check=True)
        subprocess.run([aws_path, "configure", "set", "output", "json"], 
                      timeout=10, check=True)
        print("✅ AWS region set to us-east-1")
        return True
    except Exception as e:
        print(f"❌ Error setting AWS region: {e}")
        return False

def setup_env_file():
    """Create or update .env file with AWS settings"""
    env_content = """# AWS Configuration
AWS_DEFAULT_REGION=us-east-1
AWS_REGION=us-east-1

# Add your AWS credentials here:
# AWS_ACCESS_KEY_ID=your_access_key_here
# AWS_SECRET_ACCESS_KEY=your_secret_key_here

# Optional: If using temporary credentials
# AWS_SESSION_TOKEN=your_session_token_here

# For local development, you can also use:
# AWS_PROFILE=default
"""
    
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ Created .env file with AWS region settings")
        return True
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

def main():
    print("🔧 AWS Setup Helper")
    print("=" * 50)
    
    # Check AWS CLI
    aws_path = check_aws_cli()
    if not aws_path:
        print("\n❌ AWS CLI not found. Please install AWS CLI first:")
        print("https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html")
        return False
    
    # Check current config
    print("\n🔍 Checking AWS Configuration...")
    has_config = check_aws_config()
    
    # Set up region
    print("\n⚙️ Setting up AWS region...")
    setup_aws_region()
    
    # Create .env file
    print("\n📝 Setting up .env file...")
    setup_env_file()
    
    print("\n" + "=" * 50)
    print("🎯 Next Steps:")
    
    if not has_config:
        print("\n1. 📋 Configure AWS credentials using one of these methods:")
        print("   Method A - AWS CLI:")
        print(f'   {aws_path} configure')
        print("   (You'll need your AWS Access Key ID and Secret Access Key)")
        print()
        print("   Method B - Environment variables in .env file:")
        print("   Edit .env file and add your AWS credentials")
        print()
        print("   Method C - AWS SSO:")
        print(f'   {aws_path} configure sso')
        print()
    
    print("2. 🚀 Run the application:")
    print("   venv_new\\Scripts\\streamlit.exe run app.py --server.port 8502")
    
    print("\n💡 For testing without AWS credentials, use:")
    print("   venv_new\\Scripts\\streamlit.exe run app_demo.py --server.port 8503")

if __name__ == "__main__":
    main()