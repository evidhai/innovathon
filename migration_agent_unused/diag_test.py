from mcp import StdioServerParameters, stdio_client
from strands import Agent, tool
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient
from bedrock_agentcore.runtime import BedrockAgentCoreApp
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = BedrockAgentCoreApp()

@tool
def create_aws_diagram(payload):
    """
    Creates AWS architecture diagrams using the AWS Diagram MCP server.
    
    Args:
        payload: Description of the AWS architecture diagram to create
        
    Returns:
        Response with diagram details and file path
    """
    logger.info(f"create_aws_diagram called with payload: {payload}")
    
    try:
        # Configure the AWS Diagram MCP client
        aws_diagram_mcp = MCPClient(
            lambda: stdio_client(
                StdioServerParameters(
                    command="uvx",
                    args=["awslabs.aws-diagram-mcp-server@latest"],
                )
            )
        )
        
        # Bedrock model for the agent
        bedrock_model = BedrockModel(
            model_id="us.anthropic.claude-3-5-haiku-20241022-v1:0",
            temperature=0.2,
        )
        
        SYSTEM_PROMPT = """You are an AWS Solutions Architect.
        You can generate AWS diagrams using the aws-diagram MCP server.
        Always tell the user the full output file path for the diagram you create.
        Create professional, well-structured diagrams following AWS best practices.
        """
        
        logger.info("Initializing AWS diagram agent...")
        
        # Start MCP client, discover tools, and run the agent
        with aws_diagram_mcp:
            # Discover tools exposed by the MCP server
            diagram_tools = aws_diagram_mcp.list_tools_sync()
            logger.info(f"Loaded {len(diagram_tools)} diagram tools")
            
            agent = Agent(
                model=bedrock_model,
                tools=diagram_tools,
                system_prompt=SYSTEM_PROMPT,
            )
            
            logger.info("Agent initialized, generating diagram...")
            
            # Generate the diagram
            response = agent(payload)
            
            # Extract response text
            response_text = response.message['content'][0]['text']
            logger.info(f"✅ Diagram generation completed")
            
            return response_text
            
    except Exception as e:
        error_msg = f"Error creating diagram: {str(e)}"
        logger.error(error_msg)
        return f"I encountered an error while creating the architecture diagram: {str(e)}\n\nPlease provide more details about your architecture requirements."

# Main agent that uses the diagram tool
diagram_agent = Agent(
    model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    tools=[create_aws_diagram],
    system_prompt="""You are an AWS Solutions Architect assistant.
    When users request architecture diagrams, use the create_aws_diagram tool to generate them.
    Provide helpful guidance on AWS architecture best practices.
    """
)

@app.entrypoint
def diagram_assistant(payload):
    """
    An AWS Solutions Architect assistant that creates architecture diagrams.
    """
    user_input = payload.get("input") or payload.get("prompt")
    logger.info(f"Diagram assistant called with input: {user_input}")
    
    # Process the query
    response = diagram_agent(user_input)
    
    # Return structured response
    return response.message['content'][0]['text']

if __name__ == "__main__":
    app.run()

