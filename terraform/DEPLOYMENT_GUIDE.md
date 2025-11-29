# AWS Migration Agent - Deployment Guide

## Quick Start

### 1. Configure Variables

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your preferred values (or use defaults).

### 2. Deploy Infrastructure

```bash
# Initialize Terraform
terraform init

# Review the plan
terraform plan

# Deploy resources
terraform apply
```

### 3. Verify Deployment

```bash
# View all outputs
terraform output

# View specific output
terraform output deployment_summary
```

## What Gets Created

### Storage Layer
- **3 S3 Buckets**:
  - Documents bucket (for HLD/LLD uploads)
  - Reports bucket (for generated PDFs)
  - ANZ docs bucket (for Knowledge Base)
- All with versioning, encryption, and public access blocked

### Vector Store
- **OpenSearch Serverless Collection**:
  - Type: VECTORSEARCH
  - Encryption and network policies configured
  - Data access policy for Bedrock KB

### Knowledge Base
- **Bedrock Knowledge Base**:
  - Connected to OpenSearch Serverless
  - Uses Amazon Titan Embed Text v2
  - Data source pointing to ANZ docs S3 bucket
  - Fixed-size chunking (300 tokens, 20% overlap)

### IAM Security
- **2 IAM Roles**:
  - Knowledge Base role (S3, OpenSearch, Bedrock access)
  - Agent role (models, S3, KB, Textract, Pricing API)
- **7 IAM Policies** with least-privilege permissions

### Monitoring
- **10 CloudWatch Log Groups**:
  - One for each agent type
  - Knowledge Base operations
  - Lambda functions
  - Application errors
- Retention: 30 days (90 days for errors)

## Post-Deployment Steps

### 1. Upload ANZ Documentation

```bash
# Get the bucket name
ANZ_BUCKET=$(terraform output -raw s3_buckets | jq -r '.anz_docs.name')

# Upload your ANZ documentation
aws s3 cp ./anz-docs/ s3://$ANZ_BUCKET/ --recursive
```

### 2. Trigger Knowledge Base Ingestion

```bash
# Get the Knowledge Base ID and Data Source ID
KB_ID=$(terraform output -raw knowledge_base | jq -r '.id')
DS_ID=$(terraform output -raw knowledge_base | jq -r '.data_source_id')

# Start ingestion job
aws bedrock-agent start-ingestion-job \
  --knowledge-base-id $KB_ID \
  --data-source-id $DS_ID
```

### 3. Monitor Ingestion

```bash
# Check ingestion job status
aws bedrock-agent list-ingestion-jobs \
  --knowledge-base-id $KB_ID \
  --data-source-id $DS_ID
```

## Resource Naming Convention

Resources follow this pattern:
- S3 Buckets: `{project_name}-{type}-{account_id}-{environment}`
- IAM Roles: `{project_name}-{type}-role`
- Log Groups: `/aws/bedrock/agents/{project_name}/{agent_type}`

## Cost Considerations

Estimated monthly costs (us-east-1, light usage):
- S3 Storage: ~$5-10 (depends on document volume)
- OpenSearch Serverless: ~$700 (OCU-based pricing)
- Bedrock Knowledge Base: ~$0.10 per 1000 queries
- CloudWatch Logs: ~$5 (depends on log volume)

**Total: ~$710-720/month** (primarily OpenSearch Serverless)

### Cost Optimization Tips
1. Use OpenSearch Serverless only when needed
2. Set appropriate log retention periods
3. Enable S3 lifecycle policies for old documents
4. Monitor usage with AWS Cost Explorer

## Troubleshooting

### Issue: Terraform state bucket doesn't exist

Update `provider.tf` to use your own state bucket or remove the backend configuration:

```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  # Remove or update backend configuration
}
```

### Issue: OpenSearch collection creation timeout

OpenSearch Serverless collections can take 5-10 minutes to create. If it times out:
1. Check AWS Console to see if collection is being created
2. Wait for completion and run `terraform apply` again

### Issue: Knowledge Base creation fails

Ensure:
1. IAM role has correct permissions
2. OpenSearch collection is fully created
3. S3 bucket exists and is accessible
4. Embedding model is available in your region

### Issue: Permission denied errors

Your AWS credentials need permissions to create:
- S3 buckets
- OpenSearch Serverless resources
- Bedrock Knowledge Bases
- IAM roles and policies
- CloudWatch log groups

## Cleanup

To destroy all resources:

```bash
terraform destroy
```

**Warning**: This will:
- Delete all S3 buckets and their contents
- Remove the OpenSearch collection and all vectors
- Delete the Knowledge Base
- Remove all IAM roles and policies
- Delete all CloudWatch logs

Ensure you have backups before destroying!

## Next Steps

After successful deployment:
1. ✅ Infrastructure is ready
2. 📄 Upload sample documents (Task 3)
3. 📚 Upload ANZ documentation (Task 4)
4. 🤖 Create Bedrock agents (Tasks 5-10)
5. 🔗 Set up Strands agent (Task 11)
6. 💻 Deploy Streamlit interface (Task 12)

## Support

For issues or questions:
1. Check CloudWatch logs for errors
2. Review Terraform state: `terraform show`
3. Validate configuration: `terraform validate`
4. Check AWS service quotas and limits
