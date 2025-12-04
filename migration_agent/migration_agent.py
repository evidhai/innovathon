import base64
import boto3
import json
import logging
import tempfile
import threading
import time
from datetime import timedelta
from pathlib import Path
from uuid import uuid4
from mcp import StdioServerParameters, stdio_client
from mcp.client.streamable_http import streamablehttp_client
from mcp.server import FastMCP
from strands import Agent, tool
from strands_tools import image_reader, use_aws
from strands.tools.mcp import MCPClient
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands.hooks import AgentInitializedEvent, HookProvider, MessageAddedEvent
from bedrock_agentcore.memory import MemoryClient
from strands.models import BedrockModel
import jschema_to_python


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = BedrockAgentCoreApp()

# Initialize memory client for session management
memory_client = MemoryClient()

# Create a custom hook provider for session memory
class SessionMemoryHookProvider(HookProvider):
    """Hook provider for session-based memory using Agent Core Memory"""
    
    def __init__(self, memory_client: MemoryClient):
        self.memory_client = memory_client
        self.session_id = None
    
    def on_agent_initialized(self, event: AgentInitializedEvent):
        """Initialize session when agent starts"""
        print("🧠 Initializing session memory...")
    
    def on_message_added(self, event: MessageAddedEvent):
        """Store messages in session memory"""
        if self.session_id:
            try:
                # Store the message in session memory
                message_content = str(event.message.get('content', ''))
                role = event.message.get('role', 'user')
                
                # Add to memory with session context
                self.memory_client.add_memory(
                    session_id=self.session_id,
                    memory_type="short_term",
                    content={
                        "role": role,
                        "content": message_content,
                        "timestamp": time.time()
                    }
                )
                print(f"💾 Stored {role} message in session memory")
            except Exception as e:
                print(f"⚠️ Failed to store message in memory: {e}")

# Create session memory provider (no registry needed - pass directly to Agent)
session_memory_provider = SessionMemoryHookProvider(memory_client)

# Directory for storing generated diagrams - dynamic path based on script location
import os
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DIAGRAM_OUTPUT_DIR = Path(os.path.join(SCRIPT_DIR, "generated-diagrams"))
DIAGRAM_OUTPUT_DIR.mkdir(exist_ok=True)

