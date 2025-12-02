#!/bin/bash

ROLE_NAME="AmazonBedrockAgentCoreSDKRuntime-us-east-1-1f9cc3803e"
POLICY_NAME="BedrockAgentCoreS3ReadAccess"

echo "Adding S3 read permissions to role: $ROLE_NAME"

# Create or update inline policy
aws iam put-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-name "$POLICY_NAME" \
  --policy-document file://s3-read-policy.json

if [ $? -eq 0 ]; then
  echo "✅ S3 read permissions added successfully"
  echo ""
  echo "The agent can now read from s3://innovathon-poc-docs-anz/"
  echo ""
  echo "Test again with: python agentcore_launch.py"
else
  echo "❌ Failed to add S3 permissions"
  exit 1
fi
