import base64
import boto3
import json
import logging
import tempfile
import shutil
import time
from datetime import timedelta
from pathlib import Path
from typing import Dict, List, Any
from uuid import uuid4
from mcp import StdioServerParameters, stdio_client
from mcp.client.streamable_http import streamablehttp_client
from mcp.server import FastMCP
from strands import Agent, tool
from strands_tools import generate_image, image_reader , use_aws
from strands.tools.mcp import MCPClient
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands.hooks import AgentInitializedEvent, HookProvider, MessageAddedEvent
from bedrock_agentcore.memory import MemoryClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = BedrockAgentCoreApp()

# In-memory storage for processed documents
agentcore_memory: Dict[str, Dict[str, Any]] = {}

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


# @tool
# def input_agent(query: str) -> str:
#     """
#     Analyzes architecture diagrams from S3 bucket 'innovathon-poc-docs-anz' using image_reader tool.
    
#     This tool processes HLD/LLD diagrams and extracts:
#     - Text and architecture components from images
#     - Relationships, services, and design patterns
#     - Returns structured analysis as JSON
    
#     Args:
#         query: Filename in the S3 bucket (e.g., 'appa.jpeg', 'diagram.png')
    
#     Returns:
#         JSON string with extracted architecture information
    
#     Example:
#         "Analyze the file appa.jpeg"
#     """
#     logger.info(f"input_agent called with query: {query}")
    
#     # Default S3 bucket
#     bucket = "innovathon-poc-docs-anz"
    
#     # Extract filename from query
#     import re
#     filename_match = re.search(r'([\w\-\.]+\.(?:png|jpg|jpeg|pdf|gif))', query, re.IGNORECASE)
    
#     if not filename_match:
#         return json.dumps({
#             "status": "error",
#             "message": f"Could not extract filename from query. Please specify a file like 'appa.jpeg'. Query: {query}"
#         })
    
#     filename = filename_match.group(1)
#     logger.info(f"Extracted filename: {filename}")
    
#     # Construct S3 URI
#     s3_uri = f"s3://{bucket}/{filename}"
#     logger.info(f"Analyzing image from: {s3_uri}")
    
#     try:
#         # Create an agent with image_reader tool to analyze the S3 image
#         from strands_tools import image_reader as image_reader_tool
        
#         analysis_prompt = f"""Analyze this architecture diagram comprehensively. Extract:

# 1. All visible text and labels
# 2. System components and their relationships
# 3. Data flows and integrations
# 4. Infrastructure elements (servers, databases, networks)
# 5. Security components
# 6. Technology stack identified

# Provide the analysis in JSON format with keys:
# - components: list of all components
# - data_flows: list of data movement patterns
# - integrations: external systems
# - infrastructure: servers, databases, networks
# - technologies: identified tech stack
# - architecture_pattern: detected pattern (microservices, monolith, etc.)
# - extracted_text: all visible text"""

#         # Create a simple agent to use image_reader tool
#         logger.info("Creating analysis agent with image_reader tool...")
#         analysis_agent = Agent(
#             model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
#             tools=[image_reader_tool],
#             system_prompt="You are an architecture diagram analyzer. Use the image_reader tool to analyze images from S3."
#         )
        
#         # Call the agent with the analysis request
#         logger.info(f"Calling agent to analyze {s3_uri}...")
#         agent_query = f"Use the image_reader tool to analyze the image at {s3_uri}. {analysis_prompt}"
#         response = analysis_agent(agent_query)
        
#         # Extract the analysis result
#         analysis_result = response.message['content'][0]['text']
#         logger.info(f"✓ Analysis completed, length: {len(analysis_result)}")
        
#         # Parse the result
#         try:
#             analysis_json = json.loads(analysis_result)
#         except json.JSONDecodeError:
#             # If not valid JSON, wrap it
#             analysis_json = {
#                 "raw_analysis": analysis_result,
#                 "note": "Analysis not in JSON format"
#             }
        
#         # Store in memory
#         memory_id = f"doc_{uuid4().hex[:8]}"
#         agentcore_memory[memory_id] = {
#             "doc_id": memory_id,
#             "s3_bucket": bucket,
#             "s3_key": filename,
#             "timestamp": time.time(),
#             "analysis": analysis_json
#         }
#         logger.info(f"Stored analysis in memory as {memory_id}")
        
#         result = {
#             "status": "success",
#             "filename": filename,
#             "bucket": bucket,
#             "s3_uri": s3_uri,
#             "memory_id": memory_id,
#             "analysis": analysis_json
#         }
        
#         return json.dumps(result, indent=2)
        
#     except Exception as e:
#         logger.exception(f"✗ Error processing {filename}")
#         error_result = {
#             "status": "error",
#             "message": f"Error processing file: {str(e)}",
#             "error_type": type(e).__name__,
#             "s3_uri": s3_uri
#         }
#         return json.dumps(error_result, indent=2)


