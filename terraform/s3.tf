# S3 Buckets for AWS Migration Agent System

# Generate unique bucket names using account ID and region
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id
  region     = data.aws_region.current.name

  documents_bucket = var.documents_bucket_name != "" ? var.documents_bucket_name : "${var.project_name}-documents-${local.account_id}-${var.environment}"
  reports_bucket   = var.reports_bucket_name != "" ? var.reports_bucket_name : "${var.project_name}-reports-${local.account_id}-${var.environment}"
  anz_docs_bucket  = var.anz_docs_bucket_name != "" ? var.anz_docs_bucket_name : "${var.project_name}-anz-docs-${local.account_id}-${var.environment}"
}

# S3 Bucket for uploaded documents (HLD/LLD)
resource "aws_s3_bucket" "documents" {
  bucket = local.documents_bucket

  tags = merge(var.tags, {
    Name        = "Migration Agent Documents Bucket"
    Description = "Stores uploaded HLD and LLD documents for analysis"
  })
}

# Enable versioning for documents bucket
resource "aws_s3_bucket_versioning" "documents" {
  bucket = aws_s3_bucket.documents.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Enable server-side encryption for documents bucket
resource "aws_s3_bucket_server_side_encryption_configuration" "documents" {
  bucket = aws_s3_bucket.documents.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block public access for documents bucket
resource "aws_s3_bucket_public_access_block" "documents" {
  bucket = aws_s3_bucket.documents.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# S3 Bucket for generated reports
resource "aws_s3_bucket" "reports" {
  bucket = local.reports_bucket

  tags = merge(var.tags, {
    Name        = "Migration Agent Reports Bucket"
    Description = "Stores generated migration analysis reports"
  })
}

# Enable versioning for reports bucket
resource "aws_s3_bucket_versioning" "reports" {
  bucket = aws_s3_bucket.reports.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Enable server-side encryption for reports bucket
resource "aws_s3_bucket_server_side_encryption_configuration" "reports" {
  bucket = aws_s3_bucket.reports.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block public access for reports bucket
resource "aws_s3_bucket_public_access_block" "reports" {
  bucket = aws_s3_bucket.reports.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# S3 Bucket for ANZ-specific documentation (Knowledge Base data source)
resource "aws_s3_bucket" "anz_docs" {
  bucket = local.anz_docs_bucket

  tags = merge(var.tags, {
    Name        = "ANZ Documentation Bucket"
    Description = "Stores ANZ-specific architecture guidelines and policies"
  })
}

# Enable versioning for ANZ docs bucket
resource "aws_s3_bucket_versioning" "anz_docs" {
  bucket = aws_s3_bucket.anz_docs.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Enable server-side encryption for ANZ docs bucket
resource "aws_s3_bucket_server_side_encryption_configuration" "anz_docs" {
  bucket = aws_s3_bucket.anz_docs.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block public access for ANZ docs bucket
resource "aws_s3_bucket_public_access_block" "anz_docs" {
  bucket = aws_s3_bucket.anz_docs.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lifecycle policy for reports bucket (optional - keep reports for 90 days)
resource "aws_s3_bucket_lifecycle_configuration" "reports" {
  bucket = aws_s3_bucket.reports.id

  rule {
    id     = "expire-old-reports"
    status = "Enabled"

    expiration {
      days = 90
    }

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}

# Outputs
output "documents_bucket_name" {
  value       = aws_s3_bucket.documents.id
  description = "Name of the S3 bucket for documents"
}

output "documents_bucket_arn" {
  value       = aws_s3_bucket.documents.arn
  description = "ARN of the S3 bucket for documents"
}

output "reports_bucket_name" {
  value       = aws_s3_bucket.reports.id
  description = "Name of the S3 bucket for reports"
}

output "reports_bucket_arn" {
  value       = aws_s3_bucket.reports.arn
  description = "ARN of the S3 bucket for reports"
}

output "anz_docs_bucket_name" {
  value       = aws_s3_bucket.anz_docs.id
  description = "Name of the S3 bucket for ANZ documentation"
}

output "anz_docs_bucket_arn" {
  value       = aws_s3_bucket.anz_docs.arn
  description = "ARN of the S3 bucket for ANZ documentation"
}
