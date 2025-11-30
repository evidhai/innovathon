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
            command="uvx", args=["awslabs.aws-pricing-mcp-server@latest"]
        )
    )
)

print("Initializing agent with AWS pricing tools...")

# Create an agent with MCP tools
with stdio_mcp_client:
    # Get the tools from the MCP server
    tools = stdio_mcp_client.list_tools_sync()
    
    print(f"Loaded {len(tools)} tools from AWS documentation server")
    
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
    
    print("\n📚 AWS Pricing Agent ready! Ask me about AWS services.\n")
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
