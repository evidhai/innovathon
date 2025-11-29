# Variables for AWS Migration Agent Infrastructure

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "aws-migration-agent"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "documents_bucket_name" {
  description = "S3 bucket name for storing uploaded documents (HLD/LLD)"
  type        = string
  default     = ""
}

variable "reports_bucket_name" {
  description = "S3 bucket name for storing generated reports"
  type        = string
  default     = ""
}

variable "anz_docs_bucket_name" {
  description = "S3 bucket name for ANZ-specific documentation"
  type        = string
  default     = ""
}

variable "knowledge_base_name" {
  description = "Name for the Bedrock Knowledge Base"
  type        = string
  default     = "anz-migration-kb"
}

variable "embedding_model_arn" {
  description = "ARN of the embedding model for Knowledge Base"
  type        = string
  default     = "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0"
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Project     = "AWS Migration Agent"
    ManagedBy   = "Terraform"
    Environment = "dev"
  }
}
