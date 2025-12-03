# Architecture Diagram Generation Guide

## Overview

The migration agent now includes advanced architecture diagram generation capabilities using:
- **AWS Diagram MCP Server**: Creates professional AWS architecture diagrams
- **Amazon Titan Image Generator v1**: Generates visual representations of architectures

## Features

### `arch_diag_assistant` Tool

This tool creates PNG architecture diagrams with the following capabilities:

1. **Professional AWS Diagrams**
   - Uses AWS Diagram MCP server for accurate AWS iconography
   - Follows AWS Well-Architected Framework principles
   - Includes VPC boundaries, availability zones, security groups
   - Shows networking components (ALB, NAT Gateway, IGW, etc.)
   - Adds monitoring and logging services

2. **Dual Image Generation**
   - **MCP Diagrams**: Technical, accurate AWS architecture diagrams
   - **Titan Diagrams**: AI-generated visual representations (optional)

3. **Output Management**
   - Diagrams saved to `generated-diagrams/` directory
   - PNG format with unique timestamps
   - File paths returned in response

## Usage Examples

### Example 1: Simple Architecture
```python
payload = {
    "input": "Generate a simple S3 and CloudFront architecture diagram as PNG",
    "user_id": "user123",
    "context": {}
}
response = migration_assistant(payload)
```

### Example 2: 3-Tier Web Application
```python
payload = {
    "input": "Create an AWS architecture diagram for a 3-tier web application with CloudFront, ALB, EC2 Auto Scaling, and RDS. Include VPC, public and private subnets, NAT Gateway, and security groups. Generate as PNG.",
    "user_id": "user123",
    "context": {}
}
response = migration_assistant(payload)
```

### Example 3: Microservices Architecture
```python
payload = {
    "input": "Design a microservices architecture diagram with ECS Fargate, API Gateway, Lambda, DynamoDB, and ElastiCache. Show inter-service communication and monitoring setup.",
    "user_id": "user123",
    "context": {}
}
response = migration_assistant(payload)
```

## Testing

Run the test script to verify diagram generation:

```bash
cd /Users/vasan/2\ Areas/Repo/innovathon/migration_agent
python test_local.py
```

The test script includes three test cases:
1. Simple migration query (no diagram)
2. Full 3-tier architecture diagram
3. Simple S3 + CloudFront diagram

## Configuration

### Model Configuration
- **Primary Model**: Claude 3.7 Sonnet for architecture planning
- **Image Model**: Amazon Titan Image Generator v1
  - Quality: Premium
  - Resolution: 1024x1024
  - CFG Scale: 8.0

### Output Directory
Diagrams are saved to: `migration_agent/generated-diagrams/`

### File Naming Convention
- MCP Diagrams: `diagram_<uuid>_<timestamp>.png`
- Titan Diagrams: `titan_diagram_<uuid>_<timestamp>.png`

## Best Practices

1. **Be Specific**: Provide clear requirements for the architecture
2. **Include Keywords**: Use "diagram", "PNG", "architecture" in prompts
3. **Specify Components**: List specific AWS services needed
4. **Mention Structure**: Reference VPCs, subnets, AZs when relevant

## Troubleshooting

### MCP Server Issues
If diagram generation fails:
1. Ensure `uvx` is installed: `pip install uv`
2. Check MCP server availability: `uvx awslabs.aws-diagram-mcp-server@latest`

### Titan Image Generation Issues
If Titan generation fails:
- Check AWS credentials are configured
- Verify Bedrock model access in us-east-1
- Ensure IAM permissions for `bedrock:InvokeModel`

### No Diagrams Generated
- Verify the `generated-diagrams/` directory exists
- Check file permissions for writing
- Review agent logs for specific errors

## Output Format

The tool returns:
```
<Architecture description and recommendations>

📁 Saved diagram files:
  - generated-diagrams/diagram_abc123_1733356789.png
  - generated-diagrams/titan_diagram_def456_1733356792.png

🎨 Generated visual diagram using Amazon Titan Image Generator
```

## Integration with Migration Agent

The `arch_diag_assistant` is automatically available when using the migration agent:

```python
from migration_agent import migration_assistant

payload = {
    "input": "I need to migrate my on-prem application to AWS. Can you create an architecture diagram?",
    "user_id": "user123"
}

response = migration_assistant(payload)
# The agent will automatically use arch_diag_assistant when diagram generation is needed
```

## Notes

- Titan image generation is optional and runs only when "diagram" keyword is detected
- MCP diagrams are more technically accurate for AWS architectures
- Titan diagrams provide visual appeal but may be less technically precise
- Both diagram types are generated and saved when applicable
