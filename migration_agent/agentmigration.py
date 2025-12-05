import base64
import boto3
import json
import logging
import os
import tempfile
import threading
import time
from datetime import timedelta
from pathlib import Path
from uuid import uuid4
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set default AWS region if not set
if not os.environ.get('AWS_DEFAULT_REGION'):
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
if not os.environ.get('AWS_REGION'):
    os.environ['AWS_REGION'] = 'us-east-1'
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
try:
    memory_client = MemoryClient()
    print("✅ Memory client initialized successfully")
except Exception as e:
    print(f"⚠️ Warning: Could not initialize memory client: {e}")
    print("This might be due to missing AWS credentials. The app will work with limited functionality.")
    memory_client = None

# Create a custom hook provider for session memory
class SessionMemoryHookProvider(HookProvider):
    """Hook provider for session-based memory using Agent Core Memory"""
    
    def __init__(self, memory_client):
        self.memory_client = memory_client
        self.session_id = None
    
    def on_agent_initialized(self, event: AgentInitializedEvent):
        """Initialize session when agent starts"""
        print("🧠 Initializing session memory...")
    
    def on_message_added(self, event: MessageAddedEvent):
        """Store messages in session memory"""
        if self.session_id and self.memory_client:
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
        elif not self.memory_client:
            print("⚠️ Memory client not available - running without session memory")

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
        try:
            bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')
        except Exception as e:
            return f"Error initializing AWS Bedrock client: {str(e)}. Please configure AWS credentials."
        
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
                                    4. Infrastructure requirements
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
        
        # Step 2: Get cost information for identified components
        print("🔍 Gathering cost information for identified components...")
        cost_analysis = ""
        if vision_analysis:
            # Extract key components from vision analysis for cost estimation
            cost_query = f"""Based on this architecture analysis: {vision_analysis[:1000]}
            
            Provide cost estimates for migrating this system to AWS. Focus on:
            1. Compute costs (EC2 instances based on workload)
            2. Database costs (RDS or other database services)
            3. Storage costs (EBS, S3)
            4. Network costs (Load Balancers, Data Transfer)
            5. Additional services costs
            
            Provide monthly cost estimates and optimization recommendations."""
            
            try:
                cost_analysis = cost_assistant(cost_query)
                print("✅ Cost analysis completed")
            except Exception as e:
                print(f"⚠️ Cost analysis failed: {e}")
                cost_analysis = "Cost analysis unavailable - please check AWS pricing manually."
        
        # Step 3: Get AWS documentation and best practices
        print("📚 Gathering AWS migration best practices and documentation...")
        docs_analysis = ""
        if vision_analysis:
            # Get relevant AWS documentation
            docs_query = f"""Based on this system architecture: {vision_analysis[:1000]}
            
            Provide AWS migration guidance including:
            1. Recommended AWS services for each component
            2. Migration tools and methodologies
            3. Best practices for this type of architecture
            4. Security and compliance considerations
            5. Performance optimization strategies"""
            
            try:
                docs_analysis = aws_docs_assistant(docs_query)
                print("✅ Documentation analysis completed")
            except Exception as e:
                print(f"⚠️ Documentation analysis failed: {e}")
                docs_analysis = "Documentation analysis unavailable - please refer to AWS documentation manually."
        
        # Step 4: Process with Titan Text for structured output
        print("📝 Generating comprehensive migration strategy with Titan Text...")
        
        # Combine all analyses
        combined_input = f"""
        User Query: {user_query}
        
        Architecture Vision Analysis: {vision_analysis}
        
        Cost Analysis: {cost_analysis}
        
        AWS Documentation & Best Practices: {docs_analysis}
        
        Based on the comprehensive analysis above, create a detailed structured JSON output for migration planning.
        """
        
        titan_request = {
            "modelId": "amazon.titan-text-premier-v1:0",
            "contentType": "application/json",
            "accept": "application/json",
            "body": json.dumps({
                "inputText": f"""{combined_input}
                
                Create a comprehensive JSON structure for AWS migration planning with the following format:
                {{
                    "architecture_analysis": {{
                        "system_type": "string",
                        "complexity_level": "low|medium|high",
                        "components": [
                            {{
                                "name": "string",
                                "type": "string",
                                "current_technology": "string",
                                "aws_equivalent": "string",
                                "migration_complexity": "low|medium|high"
                            }}
                        ],
                        "data_flows": [
                            {{
                                "source": "string",
                                "destination": "string",
                                "protocol": "string",
                                "data_type": "string"
                            }}
                        ]
                    }},
                    "migration_strategy": {{
                        "recommended_approach": "lift-and-shift|re-platform|refactor|rebuild",
                        "migration_phases": [
                            {{
                                "phase": "string",
                                "components": ["string"],
                                "estimated_duration": "string",
                                "dependencies": ["string"]
                            }}
                        ],
                        "aws_services": [
                            {{
                                "service": "string",
                                "purpose": "string",
                                "configuration_notes": "string"
                            }}
                        ]
                    }},
                    "infrastructure_requirements": {{
                        "compute": {{
                            "instance_types": ["string"],
                            "scaling_requirements": "string"
                        }},
                        "storage": {{
                            "types": ["string"],
                            "capacity_estimate": "string"
                        }},
                        "networking": {{
                            "vpc_requirements": "string",
                            "connectivity_needs": ["string"]
                        }}
                    }},
                    "cost_estimation": {{
                        "monthly_estimate_range": "string",
                        "cost_optimization_opportunities": ["string"]
                    }},
                    "security_considerations": {{
                        "current_security_measures": ["string"],
                        "aws_security_services": ["string"],
                        "compliance_requirements": ["string"]
                    }},
                    "risks_and_challenges": [
                        {{
                            "risk": "string",
                            "impact": "low|medium|high",
                            "mitigation": "string"
                        }}
                    ],
                    "next_steps": ["string"]
                }}
                
                Ensure the JSON is valid and comprehensive for migration planning.""",
                "textGenerationConfig": {
                    "maxTokenCount": 3000,
                    "temperature": 0.1,
                    "topP": 0.9
                }
            })
        }
        
        # Call Titan Text
        titan_response = bedrock_client.invoke_model(**titan_request)
        titan_result = json.loads(titan_response['body'].read())
        structured_output = titan_result['results'][0]['outputText']
        
        print("✅ Titan Text structured output generated")
        
        # Try to parse and validate JSON
        try:
            parsed_json = json.loads(structured_output)
            formatted_json = json.dumps(parsed_json, indent=2)
            
            result = f"""## 🎯 Comprehensive HLD/LLD Migration Analysis

### 🔍 Architecture Vision Analysis:
{vision_analysis[:800]}{'...' if len(vision_analysis) > 800 else ''}

### 💰 Cost Analysis & Optimization:
{cost_analysis[:800]}{'...' if len(cost_analysis) > 800 else ''}

### 📚 AWS Best Practices & Documentation:
{docs_analysis[:800]}{'...' if len(docs_analysis) > 800 else ''}

### 📋 Structured Migration Plan:
```json
{formatted_json}
```

### 🎯 Key Migration Insights:
- **Architecture Complexity**: {parsed_json.get('architecture_analysis', {}).get('complexity_level', 'Unknown')}
- **Recommended Approach**: {parsed_json.get('migration_strategy', {}).get('recommended_approach', 'Unknown')}
- **AWS Services Identified**: {len(parsed_json.get('migration_strategy', {}).get('aws_services', []))} services
- **Migration Phases**: {len(parsed_json.get('migration_strategy', {}).get('migration_phases', []))} phases planned

### 🚀 Next Steps:
This comprehensive analysis combines AI vision processing, cost optimization, and AWS best practices to provide you with a complete migration roadmap. Use this structured data for detailed planning and implementation.
"""
            
        except json.JSONDecodeError:
            result = f"""## 🎯 Comprehensive HLD/LLD Migration Analysis

### 🔍 Architecture Vision Analysis:
{vision_analysis}

### 💰 Cost Analysis & Optimization:
{cost_analysis}

### 📚 AWS Best Practices & Documentation:
{docs_analysis}

### 📋 Migration Strategy Output:
{structured_output}

### ⚠️ Note: 
The structured output may need JSON formatting validation, but the comprehensive analysis above provides detailed migration guidance combining AI vision processing, cost optimization, and AWS best practices.
"""
        
        return result
        
    except Exception as e:
        error_msg = f"Error in HLD/LLD Input Agent: {str(e)}"
        print(f"❌ {error_msg}")
        return f"**Error**: {error_msg}\n\nPlease ensure the image is properly formatted and try again."


