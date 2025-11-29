# Consolidated Outputs for AWS Migration Agent Infrastructure

# S3 Bucket Outputs
output "s3_buckets" {
  description = "S3 bucket information"
  value = {
    documents = {
      name = aws_s3_bucket.documents.id
      arn  = aws_s3_bucket.documents.arn
    }
    reports = {
      name = aws_s3_bucket.reports.id
      arn  = aws_s3_bucket.reports.arn
    }
    anz_docs = {
      name = aws_s3_bucket.anz_docs.id
      arn  = aws_s3_bucket.anz_docs.arn
    }
  }
}

# OpenSearch Serverless Outputs
output "opensearch_serverless" {
  description = "OpenSearch Serverless collection information"
  value = {
    collection_id       = aws_opensearchserverless_collection.kb_collection.id
    collection_arn      = aws_opensearchserverless_collection.kb_collection.arn
    collection_endpoint = aws_opensearchserverless_collection.kb_collection.collection_endpoint
  }
}

# Knowledge Base Outputs
output "knowledge_base" {
  description = "Bedrock Knowledge Base information"
  value = {
    id             = aws_bedrockagent_knowledge_base.anz_migration_kb.id
    arn            = aws_bedrockagent_knowledge_base.anz_migration_kb.arn
    name           = aws_bedrockagent_knowledge_base.anz_migration_kb.name
    data_source_id = aws_bedrockagent_data_source.anz_docs.data_source_id
  }
}

# IAM Role Outputs
output "iam_roles" {
  description = "IAM role ARNs for Bedrock services"
  value = {
    knowledge_base_role = aws_iam_role.bedrock_kb_role.arn
    agent_role          = aws_iam_role.bedrock_agent_role.arn
  }
}

# CloudWatch Log Group Outputs
output "cloudwatch_log_groups" {
  description = "CloudWatch log group names"
  value = {
    bedrock_agents       = aws_cloudwatch_log_group.bedrock_agents.name
    design_analyzer      = aws_cloudwatch_log_group.design_analyzer_agent.name
    service_advisor      = aws_cloudwatch_log_group.service_advisor_agent.name
    cost_analysis        = aws_cloudwatch_log_group.cost_analysis_agent.name
    user_interaction     = aws_cloudwatch_log_group.user_interaction_agent.name
    report_generator     = aws_cloudwatch_log_group.report_generator_agent.name
    strands_orchestrator = aws_cloudwatch_log_group.strands_agent.name
    knowledge_base       = aws_cloudwatch_log_group.knowledge_base.name
    lambda_functions     = aws_cloudwatch_log_group.lambda_functions.name
    application_errors   = aws_cloudwatch_log_group.application_errors.name
  }
}

# Summary Output for Quick Reference
output "deployment_summary" {
  description = "Quick reference summary of deployed resources"
  value = {
    region              = var.aws_region
    project_name        = var.project_name
    environment         = var.environment
    documents_bucket    = aws_s3_bucket.documents.id
    reports_bucket      = aws_s3_bucket.reports.id
    anz_docs_bucket     = aws_s3_bucket.anz_docs.id
    knowledge_base_id   = aws_bedrockagent_knowledge_base.anz_migration_kb.id
    opensearch_endpoint = aws_opensearchserverless_collection.kb_collection.collection_endpoint
  }
}
