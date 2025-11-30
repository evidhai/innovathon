import base64
import threading
import time
from datetime import timedelta
from pathlib import Path
from uuid import uuid4
from mcp import StdioServerParameters, stdio_client
from mcp.client.streamable_http import streamablehttp_client
from mcp.server import FastMCP
from strands import Agent
from strands.tools.mcp import MCPClient
from bedrock_agentcore.runtime import BedrockAgentCoreApp
app = BedrockAgentCoreApp()

DIAGRAM_OUTPUT_DIR = Path("generated_diagrams")
DIAGRAM_OUTPUT_DIR.mkdir(exist_ok=True)

# Connect to an MCP server using stdio transport
stdio_mcp_client = MCPClient(
    lambda: stdio_client(
        StdioServerParameters(
            command="uvx", args=["awslabs.aws-diagram-mcp-server@latest"]
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

        # Extract text and any image payloads returned by the MCP tools/LLM
        text_parts = []
        saved_images = []

        for part in response.message.get("content", []):
            if part.get("type") == "text" and "text" in part:
                text_parts.append(part["text"])
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
                except Exception as e:
                    text_parts.append(f"[Warning] Failed to decode image payload: {e}")

        # Fallback if no structured text was returned
        if not text_parts and isinstance(response.message, dict):
            fallback = response.message.get("content") or response.message
            text_parts.append(str(fallback))

        result = "\n\n".join(text_parts).strip()
        if saved_images:
            result = f"{result}\n\nSaved diagram images:\n" + "\n".join(saved_images)

        return result

    if __name__ == "__main__":
        app.run()