migration_system_prompt = """You are an AWS Migration Specialist.
Help users plan and execute migrations from on-premises to AWS cloud.
Your responsibilities:
- Assess on-premises workloads and recommend AWS migration strategies
- Identify suitable AWS services for migrated workloads
- Provide best practices for migration planning and execution
- Address common migration challenges and solutions
- Process High Level Design (HLD) and Low Level Design (LLD) diagrams for comprehensive migration analysis

Available tools:
- hld_lld_input_agent: Comprehensive architecture analysis using Nova Vision, cost analysis, AWS documentation, and Titan Text for complete migration planning
- cost_assistant: Get AWS pricing information and cost optimization recommendations
- aws_docs_assistant: Search AWS documentation for service information and best practices
- arch_diag_assistant: Generate AWS architecture diagrams
- image_reader: Read and analyze images
- use_aws: Execute AWS CLI commands and operations

Enhanced HLD/LLD Analysis Workflow:
1. Nova Vision analyzes uploaded architecture diagrams
2. Cost assistant provides pricing and optimization recommendations
3. AWS docs assistant gathers relevant best practices and migration guidance
4. Titan Text generates comprehensive structured migration plans

When assisting with migrations: 
- Analyze on-premises architecture and dependencies 
- Use the hld_lld_input_agent for comprehensive analysis when users provide architecture diagrams
- The HLD/LLD agent automatically integrates cost analysis and AWS best practices
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
        hld_lld_input_agent,
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
    try:
        # Invoke the migration agent with the provided payload
        # Handle both dict and string inputs
        if isinstance(payload, str):
            user_input = payload
            user_id = "unknown"
            context = {}
            image_data = None
            image_format = None
        else:
            user_input = payload.get("input") or payload.get("prompt")
            user_id = payload.get("user_id", "unknown")
            context = payload.get("context", {})
            image_data = payload.get("image_data")
            image_format = payload.get("image_format", "png")
        
        # Create or retrieve session ID
        session_id = context.get("session_id") or f"session_{user_id}_{int(time.time())}"
        if session_memory_provider:
            session_memory_provider.session_id = session_id
        
        print(f"User ID: {user_id}")
        print(f"Session ID: {session_id}")
        print(f"Input: {user_input}")
        print(f"Has Image Data: {bool(image_data)}")
        
        # If image data is provided, use the HLD/LLD input agent directly
        if image_data and ('analyze' in user_input.lower() or 'hld' in user_input.lower() or 'lld' in user_input.lower()):
            print("🖼️ Processing with HLD/LLD Input Agent...")
            hld_payload = {
                "image_data": image_data,
                "image_format": image_format,
                "query": user_input
            }
            response_text = hld_lld_input_agent(hld_payload)
            return response_text
        
        # For regular queries, process with the migration agent
        # Note: Session memory retrieval is handled automatically by the hook provider
        # The memory_client stores messages via the MessageAddedEvent hook
        # No need to manually retrieve and prepend history
        
        # Process the query
        response = migration_agent(user_input)
        
        # Return structured response
        return response.message['content'][0]['text']
        
    except Exception as e:
        error_msg = f"Error in migration assistant: {str(e)}"
        print(f"❌ {error_msg}")
        
        # Fallback to demo mode if there are AWS credential issues
        if "credentials" in str(e).lower() or "aws" in str(e).lower():
            print("🔄 Falling back to demo mode...")
            try:
                from migration_agent_demo import migration_assistant_demo
                return migration_assistant_demo(payload)
            except Exception as demo_error:
                return f"**Error**: {error_msg}\n\n**Demo Fallback Error**: {str(demo_error)}\n\nPlease configure AWS credentials or use the demo version."
        
        return f"**Error**: {error_msg}\n\nPlease check your configuration and try again."

if __name__ == "__main__":
    app.run()