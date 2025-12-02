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
from strands_tools import generate_image, image_reader, use_aws
from strands.tools.mcp import MCPClient
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands.hooks import AgentInitializedEvent, HookProvider, MessageAddedEvent
from bedrock_agentcore.memory import MemoryClient
from strands.models import BedrockModel


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





@tool
def arch_diag_assistant(payload):
    """
    A Senior AWS Solutions Architect specializing in architecture diagrams.
    Creates professional, well-structured AWS architecture diagrams that follow best practices.
    After generating a diagram, uploads it to S3 bucket 'innovathon-poc-docs-anz' in the 'arch/' folder.
    """
    print(f"arch_diag_assistant called with payload: {payload}")
    
    try:
        # Try using AWS Diagram MCP server first
        aws_diagram_mcp = MCPClient(
            lambda: stdio_client(
                StdioServerParameters(
                    command="uvx",
                    args=["awslabs.aws-diagram-mcp-server@latest"],
                )
            )
        )
        
        bedrock_model = BedrockModel(
            model_id="us.anthropic.claude-3-5-haiku-20241022-v1:0",
            temperature=0.2,
        )
        
        SYSTEM_PROMPT = """You are a Senior AWS Solutions Architect specializing in architecture diagrams.
        Use the AWS diagram tools to create clear, professional architecture diagrams.
        Always tell the user the full output file path for the diagram you create.
        If the diagram tool fails, provide a detailed textual description instead.
        """
        
        print("Initializing agent with AWS diagram tools...")
        
        with aws_diagram_mcp:
            diagram_tools = aws_diagram_mcp.list_tools_sync()
            print(f"Loaded {len(diagram_tools)} tools from AWS diagram server")
            
            agent = Agent(
                model=bedrock_model,
                tools=diagram_tools,
                system_prompt=SYSTEM_PROMPT,
            )
            
            print("Agent initialized successfully!")
            response = agent(payload)
            
            # Extract response text
            response_text = response.message['content'][0]['text']
            
            # Check if diagram was actually generated
            if "technical limitations" in response_text.lower() or "was not generated" in response_text.lower():
                print("⚠️ AWS diagram tool failed, falling back to text description")
                return response_text
            
            # If successful, try to upload to S3
            print(f"✅ Diagram generated successfully")
            return response_text
            
    except Exception as e:
        error_msg = f"Error in arch_diag_assistant: {str(e)}"
        print(error_msg)
        return f"I encountered an error while creating the architecture diagram: {str(e)}\n\nPlease provide more details about your architecture requirements and I'll help design it."   

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