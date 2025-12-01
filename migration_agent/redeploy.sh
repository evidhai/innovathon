#!/bin/bash
# Redeploy migration_agent to Bedrock Agent Core

echo "=========================================="
echo "Redeploying migration_agent"
echo "=========================================="
echo ""

cd "/Users/vasan/2 Areas/Repo/innovathon/migration_agent"

echo "Step 1: Running agentcore_build.py to rebuild and redeploy..."
python agentcore_build.py

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Next step: Test with agentcore_launch.py"
echo "  python agentcore_launch.py"
echo ""
