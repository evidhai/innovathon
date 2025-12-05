import boto3
from bedrock_agentcore_starter_toolkit import Runtime
from boto3.session import Session

boto_session = Session()
region = boto_session.region_name

agentcore_runtime = Runtime()
agent_name = "diagram_agent"

# Configure the agent runtime - Generate Docker files
response = agentcore_runtime.configure(
    entrypoint="diag_test.py",
    auto_create_execution_role=True,
    auto_create_ecr=True,
    requirements_file="requirements.txt",
    region=region,
    agent_name=agent_name
)

print("Launching Bedrock AgentCore runtime...")
launch_result = agentcore_runtime.launch()


