import base64
import threading
import time
from datetime import timedelta
from pathlib import Path
from uuid import uuid4
from mcp import StdioServerParameters, stdio_client
from mcp.client.streamable_http import streamablehttp_client
from mcp.server import FastMCP
from strands import Agent, tool
from strands.tools.mcp import MCPClient
from bedrock_agentcore.runtime import BedrockAgentCoreApp
app = BedrockAgentCoreApp()


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
            tools=tools,
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
    tools=[
        cost_assistant,
        aws_docs_assistant,
        arch_diag_assistant,],
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
    print(f"User ID: {user_id}")
    print(f"Input: {user_input}")
    if context:
        print(f"Context: {context}")
    
        # Process the query
    response = migration_agent(user_input)
        
        # Return structured response
    return response.message['content'][0]['text']

if __name__ == "__main__":
    app.run()