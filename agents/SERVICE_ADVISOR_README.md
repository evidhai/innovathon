# Service Advisor Agent

## Overview

The Service Advisor Agent provides AWS service recommendations, queries AWS documentation, compares service options, and ranks services based on criteria. This agent helps migration architects select the most appropriate AWS services for their on-premises components.

## Requirements Addressed

- **10.1**: Accept natural language queries about AWS services
- **10.2**: Retrieve information from AWS documentation using MCP (or static knowledge for MVP)
- **10.3**: Provide detailed explanations of AWS service features and capabilities
- **10.4**: Compare multiple AWS services when requested
- **11.1**: Provide multiple AWS service options for components
- **11.2**: Present service options with pros, cons, and cost implications
- **11.3**: Rank service options based on ANZ preferences and best practices

## Action Group Functions

### 1. recommend_services

Recommends AWS services for a specific component.

**Parameters:**
- `component` (object, required): Component object with name, type, technology, and specifications

**Returns:**
- List of ServiceOption objects with recommendations, ranked by suitability

**Example:**
```json
{
  "component": {
    "name": "Web Server",
    "type": "compute",
    "technology": "Apache Tomcat",
    "specifications": {
      "cpu": "4 cores",
      "memory": "16 GB"
    }
  }
}
```

### 2. query_aws_docs

Queries AWS documentation for service information.

**Parameters:**
- `query` (string, required): Natural language query about AWS services

**Returns:**
- Formatted documentation response

**Example:**
```json
{
  "query": "What is Amazon RDS?"
}
```

### 3. compare_services

Compares multiple AWS services side-by-side.

**Parameters:**
- `services` (array, required): List of AWS service names to compare

**Returns:**
- ServiceComparison object with comparison matrix and recommendation

**Example:**
```json
{
  "services": ["Amazon RDS", "Amazon Aurora", "Amazon DynamoDB"]
}
```

### 4. get_service_details

Gets detailed information about a specific AWS service.

**Parameters:**
- `service_name` (string, required): Name of the AWS service

**Returns:**
- Detailed service information including features, use cases, pricing, and documentation links

**Example:**
```json
{
  "service_name": "Amazon EC2"
}
```

## Service Categories

The agent provides recommendations for the following component types:

- **Compute**: EC2, Lambda, Elastic Beanstalk
- **Database**: RDS, Aurora, DynamoDB, ElastiCache
- **Storage**: S3, EBS, EFS
- **Network**: Application Load Balancer, Network Load Balancer, API Gateway
- **Messaging**: SQS, SNS, MSK (Kafka)

## ANZ-Approved Services

The agent maintains a list of ANZ-approved AWS services and prioritizes these in recommendations:

- Amazon EC2
- AWS Lambda
- AWS Elastic Beanstalk
- Amazon RDS
- Amazon Aurora
- Amazon DynamoDB
- Amazon S3
- Amazon EBS
- Amazon EFS
- Application Load Balancer
- Network Load Balancer
- Amazon API Gateway
- Amazon SQS
- Amazon SNS
- Amazon CloudWatch
- AWS IAM
- Amazon VPC

## Ranking Criteria

Services are ranked based on the following criteria:

1. **Suitability**: Pre-ranked based on component type and specifications
2. **ANZ Approval**: ANZ-approved services receive priority
3. **Management Level**: Fully managed services preferred
4. **Cost Efficiency**: Lower cost options ranked higher within category

## Lambda Handler

The module includes a Lambda-compatible handler for Bedrock Agent Action Groups:

```python
from agents.service_advisor import lambda_handler

# Lambda will invoke this handler
response = lambda_handler(event, context)
```

## Usage Example

```python
from agents.service_advisor import ServiceAdvisor

# Initialize advisor
advisor = ServiceAdvisor()

# Get recommendations for a compute component
component = {
    "name": "Web Server",
    "type": "compute",
    "technology": "Apache Tomcat",
    "specifications": {"cpu": "4 cores", "memory": "16 GB"}
}
recommendations = advisor.recommend_services(component)

# Query AWS documentation
docs = advisor.query_aws_docs("What is Amazon RDS?")

# Compare services
comparison = advisor.compare_services([
    "Amazon RDS",
    "Amazon Aurora",
    "Amazon DynamoDB"
])

# Get service details
details = advisor.get_service_details("Amazon EC2")
```

## Future Enhancements

- **MCP Integration**: Connect to AWS Documentation MCP server for real-time documentation
- **Dynamic Pricing**: Integrate with AWS Pricing API for real-time cost estimates
- **Custom Knowledge Base**: Load ANZ-specific service preferences from Bedrock Knowledge Base
- **Service Compatibility**: Check compatibility between selected services
- **Architecture Patterns**: Recommend complete architecture patterns (e.g., 3-tier, microservices)
