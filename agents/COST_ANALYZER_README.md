# Cost Analysis Agent

## Overview

The Cost Analysis Agent is a specialized Bedrock Agent that performs AWS cost estimation, applies ANZ-specific discounts, identifies cost optimization opportunities, and compares on-premises costs with AWS costs.

## Requirements Addressed

- **5.1**: Estimate monthly AWS costs for the proposed architecture
- **5.2**: Calculate total monthly cost for architecture
- **5.3**: Identify cost optimization opportunities
- **5.4**: Apply ANZ-specific pricing agreements and discounts
- **5.5**: Compare on-premises costs with AWS costs

## Action Group Functions

### 1. estimate_service_cost

Estimates the monthly cost for a specific AWS service based on its configuration.

**Parameters:**
- `service` (string, required): AWS service name (e.g., "Amazon EC2", "Amazon RDS")
- `configuration` (object, required): Service configuration details
- `region` (string, optional): AWS region (default: "us-east-1")

**Example Request:**
```json
{
  "service": "Amazon EC2",
  "configuration": {
    "instance_type": "t3.xlarge",
    "instances": 3,
    "pricing_model": "On-Demand"
  }
}
```

**Example Response:**
```json
{
  "service_name": "Amazon EC2",
  "configuration": {
    "instance_type": "t3.xlarge",
    "instances": 3
  },
  "monthly_cost": 364.61,
  "unit_cost": 0.1664,
  "units": 3,
  "pricing_model": "On-Demand",
  "region": "us-east-1"
}
```

### 2. calculate_total_cost

Calculates the total monthly cost for an entire architecture with multiple services.

**Parameters:**
- `architecture` (object, required): Architecture definition with services list
- `region` (string, optional): AWS region (default: "us-east-1")

**Example Request:**
```json
{
  "architecture": {
    "services": [
      {
        "service_name": "Amazon EC2",
        "configuration": {
          "instance_type": "t3.xlarge",
          "instances": 3
        }
      },
      {
        "service_name": "Amazon RDS",
        "configuration": {
          "instance_class": "db.r5.large",
          "storage": "100 GB",
          "multi_az": true
        }
      }
    ]
  }
}
```

**Example Response:**
```json
{
  "total_monthly_cost": 612.45,
  "breakdown": [
    {
      "service_name": "Amazon EC2",
      "monthly_cost": 364.61,
      "configuration": {...}
    },
    {
      "service_name": "Amazon RDS",
      "monthly_cost": 315.90,
      "configuration": {...}
    }
  ],
  "optimizations": [...],
  "anz_discount_applied": 68.04,
  "comparison_with_onprem": null
}
```

### 3. apply_anz_discounts

Applies ANZ-specific enterprise pricing agreements and discounts to a base cost.

**Parameters:**
- `base_cost` (number, required): Base monthly cost before discounts

**Example Request:**
```json
{
  "base_cost": 5000.00
}
```

**Example Response:**
```json
{
  "base_cost": 5000.00,
  "discount_rate": 0.10,
  "discount_amount": 500.00,
  "final_cost": 4500.00,
  "discount_type": "ANZ Enterprise Agreement",
  "savings_percentage": 10.0
}
```

### 4. identify_cost_optimizations

Identifies cost optimization opportunities based on service configurations.

**Parameters:**
- `breakdown` (array, required): Array of ServiceCost objects

**Example Request:**
```json
{
  "breakdown": [
    {
      "service_name": "Amazon EC2",
      "configuration": {
        "instance_type": "t3.xlarge",
        "pricing_model": "On-Demand"
      },
      "monthly_cost": 364.61,
      "unit_cost": 0.1664,
      "units": 3,
      "pricing_model": "On-Demand",
      "region": "us-east-1"
    }
  ]
}
```

**Example Response:**
```json
{
  "optimizations": [
    {
      "recommendation": "Use Reserved Instances for Amazon EC2",
      "current_cost": 364.61,
      "optimized_cost": 218.77,
      "potential_savings": 145.84,
      "effort": "LOW",
      "priority": "HIGH"
    },
    {
      "recommendation": "Right-size Amazon EC2 instances based on utilization",
      "current_cost": 364.61,
      "optimized_cost": 273.46,
      "potential_savings": 91.15,
      "effort": "MEDIUM",
      "priority": "MEDIUM"
    }
  ],
  "count": 2,
  "total_potential_savings": 236.99
}
```

