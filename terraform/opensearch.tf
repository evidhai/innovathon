# OpenSearch Serverless for Bedrock Knowledge Base

# OpenSearch Serverless encryption policy
resource "aws_opensearchserverless_security_policy" "kb_encryption" {
  name = "${var.project_name}-kb-encryption-policy"
  type = "encryption"

  policy = jsonencode({
    Rules = [
      {
        Resource = [
          "collection/${var.project_name}-kb-collection"
        ]
        ResourceType = "collection"
      }
    ]
    AWSOwnedKey = true
  })
}

# OpenSearch Serverless network policy
resource "aws_opensearchserverless_security_policy" "kb_network" {
  name = "${var.project_name}-kb-network-policy"
  type = "network"

  policy = jsonencode([
    {
      Rules = [
        {
          Resource = [
            "collection/${var.project_name}-kb-collection"
          ]
          ResourceType = "collection"
        }
      ]
      AllowFromPublic = true
    }
  ])
}

# OpenSearch Serverless collection for Knowledge Base
resource "aws_opensearchserverless_collection" "kb_collection" {
  name = "${var.project_name}-kb-collection"
  type = "VECTORSEARCH"

  depends_on = [
    aws_opensearchserverless_security_policy.kb_encryption,
    aws_opensearchserverless_security_policy.kb_network
  ]

  tags = merge(var.tags, {
    Name        = "Migration Agent Knowledge Base Collection"
    Description = "Vector store for ANZ documentation"
  })
}

# Data access policy for OpenSearch Serverless
resource "aws_opensearchserverless_access_policy" "kb_data_policy" {
  name = "${var.project_name}-kb-data-policy"
  type = "data"

  policy = jsonencode([
    {
      Rules = [
        {
          Resource = [
            "collection/${var.project_name}-kb-collection"
          ]
          Permission = [
            "aoss:CreateCollectionItems",
            "aoss:DeleteCollectionItems",
            "aoss:UpdateCollectionItems",
            "aoss:DescribeCollectionItems"
          ]
          ResourceType = "collection"
        },
        {
          Resource = [
            "index/${var.project_name}-kb-collection/*"
          ]
          Permission = [
            "aoss:CreateIndex",
            "aoss:DeleteIndex",
            "aoss:UpdateIndex",
            "aoss:DescribeIndex",
            "aoss:ReadDocument",
            "aoss:WriteDocument"
          ]
          ResourceType = "index"
        }
      ]
      Principal = [
        aws_iam_role.bedrock_kb_role.arn
      ]
    }
  ])
}

# Outputs
output "opensearch_collection_endpoint" {
  value       = aws_opensearchserverless_collection.kb_collection.collection_endpoint
  description = "Endpoint of the OpenSearch Serverless collection"
}

output "opensearch_collection_arn" {
  value       = aws_opensearchserverless_collection.kb_collection.arn
  description = "ARN of the OpenSearch Serverless collection"
}

output "opensearch_collection_id" {
  value       = aws_opensearchserverless_collection.kb_collection.id
  description = "ID of the OpenSearch Serverless collection"
}