@tool
def arch_diag_assistant(payload):
    """
    A Senior AWS Solutions Architect specializing in architecture diagrams.
    Creates PNG architecture diagrams using AWS Diagram MCP server and optionally 
    generates visual diagrams using Amazon Titan Image Generator.
    """
    print(f"arch_diag_assistant called with payload: {payload}")
    print(f"Diagram output directory: {DIAGRAM_OUTPUT_DIR}")
    
    # Track existing files before generation
    import glob
    tmp_diagram_dir = Path("/tmp/generated-diagrams")
    existing_files = set()
    if tmp_diagram_dir.exists():
        existing_files = set(tmp_diagram_dir.glob("*.png"))
    
    # Connect to AWS Diagram MCP server with required dependencies
    diagram_mcp_client = MCPClient(
        lambda: stdio_client(
            StdioServerParameters(
                command="uvx",
                args=[
                    "--with", "jschema-to-python",
                    "awslabs.aws-diagram-mcp-server@latest"
                ]
            )
        )
    )
    
    print("Initializing architecture diagram agent with AWS diagram tools...")
    
    # Keep the context manager alive
    with diagram_mcp_client:
        # Get the tools from the MCP server
        diagram_tools = diagram_mcp_client.list_tools_sync()
        print(f"Loaded {len(diagram_tools)} diagram tools from AWS diagram server")
        
        # Create an agent with diagram tools using Claude (NOT Titan - Titan can't use tools)
        bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')
        
        agent = Agent(
            model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",  # Claude can use tools
            tools=diagram_tools,
            system_prompt="""You are a Senior AWS Solutions Architect specializing in architecture diagrams.
            Your role is to create professional, well-structured AWS architecture diagrams that follow best practices.
            
            When designing architectures:
            - Use the generate_diagram tool ONCE to create a clear, professional architecture diagram in PNG format
            - Follow AWS Well-Architected Framework principles
            - Include appropriate AWS services for high availability, scalability, and fault tolerance
            - Organize components into logical layers (presentation, application, data, etc.)
            - Show VPC boundaries, availability zones, and security groups where relevant
            - Include proper networking components (load balancers, NAT gateways, VPC endpoints)
            - Add monitoring and logging services (CloudWatch, CloudTrail)
            - Consider security best practices (IAM, encryption, least privilege)
            - Use industry-standard naming conventions and clear labels
            - Generate only ONE diagram per request
            
            IMPORTANT: Call the generate_diagram tool only once. Do not create multiple versions or iterations.
            Generate production-ready, enterprise-grade architecture diagrams that demonstrate deep AWS expertise.
            """)
        
        print("Agent initialized successfully!")
        
        # Process the query with the diagram agent
        response = agent(payload)
        
        # Extract text and any image payloads returned by the MCP tools
        text_parts = []
        saved_images = []
        
        for part in response.message.get("content", []):
            if part.get("type") == "text" and "text" in part:
                text_content = part["text"]
                text_parts.append(text_content)
                continue
            
            # Handle base64-encoded image parts from tools/models
            b64_data = part.get("data") or part.get("base64_data") or part.get("base64")
            if b64_data:
                try:
                    image_bytes = base64.b64decode(b64_data)
                    ext = (part.get("format") or "png").replace(".", "")
                    filename = (
                        DIAGRAM_OUTPUT_DIR
                        / f"diagram_{uuid4().hex[:8]}_{int(time.time())}.{ext}"
                    )
                    with open(filename, "wb") as f:
                        f.write(image_bytes)
                    saved_images.append(str(filename))
                    print(f"✅ Saved diagram to {filename}")
                except Exception as e:
                    text_parts.append(f"[Warning] Failed to decode image payload: {e}")
        
        # Check if MCP tool saved files to /tmp and copy them to our output directory
        if tmp_diagram_dir.exists():
            new_files = set(tmp_diagram_dir.glob("*.png")) - existing_files
            print(f"Found {len(new_files)} new diagram(s) in /tmp/generated-diagrams")
            
            for tmp_file in new_files:
                try:
                    import shutil
                    # Create a clean filename
                    dest_filename = DIAGRAM_OUTPUT_DIR / tmp_file.name
                    shutil.copy2(tmp_file, dest_filename)
                    saved_images.append(str(dest_filename))
                    print(f"✅ Copied diagram from /tmp to {dest_filename}")
                except Exception as e:
                    print(f"⚠️ Failed to copy {tmp_file}: {e}")
        
        # Fallback if no structured text was returned
        if not text_parts and isinstance(response.message, dict):
            fallback = response.message.get("content") or response.message
            text_parts.append(str(fallback))
        
        result = "\n\n".join(text_parts).strip()
        if saved_images:
            result = f"{result}\n\n📁 Saved diagram files:\n" + "\n".join(f"  - {img}" for img in saved_images)
        
        return result   

@tool
def cost_assistant(payload):
    """
    An AWS Cost Optimization Assistant that helps users understand AWS service pricing,
    cost recommendations, and migration strategies from on-premises to cloud.
    """
    # Connect to an MCP server using stdio transport
    stdio_mcp_client = MCPClient(
        lambda: stdio_client(
            StdioServerParameters(
                command="uvx", args=["awslabs.aws-pricing-mcp-server@latest"]
            )
        )
    )

    print("Initializing agent with AWS pricing tools...")

    # Keep the context manager alive
    with stdio_mcp_client:
        # Get the tools from the MCP server
        tools = stdio_mcp_client.list_tools_sync()

        print(f"Loaded {len(tools)} tools from AWS pricing server")

        # Create an agent with these tools
        agent = Agent(
            model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
            tools=tools,
            system_prompt="""You are an AWS Cost Optimization Assistant.
            Help users understand AWS service pricing, cost recommendations, and migration strategies from on-premises to cloud.

            Your responsibilities:
            - Analyze AWS service pricing and provide cost estimates
            - Compare AWS services with on-premises equivalent solutions
            - Identify cost optimization opportunities (Reserved Instances, Savings Plans, right-sizing)
            - Recommend cost-effective AWS service alternatives
            - Explain pricing models (on-demand, reserved, spot instances)
            - Calculate TCO (Total Cost of Ownership) for cloud migrations
            - Suggest cost allocation strategies and tagging best practices

            When providing recommendations:
            - Use the AWS pricing tools to fetch current pricing data
            - Compare costs across different AWS regions
            - Consider on-premises infrastructure costs (hardware, power, cooling, staff)
            """)

        print("Agent initialized successfully!")

        # Invoke the agent with the provided payload
        response = agent(payload)
        return response.message['content'][0]['text']
    
