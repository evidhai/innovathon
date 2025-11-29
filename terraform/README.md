# AWS Migration Agent - Terraform Infrastructure

This directory contains Terraform configurations for deploying the AWS Migration Agent infrastructure.

## Overview

The infrastructure includes:
- **S3 Buckets**: For documents, reports, and ANZ documentation
- **OpenSearch Serverless**: Vector store for the Knowledge Base
- **Bedrock Knowledge Base**: ANZ-specific guidelines and policies
- **IAM Roles & Policies**: For Bedrock agents and Knowledge Base
- **CloudWatch Log Groups**: For monitoring and debugging

## Prerequisites

1. **AWS CLI** configured with appropriate credentials
2. **Terraform** v1.0+ installed
3. **AWS Account** with permissions to create:
   - S3 buckets
   - OpenSearch Serverless collections
   - Bedrock Knowledge Bases
   - IAM roles and policies
   - CloudWatch log groups

## Configuration

1. Copy the example variables file:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```

2. Edit `terraform.tfvars` with your values:
   ```hcl
   project_name = "aws-migration-agent"
   environment  = "dev"
   aws_region   = "us-east-1"
   ```

3. (Optional) Customize S3 bucket names or use auto-generated names

## Deployment

### Initialize Terraform

```bash
terraform init
```

### Plan the Deployment

```bash
terraform plan
```

### Apply the Configuration

```bash
terraform apply
```

Review the plan and type `yes` to confirm.

### View Outputs

```bash
terraform output
```

## Resource Details

### S3 Buckets

- **Documents Bucket**: Stores uploaded HLD/LLD documents
- **Reports Bucket**: Stores generated migration reports (90-day lifecycle)
- **ANZ Docs Bucket**: Stores ANZ-specific documentation for Knowledge Base

All buckets have:
- Versioning enabled
- Server-side encryption (AES256)
- Public access blocked

### OpenSearch Serverless

- **Collection Type**: VECTORSEARCH
- **Encryption**: AWS-owned key
- **Network Access**: Public (can be restricted in production)

### Bedrock Knowledge Base

- **Embedding Model**: Amazon Titan Embed Text v2
- **Vector Store**: OpenSearch Serverless
- **Data Source**: S3 bucket with ANZ documentation
- **Chunking Strategy**: Fixed size (300 tokens, 20% overlap)

### IAM Roles

1. **Knowledge Base Role**: Allows Bedrock KB to:
   - Read from ANZ docs S3 bucket
   - Access OpenSearch Serverless collection
   - Invoke embedding models

2. **Agent Role**: Allows Bedrock Agents to:
   - Invoke foundation models (Claude 3.5 Sonnet)
   - Read documents from S3
   - Write reports to S3
   - Retrieve from Knowledge Base
   - Use Textract for document analysis
   - Access AWS Pricing API

### CloudWatch Log Groups

Separate log groups for:
- Each specialized agent (Design Analyzer, Service Advisor, etc.)
- Strands orchestrator agent
- Knowledge Base operations
- Lambda functions
- Application errors (90-day retention)

## Outputs

After deployment, Terraform provides:
- S3 bucket names and ARNs
- OpenSearch collection endpoint
- Knowledge Base ID and ARN
- IAM role ARNs
- CloudWatch log group names

## Cleanup

To destroy all resources:

```bash
terraform destroy
```

**Warning**: This will delete all S3 buckets and their contents. Ensure you have backups if needed.

## File Structure

```
terraform/
├── provider.tf              # AWS provider configuration
├── variables.tf             # Input variables
├── terraform.tfvars.example # Example variable values
├── s3.tf                    # S3 bucket resources
├── opensearch.tf            # OpenSearch Serverless resources
├── knowledge_base.tf        # Bedrock Knowledge Base resources
├── bedrock_iam.tf           # IAM roles and policies
├── cloudwatch.tf            # CloudWatch log groups
├── outputs.tf               # Output values
└── README.md                # This file
```

## Notes

- The S3 backend configuration in `provider.tf` uses bucket `innovathon-poc-state-anz`. Update this if needed.
- Bucket names are auto-generated with account ID to ensure uniqueness
- All resources are tagged with project, environment, and management information
- Log retention is set to 30 days (90 days for errors) to manage costs

## Troubleshooting

### OpenSearch Serverless Collection Creation Fails

Ensure the encryption and network policies are created before the collection. The `depends_on` blocks handle this automatically.

### Knowledge Base Creation Fails

Verify that:
1. IAM role has correct trust policy for Bedrock
2. OpenSearch collection is fully created
3. S3 bucket exists and is accessible

### Permission Errors

Ensure your AWS credentials have sufficient permissions to create all resources. Consider using an admin role for initial setup.

## Next Steps

After infrastructure deployment:
1. Upload ANZ documentation to the ANZ docs S3 bucket
2. Trigger Knowledge Base ingestion
3. Create and configure Bedrock agents
4. Deploy the Streamlit application
