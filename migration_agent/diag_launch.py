import boto3
import json

client = boto3.client('bedrock-agent-runtime', region_name='us-east-1')

# Replace with your actual runtime ARN after deployment
response = client.invoke_agent_runtime(
    agentRuntimeArn='arn:aws:bedrock-agentcore:us-east-1:095059577505:runtime/diagram_agent-SjZNtSCaIC',  # Update this after first deployment
    input={
        "prompt":"
    },
    qualifier="DEFAULT"
)

print(json.dumps(response, indent=2, default=str))