@tool
def read_hld_agent(payload):
    """
    Reads and summarizes High-Level Design (HLD) documents from S3 bucket 'innovathon-poc-docs-anz'.
    
    This tool processes HLD documents (PDF, DOCX) and extracts:
    - Key architecture components
    - Design patterns
    - Technology stack
    - Security considerations
    - Scalability and reliability features
    
    Args:
        payload: Structured payload with 'filename' key
    
    Returns:
        JSON string with extracted HLD information
    
    Example payload:
        {
            "filename": "hld_document.pdf"
        }
    """
    logger.info(f"read_hld_agent called with payload: {payload}")
    
    # Default S3 bucket
    bucket = "innovathon-poc-docs-anz"
    
    filename = payload.get("filename")
    if not filename:
        return json.dumps({
            "status": "error",
            "message": "Filename not provided in payload."
        })
    
    # Construct S3 URI
    s3_uri = f"s3://{bucket}/{filename}"
    logger.info(f"Reading HLD document from: {s3_uri}")
    
    try:
        # Create an agent with document reading tools to analyze the HLD document
        from strands_tools import document_reader as document_reader_tool
        
        analysis_prompt = f"""Analyze this High-Level Design (HLD) document comprehensively. Extract:
1. Key architecture components
2. Design patterns used
3. Technology stack
4. Security considerations
5. Scalability and reliability features
Provide the analysis in JSON format with keys:
- components
- design_patterns
- technologies
- security
- scalability
- reliability"""
        # Create a simple agent to use document_reader tool
        logger.info("Creating analysis agent with document_reader tool...")
        analysis_agent = Agent(
            model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
            tools=[document_reader_tool,image_reader, use_aws],
            system_prompt="You are an HLD document analyzer. Use the document_reader tool to analyze documents from S3."
        )
        # Call the agent with the analysis request
        logger.info(f"Calling agent to analyze {s3_uri}...")
        agent_query = f"Use the document_reader tool to analyze the document at {s3_uri}. {analysis_prompt}"
        response = analysis_agent(agent_query)
        # Extract the analysis result
        analysis_result = response.message['content'][0]['text']
        logger.info(f"✓ Analysis completed, length: {len(analysis_result)}")
        # Parse the result
        try:
            analysis_json = json.loads(analysis_result)
        except json.JSONDecodeError:
            # If not valid JSON, wrap it
            analysis_json = {
                "raw_analysis": analysis_result,
                "note": "Analysis not in JSON format"
            }
        # Store in memory
        memory_id = f"hld_{uuid4().hex[:8]}"
        agentcore_memory[memory_id] = {
            "doc_id": memory_id,
            "s3_bucket": bucket,
            "s3_key": filename,
            "timestamp": time.time(),
            "analysis": analysis_json
        }
        logger.info(f"Stored analysis in memory as {memory_id}")
        result = {
            "status": "success",
            "filename": filename,
            "bucket": bucket,
            "s3_uri": s3_uri,
            "memory_id": memory_id,
            "analysis": analysis_json
        }
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.exception(f"✗ Error processing {filename}")
        error_result = {
            "status": "error",
            "message": f"Error processing file: {str(e)}",
            "error_type": type(e).__name__,
            "s3_uri": s3_uri
        }
        return json.dumps(error_result, indent=2)




