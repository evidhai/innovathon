
import boto3
from bedrock_agentcore_starter_toolkit import Runtime
from boto3.session import Session
boto_session = Session()
region = boto_session.region_name

agentcore_runtime = Runtime()
agent_name = "migration_agent"

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

try:
    print("🚀 Starting agent runtime launch...")
    launch_result = agentcore_runtime.launch()
    print(f"✅ Launch successful!")
    print(f"Agent ID: {launch_result.agent_id}")
    print(f"ECR URI: {launch_result.ecr_uri}")
except Exception as e:
    print(f"❌ Launch failed: {e}")
    
    # Get more detailed error information
    import traceback
    print("\n📋 Full error traceback:")
    traceback.print_exc()
    
    # Check if it's a CodeBuild or runtime deployment issue
    codebuild_client = boto3.client('codebuild', region_name=region)
    
    try:
        # Get the latest CodeBuild project for this agent
        project_name = f"bedrock-agentcore-{agent_name}-builder"
        print(f"\n🔍 Checking CodeBuild project: {project_name}")
        
        builds = codebuild_client.list_builds_for_project(
            projectName=project_name,
            sortOrder='DESCENDING'
        )
        
        if builds['ids']:
            latest_build_id = builds['ids'][0]
            print(f"Latest build ID: {latest_build_id}")
            
            build_info = codebuild_client.batch_get_builds(ids=[latest_build_id])
            if build_info['builds']:
                build = build_info['builds'][0]
                print(f"\nBuild status: {build['buildStatus']}")
                print(f"Build phase: {build.get('currentPhase', 'N/A')}")
                
                if 'phases' in build:
                    print("\n📊 Build phases:")
                    for phase in build['phases']:
                        status = phase.get('phaseStatus', 'N/A')
                        phase_type = phase.get('phaseType', 'N/A')
                        print(f"  {phase_type}: {status}")
                        
                        if status == 'FAILED' and 'contexts' in phase:
                            for context in phase['contexts']:
                                if 'message' in context:
                                    print(f"    Error: {context['message']}")
    except Exception as cb_error:
        print(f"Could not retrieve CodeBuild details: {cb_error}")
    
    # Check agent runtime status
    try:
        agentcore_client = boto3.client('bedrock-agentcore-control', region_name=region)
        print("\n🔍 Checking existing agent runtimes...")
        
        response = agentcore_client.list_agent_runtimes()
        print(f"Found {len(response.get('agentRuntimes', []))} agent runtimes")
        
        for runtime in response.get('agentRuntimes', []):
            if agent_name in runtime.get('agentRuntimeName', ''):
                print(f"\nAgent: {runtime.get('agentRuntimeName')}")
                print(f"Status: {runtime.get('status')}")
                print(f"Runtime ID: {runtime.get('agentRuntimeId')}")
    except Exception as runtime_error:
        print(f"Could not retrieve agent runtime status: {runtime_error}")
    
    raise

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