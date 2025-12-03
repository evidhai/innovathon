
import boto3
from bedrock_agentcore_starter_toolkit import Runtime
from boto3.session import Session
boto_session = Session()
region = boto_session.region_name

agentcore_runtime = Runtime()
agent_name = "migration_agent_test"

### To Configure the agent runtime - Generate Docker files
response = agentcore_runtime.configure(
    entrypoint="migration_agent.py",
    auto_create_execution_role=True,
    auto_create_ecr=True,
    requirements_file="requirements.txt",
    region=region,
    agent_name=agent_name
)
response

### To Launch the agent runtime

launch_result = agentcore_runtime.launch()

### For Cleanup 

# launch_result.ecr_uri, launch_result.agent_id, launch_result.ecr_uri.split('/')[1]

# agentcore_control_client = boto3.client(
#     'bedrock-agentcore-control',
#     region_name=region
# )
# ecr_client = boto3.client(
#     'ecr',
#     region_name=region
    
# )

# runtime_delete_response = agentcore_control_client.delete_agent_runtime(
#     agentRuntimeId=launch_result.agent_id,
    
# )

# response = ecr_client.delete_repository(
#     repositoryName=launch_result.ecr_uri.split('/')[1],
#     force=True
# )