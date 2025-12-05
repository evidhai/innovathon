import base64
import boto3
import json
import logging
import tempfile
import threading
import time
import asyncio
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
def hld_lld_input_agent(payload):
    """
    Input agent that processes High Level Design (HLD) and Low Level Design (LLD) images
    using Amazon Nova Vision for image analysis and Amazon Titan Text for structured output.
    """
    print(f"HLD/LLD Input Agent called with payload: {payload}")

    # Initialize Bedrock client
    try:
        bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')
    except Exception as e:
        return f"Error initializing AWS Bedrock client for HLD/LLD analysis: {str(e)}. Please configure AWS credentials."

    try:
        # Extract image data from payload
        image_data = None
        image_format = "png"
        user_query = ""

        if isinstance(payload, dict):
            # Handle base64 encoded image
            if "image_data" in payload:
                image_data = payload["image_data"]
                image_format = payload.get("image_format", "png")
            elif "image_base64" in payload:
                image_data = payload["image_base64"]
                image_format = payload.get("image_format", "png")

            user_query = payload.get("query", payload.get("input", ""))
        elif isinstance(payload, str):
            user_query = payload

        if not image_data and not user_query:
            return "Please provide either an image (HLD/LLD) or a query about architecture design."

        # Process image with Nova Vision if image data is provided
        vision_analysis = ""
        if image_data:
            print("Processing image with Amazon Nova Vision...")

            # Ensure image_data is properly decoded if it's base64 string
            if isinstance(image_data, str):
                try:
                    image_bytes = base64.b64decode(image_data)
                except Exception as e:
                    return f"Error decoding image data: {str(e)}"
            else:
                image_bytes = image_data

            # Prepare Nova Vision request
            nova_request = {
                "modelId": "us.amazon.nova-pro-v1:0",
                "contentType": "application/json",
                "accept": "application/json",
                "body": json.dumps({
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "text": """Analyze this High Level Design (HLD) or Low Level Design (LLD) architecture diagram. 
                                    Extract and identify:
                                    1. System components and their relationships
                                    2. Data flow and communication patterns
                                    3. Technology stack and frameworks mentioned
                                    4. AWS Cloud equivalent services
                                    5. Integration points and APIs
                                    6. Security considerations visible
                                    7. Scalability and performance aspects
                                    8. Database and storage requirements
                                    
                                    Provide a detailed technical analysis suitable for cloud migration planning."""
                                },
                                {
                                    "image": {
                                        "format": image_format,
                                        "source": {
                                            "bytes": base64.b64encode(image_bytes).decode() if isinstance(image_bytes, bytes) else image_bytes
                                        }
                                    }
                                }
                            ]
                        }
                    ],
                    "inferenceConfig": {
                        "max_new_tokens": 2000,
                        "temperature": 0.1
                    }
                })
            }

            # Call Nova Vision
            nova_response = bedrock_client.invoke_model(**nova_request)
            nova_result = json.loads(nova_response['body'].read())
            vision_analysis = nova_result['output']['message']['content'][0]['text']
            print("✅ Nova Vision analysis completed")
            return vision_analysis

    except Exception as e:
        print(f"❌ Error in HLD/LLD analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"Error analyzing architecture diagram: {str(e)}"



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


migration_system_prompt = """You are an expert AWS Migration Specialist and Cloud Architect.
Your goal is to guide users through the complex process of migrating on-premises workloads to AWS with confidence and clarity.

### Core Responsibilities
1.  **Analyze & Assess**: deeply understand the user's existing infrastructure (from text or provided HLD/LLD images).
2.  **Consult & Clarify**: Do NOT just give a generic answer. Proactively ask for technical preferences to tailor the solution.
    *   *Server Preference*: Virtual Machines (EC2) vs. Serverless (Lambda/Fargate)?
    *   *Containerization*: ECS, EKS, or standard EC2?
    *   *Networking*: Specific VPC CIDR requirements or connectivity (Direct Connect/VPN)?
    *   *Database*: Managed (RDS/DynamoDB) vs. Self-hosted?
3.  **Recommend & Plan**: Suggest appropriate migration strategies (Re-host, Re-platform, Re-factor) and AWS services.
4.  **Cost & Best Practices**: Always consider TCO (Total Cost of Ownership) and the AWS Well-Architected Framework (Security, Reliability, Performance).

### Operational Rules
*   **Step-by-Step Approach**: Don't overwhelm the user. Break complex migrations into logical phases.
*   **Diagram Generation Constraint**: **DO NOT** generate an architecture diagram until the user has **confirmed and finalized** the proposed service stack. Use the `arch_diag_assistant` only after this confirmation.
*   **Tone**: Professional, encouraging, and technically precise but accessible.

### Workflow Example
1.  **User**: "Migrate my 3-tier app."
2.  **You**: "I can help. Is it Python/Java? Do you prefer serverless or containers? Any compliance needs?" (Gather Context)
3.  **User**: "Python, serverless."
4.  **You**: "Great. I recommend API Gateway + Lambda + DynamoDB. Here is why..." (Propose Solution)
5.  **User**: "Looks good."
6.  **You**: "Excellent. I will now generate the architecture diagram and detailed cost breakdown." (Execute Tools)
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
        use_aws,
        hld_lld_input_agent],
)
@app.entrypoint
async def migration_assistant(payload):
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
    
    # Process image if included in payload
    if isinstance(payload, dict) and ("image_data" in payload or "image_base64" in payload):
        print("📸 Image detected in payload, running visual analysis...")
        try:
            # We can call the tool function directly since it's just a python function decorated with @tool
            # But we need to pass the full payload as it expects
            vision_analysis = hld_lld_input_agent(payload)
            
            # Enrich the user input with the vision analysis
            user_input = f"""USER QUERY: {user_input}
            
VISUAL ANALYSIS OF UPLOADED IMAGE:
{vision_analysis}
            
Please use the visual analysis above to answer the user's query about the attached architecture diagram."""
            
            print("✅ Visual analysis integrated into prompt")
        except Exception as e:
            print(f"⚠️ Error processing image: {e}")
            user_input = f"{user_input}\n\n[System Note: User uploaded an image but analysis failed: {str(e)}]"

    # Process the query - run in thread pool to avoid blocking
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, migration_agent, user_input)
    
    # Return structured response
    return response.message['content'][0]['text']
    return response.message['content'][0]['text']

if __name__ == "__main__":
    app.run()