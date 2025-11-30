import threading
import time
from datetime import timedelta
from mcp import StdioServerParameters, stdio_client
from mcp.client.streamable_http import streamablehttp_client
from mcp.server import FastMCP
from strands import Agent
from strands.tools.mcp import MCPClient

# Connect to an MCP server using stdio transport
stdio_mcp_client = MCPClient(
    lambda: stdio_client(
        StdioServerParameters(
            command="uvx", args=["awslabs.aws-documentation-mcp-server@latest"]
        )
    )
)

print("Initializing agent with AWS documentation tools...")

# Create an agent with MCP tools
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
        - Cite specific AWS services and features , keep it one liner
        - Provide clear, practical examples when possible ,
        - If you're unsure, use the search tool to find the answer
        - Keep it simple for beginners , relatable to users from onprem to cloud-native
        """)
    
    print("\n📚 AWS Documentation Agent ready! Ask me about AWS services.\n")
    print("Type 'exit' to quit.\n")
    
    # Interactive loop
    while True:
        user_input = input("\nYou > ")
        if user_input.lower() == "exit":
            print("Goodbye! 👋")
            break
        
        print("\nAgent is thinking...")
        response = agent(user_input)
        print(f"\nAgent > {response}")
