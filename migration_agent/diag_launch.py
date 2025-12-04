import boto3
import json

client = boto3.client('bedrock-agent-runtime', region_name='us-east-1')

try:
    response = client.invoke_agent_runtime(
        agentRuntimeArn='arn:aws:bedrock-agentcore:us-east-1:095059577505:runtime/diagram_agent-SjZNtSCaIC',
        input={
            "prompt": "Create an AWS architecture diagram for a 3-tier web app: CloudFront -> ALB -> EC2 ASG -> RDS in private subnets, with VPC, subnets, IGW, NAT GW, and security groups as PNG"
        },
        qualifier="DEFAULT"
    )
    
    print(json.dumps(response, indent=2, default=str))
    
except client.exceptions.RuntimeClientError as e:
    print("Error code:", e.response["Error"]["Code"])
    print("Message:", e.response["Error"]["Message"])
    raise

