#!/bin/bash
# Quick AWS credential check and fix

echo "=========================================="
echo "AWS Credentials Check"
echo "=========================================="
echo ""

# Check if credentials are valid
echo "Testing AWS credentials..."
if aws sts get-caller-identity &>/dev/null; then
    echo "✓ AWS credentials are VALID"
    echo ""
    echo "Account details:"
    aws sts get-caller-identity
    echo ""
    echo "Testing S3 bucket access..."
    if aws s3 ls s3://innovathon-poc-docs-anz/ &>/dev/null; then
        echo "✓ S3 bucket access: SUCCESS"
        echo ""
        echo "Files in bucket:"
        aws s3 ls s3://innovathon-poc-docs-anz/
    else
        echo "✗ S3 bucket access: FAILED"
        echo "Check bucket name or permissions"
    fi
else
    echo "✗ AWS credentials are INVALID or EXPIRED"
    echo ""
    echo "=========================================="
    echo "Fix Options:"
    echo "=========================================="
    echo ""
    echo "Option 1: AWS SSO Login (Recommended)"
    echo "  aws sso login"
    echo ""
    echo "Option 2: Set environment variables"
    echo "  export AWS_ACCESS_KEY_ID='...'"
    echo "  export AWS_SECRET_ACCESS_KEY='...'"
    echo "  export AWS_SESSION_TOKEN='...'  # if using temporary credentials"
    echo ""
    echo "Option 3: Update ~/.aws/credentials file"
    echo "  [default]"
    echo "  aws_access_key_id = YOUR_KEY"
    echo "  aws_secret_access_key = YOUR_SECRET"
    echo ""
fi

echo ""
echo "=========================================="
echo "Next Steps:"
echo "=========================================="
echo "1. Fix credentials using one of the options above"
echo "2. Run: python test_s3_access.py"
echo "3. Run: python test_agent_directly.py"
echo ""