### 5. compare_costs

Compares on-premises monthly costs with AWS monthly costs.

**Parameters:**
- `onprem_cost` (number, required): Monthly on-premises cost
- `aws_cost` (number, required): Monthly AWS cost

**Example Request:**
```json
{
  "onprem_cost": 8000.00,
  "aws_cost": 5420.00
}
```

**Example Response:**
```json
{
  "onprem_monthly_cost": 8000.00,
  "aws_monthly_cost": 5420.00,
  "difference": -2580.00,
  "percentage_change": -32.25,
  "breakeven_months": null
}
```

## Supported AWS Services

The Cost Analyzer supports pricing estimation for the following AWS services:

- **Compute**: Amazon EC2, AWS Lambda, AWS Elastic Beanstalk
- **Database**: Amazon RDS, Amazon Aurora, Amazon DynamoDB, Amazon ElastiCache
- **Storage**: Amazon S3, Amazon EBS, Amazon EFS
- **Network**: Application Load Balancer, Network Load Balancer, Amazon API Gateway
- **Messaging**: Amazon SQS, Amazon SNS, Amazon MSK

## Cost Optimization Strategies

The agent identifies the following types of optimizations:

### EC2 Optimizations
- **Reserved Instances**: 40% savings for 1-year commitment
- **Right-sizing**: 25% savings by matching instance size to utilization

### RDS Optimizations
- **Reserved Instances**: 35% savings for 1-year commitment
- **Multi-AZ**: 50% savings by disabling for non-production environments

### S3 Optimizations
- **Lifecycle Policies**: 30% savings by transitioning to cheaper storage classes

### Lambda Optimizations
- **Memory Optimization**: 20% savings by optimizing memory allocation

### EBS Optimizations
- **Volume Type Migration**: 20% savings by migrating from gp2 to gp3

## ANZ Discount Configuration

The agent applies a 10% enterprise discount rate for ANZ customers. This can be configured by modifying the `anz_discount_rate` in the `CostAnalyzer` class.

## Pricing Data

For the MVP, the agent uses a static pricing catalog with typical AWS pricing as of 2024. In production, this should be replaced with real-time pricing from the AWS Pricing API.

## Lambda Handler

The module includes a Lambda-compatible handler that can be deployed as a Lambda function for Bedrock Agent action groups:

```python
def lambda_handler(event, context):
    # Routes requests to appropriate action group functions
    # Returns responses in Bedrock Agent format
```

## Usage Example

```python
from agents.cost_analyzer import CostAnalyzer

# Initialize analyzer
analyzer = CostAnalyzer(region='us-east-1')

# Estimate service cost
ec2_cost = analyzer.estimate_service_cost(
    service='Amazon EC2',
    configuration={
        'instance_type': 't3.xlarge',
        'instances': 3
    }
)

# Calculate total architecture cost
architecture = {
    'services': [
        {
            'service_name': 'Amazon EC2',
            'configuration': {'instance_type': 't3.xlarge', 'instances': 3}
        },
        {
            'service_name': 'Amazon RDS',
            'configuration': {'instance_class': 'db.r5.large', 'storage': '100 GB', 'multi_az': True}
        }
    ]
}

total_cost = analyzer.calculate_total_cost(architecture)
print(f"Total monthly cost: ${total_cost['total_monthly_cost']}")
print(f"ANZ discount applied: ${total_cost['anz_discount_applied']}")
```

## Integration with Bedrock Agent

This module is designed to be deployed as a Lambda function and configured as an action group for a Bedrock Agent. The agent can invoke these functions to perform cost analysis as part of the migration workflow.

## Future Enhancements

- Integration with AWS Pricing API for real-time pricing
- Support for Savings Plans in addition to Reserved Instances
- Regional pricing variations
- Custom discount rates per customer
- Historical cost tracking and trending
- Cost allocation tags support
- Multi-year TCO analysis
