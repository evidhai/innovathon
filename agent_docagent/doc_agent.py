import threading
import time
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
            command="uvx", args=["awslabs.aws-documentation-mcp-server@latest"]
        )
    )
)

print("Initializing agent with AWS documentation tools...")

# Create an agent with MCP tools - keep context alive
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

    @app.entrypoint
    def aws_docs_agent(payload):
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
        app.run()
