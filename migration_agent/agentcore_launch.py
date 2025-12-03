import boto3
import json

client = boto3.client('bedrock-agentcore', region_name='us-east-1')
payload = json.dumps({
        "input": "Hello what is ec2",
        "user_id": "test_user",
        "session_id": "34567897890123456789012345678901234",
        "context": {}
    })

try:
    response = client.invoke_agent_runtime(
        agentRuntimeArn='arn:aws:bedrock-agentcore:us-east-1:095059577505:runtime/migration_agent-yss0vU3nxI',
        runtimeSessionId='dfmeoagmreaklgmrkleafremoigrmtesogmtrskhmtkrlshmtyurtq',  # Must be 33+ chars
        payload=payload,
        qualifier="DEFAULT"  # Optional
    )
    
    response_body = response['response'].read()
    response_data = json.loads(response_body)
    print("Agent Response:", response_data)
    
except client.exceptions.RuntimeClientError as e:
    print("Error code:", e.response["Error"]["Code"])
    print("Message:", e.response["Error"]["Message"])
    raise
