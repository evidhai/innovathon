# CloudWatch Log Groups for AWS Migration Agent System

# Log group for Bedrock Agents
resource "aws_cloudwatch_log_group" "bedrock_agents" {
  name              = "/aws/bedrock/agents/${var.project_name}"
  retention_in_days = 30

  tags = merge(var.tags, {
    Name        = "Bedrock Agents Logs"
    Description = "Logs for all Bedrock agents in the migration system"
  })
}

# Log group for Design Analyzer Agent
resource "aws_cloudwatch_log_group" "design_analyzer_agent" {
  name              = "/aws/bedrock/agents/${var.project_name}/design-analyzer"
  retention_in_days = 30

  tags = merge(var.tags, {
    Name        = "Design Analyzer Agent Logs"
    Description = "Logs for Design Analyzer Agent"
  })
}

# Log group for Service Advisor Agent
resource "aws_cloudwatch_log_group" "service_advisor_agent" {
  name              = "/aws/bedrock/agents/${var.project_name}/service-advisor"
  retention_in_days = 30

  tags = merge(var.tags, {
    Name        = "Service Advisor Agent Logs"
    Description = "Logs for Service Advisor Agent"
  })
}

# Log group for Cost Analysis Agent
resource "aws_cloudwatch_log_group" "cost_analysis_agent" {
  name              = "/aws/bedrock/agents/${var.project_name}/cost-analysis"
  retention_in_days = 30

  tags = merge(var.tags, {
    Name        = "Cost Analysis Agent Logs"
    Description = "Logs for Cost Analysis Agent"
  })
}

# Log group for User Interaction Agent
resource "aws_cloudwatch_log_group" "user_interaction_agent" {
  name              = "/aws/bedrock/agents/${var.project_name}/user-interaction"
  retention_in_days = 30

  tags = merge(var.tags, {
    Name        = "User Interaction Agent Logs"
    Description = "Logs for User Interaction Agent"
  })
}

# Log group for Report Generator Agent
resource "aws_cloudwatch_log_group" "report_generator_agent" {
  name              = "/aws/bedrock/agents/${var.project_name}/report-generator"
  retention_in_days = 30

  tags = merge(var.tags, {
    Name        = "Report Generator Agent Logs"
    Description = "Logs for Report Generator Agent"
  })
}

# Log group for Strands Agent (main orchestrator)
resource "aws_cloudwatch_log_group" "strands_agent" {
  name              = "/aws/bedrock/agents/${var.project_name}/strands-orchestrator"
  retention_in_days = 30

  tags = merge(var.tags, {
    Name        = "Strands Agent Logs"
    Description = "Logs for main Strands orchestrator agent"
  })
}

# Log group for Knowledge Base
resource "aws_cloudwatch_log_group" "knowledge_base" {
  name              = "/aws/bedrock/knowledgebase/${var.project_name}"
  retention_in_days = 30

  tags = merge(var.tags, {
    Name        = "Knowledge Base Logs"
    Description = "Logs for Bedrock Knowledge Base operations"
  })
}

# Log group for Lambda functions (if used for action groups)
resource "aws_cloudwatch_log_group" "lambda_functions" {
  name              = "/aws/lambda/${var.project_name}"
  retention_in_days = 30

  tags = merge(var.tags, {
    Name        = "Lambda Functions Logs"
    Description = "Logs for Lambda functions used in agent action groups"
  })
}

# Log group for application errors
resource "aws_cloudwatch_log_group" "application_errors" {
  name              = "/aws/${var.project_name}/errors"
  retention_in_days = 90

  tags = merge(var.tags, {
    Name        = "Application Errors"
    Description = "Centralized error logs for the migration agent system"
  })
}

# Outputs
output "bedrock_agents_log_group_name" {
  value       = aws_cloudwatch_log_group.bedrock_agents.name
  description = "Name of the CloudWatch log group for Bedrock agents"
}

output "knowledge_base_log_group_name" {
  value       = aws_cloudwatch_log_group.knowledge_base.name
  description = "Name of the CloudWatch log group for Knowledge Base"
}

output "lambda_log_group_name" {
  value       = aws_cloudwatch_log_group.lambda_functions.name
  description = "Name of the CloudWatch log group for Lambda functions"
}
