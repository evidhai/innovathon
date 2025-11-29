# IAM Roles and Policies for Bedrock Agents and Knowledge Base

# IAM Role for Bedrock Knowledge Base
resource "aws_iam_role" "bedrock_kb_role" {
  name = "${var.project_name}-kb-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "bedrock.amazonaws.com"
        }
        Action = "sts:AssumeRole"
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = data.aws_caller_identity.current.account_id
          }
          ArnLike = {
            "aws:SourceArn" = "arn:aws:bedrock:${var.aws_region}:${data.aws_caller_identity.current.account_id}:knowledge-base/*"
          }
        }
      }
    ]
  })

  tags = merge(var.tags, {
    Name        = "Bedrock Knowledge Base Role"
    Description = "IAM role for Bedrock Knowledge Base to access S3 and OpenSearch"
  })
}

# IAM Policy for Bedrock Knowledge Base - S3 Access
resource "aws_iam_policy" "bedrock_kb_s3_policy" {
  name        = "${var.project_name}-kb-s3-policy"
  description = "Policy for Bedrock Knowledge Base to access S3 buckets"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "S3ListBucket"
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.anz_docs.arn
        ]
      },
      {
        Sid    = "S3GetObject"
        Effect = "Allow"
        Action = [
          "s3:GetObject"
        ]
        Resource = [
          "${aws_s3_bucket.anz_docs.arn}/*"
        ]
      }
    ]
  })
}

# IAM Policy for Bedrock Knowledge Base - OpenSearch Access
resource "aws_iam_policy" "bedrock_kb_aoss_policy" {
  name        = "${var.project_name}-kb-aoss-policy"
  description = "Policy for Bedrock Knowledge Base to access OpenSearch Serverless"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "OpenSearchServerlessAPIAccess"
        Effect = "Allow"
        Action = [
          "aoss:APIAccessAll"
        ]
        Resource = [
          aws_opensearchserverless_collection.kb_collection.arn
        ]
      }
    ]
  })
}

# IAM Policy for Bedrock Knowledge Base - Bedrock Model Access
resource "aws_iam_policy" "bedrock_kb_model_policy" {
  name        = "${var.project_name}-kb-model-policy"
  description = "Policy for Bedrock Knowledge Base to invoke embedding models"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "BedrockInvokeModel"
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel"
        ]
        Resource = [
          var.embedding_model_arn
        ]
      }
    ]
  })
}

# Attach policies to Knowledge Base role
resource "aws_iam_role_policy_attachment" "kb_s3_attachment" {
  role       = aws_iam_role.bedrock_kb_role.name
  policy_arn = aws_iam_policy.bedrock_kb_s3_policy.arn
}

resource "aws_iam_role_policy_attachment" "kb_aoss_attachment" {
  role       = aws_iam_role.bedrock_kb_role.name
  policy_arn = aws_iam_policy.bedrock_kb_aoss_policy.arn
}

resource "aws_iam_role_policy_attachment" "kb_model_attachment" {
  role       = aws_iam_role.bedrock_kb_role.name
  policy_arn = aws_iam_policy.bedrock_kb_model_policy.arn
}

# IAM Role for Bedrock Agents
resource "aws_iam_role" "bedrock_agent_role" {
  name = "${var.project_name}-agent-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "bedrock.amazonaws.com"
        }
        Action = "sts:AssumeRole"
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = data.aws_caller_identity.current.account_id
          }
          ArnLike = {
            "aws:SourceArn" = "arn:aws:bedrock:${var.aws_region}:${data.aws_caller_identity.current.account_id}:agent/*"
          }
        }
      }
    ]
  })

  tags = merge(var.tags, {
    Name        = "Bedrock Agent Role"
    Description = "IAM role for Bedrock Agents to invoke models and access resources"
  })
}

# IAM Policy for Bedrock Agents - Model Invocation
resource "aws_iam_policy" "bedrock_agent_model_policy" {
  name        = "${var.project_name}-agent-model-policy"
  description = "Policy for Bedrock Agents to invoke foundation models"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "BedrockInvokeModel"
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
        ]
        Resource = [
          "arn:aws:bedrock:${var.aws_region}::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0",
          "arn:aws:bedrock:${var.aws_region}::foundation-model/anthropic.claude-3-5-sonnet-20240620-v1:0",
          "arn:aws:bedrock:${var.aws_region}::foundation-model/amazon.titan-embed-text-v2:0"
        ]
      }
    ]
  })
}

