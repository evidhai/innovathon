import threading
import time
import json
import sys
from datetime import timedelta
from mcp import StdioServerParameters, stdio_client
from mcp.client.streamable_http import streamablehttp_client
from mcp.server import FastMCP
from strands import Agent
from strands.tools.mcp import MCPClient

from bedrock_agentcore.runtime import BedrockAgentCoreApp
app = BedrockAgentCoreApp()

# Connect to an MCP server using stdio transport
stdio_mcp_client = MCPClient(
    lambda: stdio_client(
        StdioServerParameters(
            command="uvx", args=["awslabs.aws-pricing-mcp-server@latest"]
        )
    )
)

# Initialize agent as None
agent = None
mcp_context = None

# Create an agent with MCP tools
def initialize_agent():
    global agent, mcp_context
    print("Initializing agent with AWS pricing tools...")
    
    # Keep the context manager alive
    mcp_context = stdio_mcp_client.__enter__()
    
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
        - Provide one-liner summaries with specific cost figures when possible
        - Highlight hidden costs and cost-saving opportunities
        - Tailor advice for users transitioning from on-prem to cloud-native architectures
        - Be practical and actionable in your cost recommendations
        - Give it as summary in detailed tabulated format
        - Ask user for clarifications if region of service is not specified
        """)
    print("Agent initialized successfully!")

@app.entrypoint
def cost_analysis_agent(payload):
    """
    Invoke the agent with a structured payload.
    Expected format:
    {
        "input": "user query",
        "user_id": "optional user id",
        "context": {
            "timezone": "optional timezone",
            "language": "optional language"
        }
    }
    """
    global agent
    if agent is None:
        initialize_agent()
    
    # Extract input from payload
    user_input = payload.get("input") or payload.get("prompt")
    user_id = payload.get("user_id", "unknown")
    context = payload.get("context", {})
    
    print(f"User ID: {user_id}")
    print(f"Input: {user_input}")
    if context:
        print(f"Context: {context}")
    
    # Process the query
    response = agent(user_input)
    
    # Return structured response
    return response.message['content'][0]['text']

if __name__ == "__main__":
    try:
        # Check if running with command-line argument (for testing)
        if len(sys.argv) > 1:
            try:
                payload = json.loads(sys.argv[1])
                initialize_agent()
                result = cost_analysis_agent(payload)
                print(f"\nResponse:\n{result}")
            except json.JSONDecodeError:
                print("Error: Invalid JSON payload")
                sys.exit(1)
        else:
            # Interactive mode for direct testing
            initialize_agent()
            print("\n💰 AWS Cost Analysis Agent ready!\n")
            print("Type 'exit' to quit.\n")
            
            while True:
                user_input = input("\nYou > ")
                if user_input.lower() == "exit":
                    print("Goodbye! 👋")
                    break
                
                # Create payload from user input
                payload = {
                    "input": user_input,
                    "user_id": "interactive",
                    "context": {}
                }
                
                print("\nAgent is thinking...")
                try:
                    response = cost_analysis_agent(payload)
                    print(f"\nAgent > {response}")
                except Exception as e:
                    print(f"\nError: {e}")
    finally:
        # Clean up MCP context
        if mcp_context is not None:
            stdio_mcp_client.__exit__(None, None, None)