@tool
def arch_diag_assistant(payload):
    """
    A Senior AWS Solutions Architect specializing in architecture diagrams.
    Creates professional, well-structured AWS architecture diagrams that follow best practices.
    """
    # Connect to an MCP server using stdio transport
    stdio_mcp_client = MCPClient(
        lambda: stdio_client(
            StdioServerParameters(
                command="uvx", args=["awslabs.aws-diagram-mcp-server@latest"]
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
            model="us.amazon.nova-pro-v1:0",
            tools=tools+[generate_image, image_reader, use_aws],
            system_prompt="""You are a Senior AWS Solutions Architect specializing in architecture diagrams.
            Your role is to create professional, well-structured AWS architecture diagrams that follow best practices.

            When designing architectures:
            - Use the AWS diagram tools to create clear, professional architecture diagrams
            - Follow AWS Well-Architected Framework principles (security, reliability, performance, cost optimization, operational excellence)
            - Include appropriate AWS services for high availability, scalability, and fault tolerance
            - Organize components into logical layers (presentation, application, data, etc.)
            - Show VPC boundaries, availability zones, and security groups where relevant
            - Include proper networking components (load balancers, NAT gateways, VPC endpoints)
            - Add monitoring and logging services (CloudWatch, CloudTrail)
            - Consider security best practices (IAM, encryption, least privilege)
            - Use industry-standard naming conventions and clear labels
            - Provide brief explanations for key architectural decisions

            Generate production-ready, enterprise-grade architecture diagrams that demonstrate deep AWS expertise.
            """)
        print("Agent initialized successfully!")
        # Invoke the agent with the provided payload
        response = agent(payload)
        return response.message['content'][0]['text']   

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


migration_system_prompt = """You are an AWS Migration Specialist with diagram analysis capabilities.

🚨 TOOL USAGE PROTOCOL 🚨
When user mentions a file (appa.jpeg, diagram.png, etc):
1. MUST call: input_agent("filename")
2. If tool returns error → MUST show user the EXACT error JSON
3. If tool succeeds → Parse JSON and recommend services

CRITICAL: You MUST show tool errors to the user. Do NOT hide them with apologies.

EXAMPLE 1 - Tool Error (CORRECT):
User: "Recommend services for appa.jpeg"
You: [Call input_agent("appa.jpeg")]
Tool returns: {"status": "error", "message": "Bedrock API error: AccessDeniedException"}
You: "I called input_agent to analyze appa.jpeg but received an error:
```json
{
  \"status\": \"error\",
  \"message\": \"Bedrock API error: AccessDeniedException\"
}
```
This indicates a permissions issue with the Bedrock service. Please check IAM permissions."

EXAMPLE 2 - Tool Success (CORRECT):
User: "Recommend services for appa.jpeg"
You: [Call input_agent("appa.jpeg")]
Tool returns: {"status": "success", "analysis": {"components": ["web server", "database"]}}
You: "I analyzed appa.jpeg and found: web servers and databases. I recommend:
1. Amazon EC2 or ECS for web servers
2. Amazon RDS for databases"

EXAMPLE 3 - WRONG (Do NOT do this):
User: "Recommend services for appa.jpeg"
You: "I apologize for the technical error..." ❌ WRONG! You must show the actual error!

YOUR TOOLS:
- input_agent(query: str) → Analyzes S3 diagrams from 'innovathon-poc-docs-anz'
- cost_assistant(payload: str) → AWS pricing
- aws_docs_assistant(payload: str) → AWS docs
- arch_diag_assistant(payload: str) → Creates diagrams

RULES:
1. File mentioned → Call input_agent()
2. Tool returns error → Show EXACT error JSON to user
3. Tool returns success → Parse and recommend
4. NEVER say "technical error" without showing the actual error
"""

migration_agent = Agent(
    model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    system_prompt=migration_system_prompt,
    hooks=[session_memory_provider],  # Pass hook provider directly as a list
    tools=[
        read_hld_agent,
        cost_assistant,
        aws_docs_assistant,
        arch_diag_assistant,
        generate_image,
        image_reader,
        use_aws],
)

@app.entrypoint
def migration_assistant(payload):
    """
    An AWS Migration Specialist that helps users plan and execute migrations from on-premises to AWS cloud.
    """
    # Invoke the migration agent with the provided payload
    user_input = payload.get("input") or payload.get("prompt")
    user_id = payload.get("user_id", "unknown")
    context = payload.get("context", {})
    
    # Create or retrieve session ID
    session_id = context.get("session_id") or f"session_{user_id}_{int(time.time())}"
    session_memory_provider.session_id = session_id
    
    print(f"User ID: {user_id}")
    print(f"Session ID: {session_id}")
    print(f"Input: {user_input}")
    
    # Check if user mentioned a file and log a reminder
    import re
    file_pattern = r'\w+\.(jpeg|jpg|png|pdf|gif)'
    if re.search(file_pattern, user_input, re.IGNORECASE):
        detected_files = re.findall(file_pattern, user_input, re.IGNORECASE)
        print(f"⚠️ FILE DETECTED: {detected_files} - Agent MUST call input_agent tool!")
        print(f"⚠️ Reminder: The agent should call input_agent() for these files!")
    
    # Retrieve conversation history from memory
    try:
        conversation_history = memory_client.get_memories(
            session_id=session_id,
            memory_type="short_term",
            limit=10  # Last 10 messages
        )
        
        if conversation_history:
            print(f"📚 Retrieved {len(conversation_history)} previous messages from session")
            # Add context to the agent about previous conversation
            history_context = "\n\nPrevious conversation context:\n"
            for mem in conversation_history[-5:]:  # Last 5 for context
                content = mem.get('content', {})
                history_context += f"{content.get('role', 'user')}: {content.get('content', '')[:100]}...\n"
            
            # Prepend history to user input
            user_input = history_context + "\n\nCurrent query: " + user_input
    except Exception as e:
        print(f"⚠️ Could not retrieve session history: {e}")
    
    # Process the query
    response = migration_agent(user_input)
    
    # Return structured response
    return response.message['content'][0]['text']

if __name__ == "__main__":
    app.run()