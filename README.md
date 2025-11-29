# AWS Migration Agent System

An agentic AI system that analyzes on-premises applications and generates AWS migration proposals using AWS Strands, Agentic Core, and Amazon Bedrock.

## Overview

This system uses a multi-agent architecture to:
- Analyze High-Level Design (HLD) and Low-Level Design (LLD) documents
- Recommend AWS services for each application component
- Perform cost analysis and optimization
- Generate comprehensive PDF migration reports
- Incorporate ANZ-specific architecture guidelines and standards

## Architecture

The system consists of:
- **AWS Strands Agent**: Main orchestrator deployed in AWS Agentic Core
- **Design Analyzer Agent**: Analyzes architecture documents
- **Service Advisor Agent**: Recommends AWS services
- **Cost Analysis Agent**: Estimates migration costs
- **User Interaction Agent**: Handles clarifications and queries
- **Report Generator Agent**: Creates PDF reports
- **Streamlit Chat Interface**: Local web-based conversational UI

## Prerequisites

- Python 3.11 or higher
- AWS Account with appropriate permissions
- AWS CLI configured with credentials
- Terraform 1.5+ (for infrastructure deployment)
- Graphviz installed on your system (for diagram generation)

### Install Graphviz

**macOS:**
```bash
brew install graphviz
```

**Ubuntu/Debian:**
```bash
sudo apt-get install graphviz
```

**Windows:**
Download from https://graphviz.org/download/

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd aws-migration-agent
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your AWS credentials and configuration:
- AWS credentials (or use AWS CLI profile)
- Strands Agent ID and Alias ID (after deploying infrastructure)
- S3 bucket names
- Bedrock Knowledge Base ID

### 5. Deploy AWS Infrastructure

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

This will create:
- S3 buckets for documents and reports
- Bedrock Knowledge Base with OpenSearch Serverless
- IAM roles and policies
- CloudWatch log groups

### 6. Deploy Bedrock Agents

```bash
python scripts/deploy_agents.py
```

This script will:
- Create all 5 specialized Bedrock agents
- Configure action groups and Lambda functions
- Set up the main Strands Agent with agent collaboration
- Link the Knowledge Base

### 7. Upload Sample Documents

```bash
python scripts/upload_sample_docs.py
```

This will generate and upload:
- Sample HLD/LLD documents
- ANZ-specific documentation to the Knowledge Base

### 8. Run the Streamlit Application

```bash
streamlit run streamlit/app.py
```

The chat interface will open in your browser at `http://localhost:8501`

## Project Structure

```
aws-migration-agent/
├── agents/                 # Bedrock agent action group implementations
│   ├── design_analyzer/
│   ├── service_advisor/
│   ├── cost_analyzer/
│   ├── user_interaction/
│   └── report_generator/
├── utils/                  # Utility functions and helpers
│   ├── document_parser.py
│   ├── cost_calculator.py
│   └── pdf_generator.py
├── terraform/              # Infrastructure as Code
│   ├── main.tf
│   ├── s3.tf
│   ├── bedrock.tf
│   └── iam.tf
├── streamlit/              # Chat interface
│   └── app.py
├── tests/                  # Test files
├── scripts/                # Deployment and utility scripts
├── sample_documents/       # Generated sample documents
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
└── README.md              # This file
```

## Usage

### Starting a Migration Analysis

1. Open the Streamlit chat interface
2. Start a conversation: "I want to analyze my application for AWS migration"
3. Provide document paths or S3 URIs when requested
4. Answer clarification questions from the agent
5. Review service recommendations and make selections
6. Receive cost analysis and final PDF report

### Example Conversation Flow

```
User: I want to migrate my e-commerce application to AWS
Agent: I'll help you with that. Please provide the HLD and LLD documents...
User: The documents are at s3://my-bucket/hld.pdf and s3://my-bucket/lld.pdf
Agent: [Analyzes documents] I've identified 3 tiers: web, application, and database...
Agent: For the web tier, I recommend: 1) Elastic Beanstalk, 2) ECS Fargate, 3) EC2...
User: I prefer Elastic Beanstalk
Agent: [Continues with other components and cost analysis]
Agent: Your migration report is ready: s3://reports-bucket/migration-report-123.pdf
```

## Configuration

### AWS Credentials

You can configure AWS credentials in multiple ways:
1. Environment variables in `.env`
2. AWS CLI profile: `aws configure`
3. IAM role (if running on EC2/ECS)

### Agent Configuration

Agent behavior can be customized by modifying:
- Agent instructions in `scripts/deploy_agents.py`
- Action group functions in `agents/` directory
- Knowledge Base content in S3

## Troubleshooting

### Common Issues

**Issue: "Agent not found" error**
- Ensure you've deployed the infrastructure and agents
- Check that STRANDS_AGENT_ID in .env matches the deployed agent

**Issue: "Access Denied" errors**
- Verify AWS credentials are correct
- Check IAM permissions for Bedrock, S3, and other services

**Issue: Graphviz errors**
- Ensure Graphviz is installed on your system
- Add Graphviz to your PATH

**Issue: Knowledge Base queries return no results**
- Verify documents are uploaded to S3
- Check that Knowledge Base ingestion job completed successfully

### Logs

- Agent execution logs: CloudWatch Logs
- Streamlit logs: Terminal output
- Terraform logs: `terraform.log`

## Development

### Running Tests

```bash
pytest tests/
```

### Adding New Agents

1. Create agent module in `agents/`
2. Implement action group functions
3. Update `scripts/deploy_agents.py`
4. Add agent to Strands Agent collaboration

## Security

- All data is encrypted at rest (S3, OpenSearch)
- TLS for data in transit
- IAM roles follow least privilege principle
- Credentials stored in environment variables (never in code)

## Cost Considerations

This system uses several AWS services that incur costs:
- Amazon Bedrock (per token)
- S3 storage
- OpenSearch Serverless
- CloudWatch Logs
- AWS Strands Agent invocations

Estimated monthly cost for demo usage: $50-100

## License

[Your License Here]

## Support

For issues and questions:
- Create an issue in the repository
- Contact: [Your Contact Info]
