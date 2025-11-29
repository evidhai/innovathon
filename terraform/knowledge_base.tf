# Bedrock Knowledge Base Configuration

# Bedrock Knowledge Base
resource "aws_bedrockagent_knowledge_base" "anz_migration_kb" {
  name     = var.knowledge_base_name
  role_arn = aws_iam_role.bedrock_kb_role.arn

  description = "Knowledge Base containing ANZ-specific architecture guidelines, VPC configurations, and cost optimization policies"

  knowledge_base_configuration {
    type = "VECTOR"

    vector_knowledge_base_configuration {
      embedding_model_arn = var.embedding_model_arn
    }
  }

  storage_configuration {
    type = "OPENSEARCH_SERVERLESS"

    opensearch_serverless_configuration {
      collection_arn    = aws_opensearchserverless_collection.kb_collection.arn
      vector_index_name = "${var.project_name}-vector-index"

      field_mapping {
        vector_field   = "vector"
        text_field     = "text"
        metadata_field = "metadata"
      }
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.kb_s3_attachment,
    aws_iam_role_policy_attachment.kb_aoss_attachment,
    aws_iam_role_policy_attachment.kb_model_attachment,
    aws_opensearchserverless_access_policy.kb_data_policy
  ]

  tags = merge(var.tags, {
    Name        = "ANZ Migration Knowledge Base"
    Description = "Vector store for ANZ documentation and guidelines"
  })
}

# Bedrock Knowledge Base Data Source
resource "aws_bedrockagent_data_source" "anz_docs" {
  knowledge_base_id = aws_bedrockagent_knowledge_base.anz_migration_kb.id
  name              = "anz-documentation"
  description       = "ANZ-specific architecture guidelines and policies"

  data_source_configuration {
    type = "S3"

    s3_configuration {
      bucket_arn = aws_s3_bucket.anz_docs.arn
    }
  }

  vector_ingestion_configuration {
    chunking_configuration {
      chunking_strategy = "FIXED_SIZE"

      fixed_size_chunking_configuration {
        max_tokens         = 300
        overlap_percentage = 20
      }
    }
  }

  depends_on = [
    aws_bedrockagent_knowledge_base.anz_migration_kb
  ]
}

# Outputs
output "knowledge_base_id" {
  value       = aws_bedrockagent_knowledge_base.anz_migration_kb.id
  description = "ID of the Bedrock Knowledge Base"
}

output "knowledge_base_arn" {
  value       = aws_bedrockagent_knowledge_base.anz_migration_kb.arn
  description = "ARN of the Bedrock Knowledge Base"
}

output "data_source_id" {
  value       = aws_bedrockagent_data_source.anz_docs.data_source_id
  description = "ID of the Knowledge Base data source"
}