# IAM Policy for Bedrock Agents - S3 Access
resource "aws_iam_policy" "bedrock_agent_s3_policy" {
  name        = "${var.project_name}-agent-s3-policy"
  description = "Policy for Bedrock Agents to access S3 buckets"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "S3ReadDocuments"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.documents.arn,
          "${aws_s3_bucket.documents.arn}/*"
        ]
      },
      {
        Sid    = "S3WriteReports"
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:PutObjectAcl"
        ]
        Resource = [
          "${aws_s3_bucket.reports.arn}/*"
        ]
      }
    ]
  })
}

# IAM Policy for Bedrock Agents - Knowledge Base Access
resource "aws_iam_policy" "bedrock_agent_kb_policy" {
  name        = "${var.project_name}-agent-kb-policy"
  description = "Policy for Bedrock Agents to retrieve from Knowledge Base"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "BedrockKnowledgeBaseRetrieve"
        Effect = "Allow"
        Action = [
          "bedrock:Retrieve",
          "bedrock:RetrieveAndGenerate"
        ]
        Resource = [
          "arn:aws:bedrock:${var.aws_region}:${data.aws_caller_identity.current.account_id}:knowledge-base/*"
        ]
      }
    ]
  })
}

# IAM Policy for Bedrock Agents - Textract Access
resource "aws_iam_policy" "bedrock_agent_textract_policy" {
  name        = "${var.project_name}-agent-textract-policy"
  description = "Policy for Bedrock Agents to use Textract for document analysis"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "TextractAnalyze"
        Effect = "Allow"
        Action = [
          "textract:AnalyzeDocument",
          "textract:DetectDocumentText",
          "textract:StartDocumentAnalysis",
          "textract:GetDocumentAnalysis"
        ]
        Resource = "*"
      }
    ]
  })
}

# IAM Policy for Bedrock Agents - Pricing API Access
resource "aws_iam_policy" "bedrock_agent_pricing_policy" {
  name        = "${var.project_name}-agent-pricing-policy"
  description = "Policy for Bedrock Agents to access AWS Pricing API"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "PricingAPIAccess"
        Effect = "Allow"
        Action = [
          "pricing:GetProducts",
          "pricing:DescribeServices",
          "pricing:GetAttributeValues"
        ]
        Resource = "*"
      }
    ]
  })
}

# Attach policies to Bedrock Agent role
resource "aws_iam_role_policy_attachment" "agent_model_attachment" {
  role       = aws_iam_role.bedrock_agent_role.name
  policy_arn = aws_iam_policy.bedrock_agent_model_policy.arn
}

resource "aws_iam_role_policy_attachment" "agent_s3_attachment" {
  role       = aws_iam_role.bedrock_agent_role.name
  policy_arn = aws_iam_policy.bedrock_agent_s3_policy.arn
}

resource "aws_iam_role_policy_attachment" "agent_kb_attachment" {
  role       = aws_iam_role.bedrock_agent_role.name
  policy_arn = aws_iam_policy.bedrock_agent_kb_policy.arn
}

resource "aws_iam_role_policy_attachment" "agent_textract_attachment" {
  role       = aws_iam_role.bedrock_agent_role.name
  policy_arn = aws_iam_policy.bedrock_agent_textract_policy.arn
}

resource "aws_iam_role_policy_attachment" "agent_pricing_attachment" {
  role       = aws_iam_role.bedrock_agent_role.name
  policy_arn = aws_iam_policy.bedrock_agent_pricing_policy.arn
}

# Outputs
output "bedrock_kb_role_arn" {
  value       = aws_iam_role.bedrock_kb_role.arn
  description = "ARN of the Bedrock Knowledge Base IAM role"
}

output "bedrock_agent_role_arn" {
  value       = aws_iam_role.bedrock_agent_role.arn
  description = "ARN of the Bedrock Agent IAM role"
}