@tool
def aws_docs_assistant(payload):
    """
    An AWS Documentation Assistant that helps users understand AWS services,
    features, and best practices using AWS documentation tools.
    """
    # Connect to an MCP server using stdio transport
    stdio_mcp_client = MCPClient(
        lambda: stdio_client(
            StdioServerParameters(
                command="uvx", args=["awslabs.aws-documentation-mcp-server@latest"]
            )
        )
    )

    print("Initializing agent with AWS documentation tools...")

    # Keep the context manager alive
    with stdio_mcp_client:
        # Get the tools from the MCP server
        tools = stdio_mcp_client.list_tools_sync()

        print(f"Loaded {len(tools)} tools from AWS documentation server")

        # Create an agent with these tools
        agent = Agent(
            model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
            tools=tools,
            system_prompt="""You are an AWS Documentation Assistant. 
            Help users understand AWS services, features, and best practices.
            Use the AWS documentation tools to search for accurate, up-to-date information.
            When answering questions:
            - Search the documentation to provide accurate information
            - Cite specific AWS services and features, keep it one liner
            - Provide clear, practical examples when possible
            - If you're unsure, use the search tool to find the answer
            - Keep it simple for beginners, relatable to users from onprem to cloud-native
            """)

        print("Agent initialized successfully!")

        # Invoke the agent with the provided payload
        response = agent(payload)
        return response.message['content'][0]['text']


migration_system_prompt = """You are an AWS Migration Specialist.
Help users plan and execute migrations from on-premises to AWS cloud.
Your responsibilities:
- Assess on-premises workloads and recommend AWS migration strategies
- Identify suitable AWS services for migrated workloads
- Provide best practices for migration planning and execution
- Address common migration challenges and solutions
When assisting with migrations: 
- Analyze on-premises architecture and dependencies 
- Recommend AWS services that align with workload requirements
- Suggest migration tools and methodologies (lift-and-shift, re-platforming, refactoring)
- Provide cost estimates and optimization strategies for cloud deployments
- Ensure security and compliance considerations are addressed
- Offer practical, actionable advice tailored to the user's environment
- Keep responses clear and concise for users new to cloud migrations
"""

migration_agent = Agent(
    model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    system_prompt=migration_system_prompt,
    hooks=[session_memory_provider],  # Pass hook provider directly as a list
    tools=[
        cost_assistant,
        aws_docs_assistant,
        arch_diag_assistant,
        image_reader,
        use_aws],
)

@app.entrypoint
def migration_assistant(payload):
    """
    An AWS Migration Specialist that helps users plan and execute migrations from on-premises to AWS cloud.
    """
    # Invoke the migration agent with the provided payload
    # Handle both dict and string inputs
    if isinstance(payload, str):
        user_input = payload
        user_id = "unknown"
        context = {}
    else:
        user_input = payload.get("input") or payload.get("prompt")
        user_id = payload.get("user_id", "unknown")
        context = payload.get("context", {})
    
    # Create or retrieve session ID
    session_id = context.get("session_id") or f"session_{user_id}_{int(time.time())}"
    session_memory_provider.session_id = session_id
    
    print(f"User ID: {user_id}")
    print(f"Session ID: {session_id}")
    print(f"Input: {user_input}")
    
    # Note: Session memory retrieval is handled automatically by the hook provider
    # The memory_client stores messages via the MessageAddedEvent hook
    # No need to manually retrieve and prepend history
    
    # Process the query
    response = migration_agent(user_input)
    
    # Return structured response
    return response.message['content'][0]['text']

if __name__ == "__main__":
    app.run()