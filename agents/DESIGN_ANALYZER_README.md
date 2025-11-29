# Design Analyzer Agent Implementation

## Overview

This module implements the Design Analyzer Agent action groups for the AWS Migration Agent System. It analyzes High-Level Design (HLD) and Low-Level Design (LLD) documents to extract architectural components, technical specifications, dependencies, and AWS service mappings.

## Requirements Coverage

### Requirement 2.1: Identify all application components from HLD documents
✅ **Implemented in**: `analyze_hld()` method
- Parses HLD documents from S3 using Amazon Textract
- Extracts components using pattern matching
- Identifies architecture patterns (3-tier, microservices, etc.)
- Returns structured component data

### Requirement 2.2: Map on-premises components to equivalent AWS services
✅ **Implemented in**: `map_to_aws_categories()` method
- Maps each component to AWS service categories
- Uses component type and technology to determine appropriate AWS services
- Returns mapping dictionary with AWS service recommendations

### Requirement 2.3: Identify dependencies between components
✅ **Implemented in**: `detect_dependencies()` method
- Extracts dependency relationships from document text
- Identifies integration points between components
- Returns structured dependency data with source, target, and type

### Requirement 2.4: Map components to AWS service categories
✅ **Implemented in**: `_determine_aws_category()` method
- Classifies components into AWS service categories
- Provides specific AWS service recommendations per category
- Supports: Compute, Database, Storage, Network, Messaging, Analytics, Security, Management

### Requirement 2.5: Extract technical specifications from LLD documents
✅ **Implemented in**: `analyze_lld()` method
- Parses LLD documents from S3
- Extracts detailed technical specifications
- Captures performance, scalability, security requirements
- Identifies integration points

## Task Completion Checklist

### ✅ Create Python module for document parsing using Textract via Boto3
- **File**: `agents/design_analyzer.py`
- **Class**: `DocumentParser`
- **Method**: `parse_document_from_s3(s3_uri: str) -> str`
- Uses boto3 Textract client to extract text from PDF documents
- Handles S3 URI parsing and error handling

### ✅ Implement function to extract components from HLD documents
- **Method**: `analyze_hld(document_s3_uri: str) -> Dict`
- Extracts components with names, types, technologies, specifications
- Identifies architecture patterns
- Returns structured JSON-serializable output

### ✅ Implement function to extract technical specifications from LLD documents
- **Method**: `analyze_lld(document_s3_uri: str) -> Dict`
- Extracts detailed technical specifications
- Captures performance, scalability, security requirements
- Identifies integration points and APIs

### ✅ Implement function to identify component dependencies
- **Method**: `detect_dependencies() -> List[Dict]`
- Extracts dependency relationships from text
- Identifies source, target, and dependency type
- Updates component dependency lists

### ✅ Implement function to map components to AWS service categories
- **Method**: `map_to_aws_categories() -> Dict[str, str]`
- Maps each component to appropriate AWS service category
- Provides specific service recommendations
- Updates component AWS service mappings

### ✅ Create Lambda-compatible handler for action group functions
- **Function**: `lambda_handler(event, context)`
- Routes requests to appropriate action group functions
- Handles parameter conversion from Bedrock Agent format
- Returns responses in Bedrock Agent format
- Includes error handling and logging

## Module Structure

```
agents/design_analyzer.py
├── ComponentType (Enum)
│   └── AWS service categories
├── Component (Dataclass)
│   └── Application component model
├── Dependency (Dataclass)
│   └── Component dependency model
├── DocumentParser (Class)
│   └── parse_document_from_s3()
├── DesignAnalyzer (Class)
│   ├── analyze_hld()
│   ├── analyze_lld()
│   ├── identify_components()
│   ├── map_to_aws_categories()
│   ├── detect_dependencies()
│   └── Private helper methods
└── Lambda Handlers
    ├── lambda_handler()
    ├── analyze_hld_handler()
    ├── analyze_lld_handler()
    ├── identify_components_handler()
    ├── map_to_aws_categories_handler()
    └── detect_dependencies_handler()
```

## Action Group Functions

### 1. analyze_hld
**Purpose**: Extract high-level architecture from HLD document
**Parameters**: 
- `document_s3_uri` (string): S3 URI of HLD document
**Returns**: JSON with components and architecture patterns

### 2. analyze_lld
**Purpose**: Extract detailed technical specifications from LLD document
**Parameters**: 
- `document_s3_uri` (string): S3 URI of LLD document
**Returns**: JSON with components and technical specifications

### 3. identify_components
**Purpose**: List all identified application components
**Parameters**: None
**Returns**: JSON array of component objects

### 4. map_to_aws_categories
**Purpose**: Map components to AWS service categories
**Parameters**: None
**Returns**: JSON object mapping component names to AWS services

### 5. detect_dependencies
**Purpose**: Identify dependencies between components
**Parameters**: None
**Returns**: JSON array of dependency objects

## Component Classification

The module classifies components into the following AWS service categories:

- **COMPUTE**: Amazon EC2, AWS Lambda, ECS
- **DATABASE**: Amazon RDS, DynamoDB, Aurora
- **STORAGE**: Amazon S3, EBS, EFS
- **NETWORK**: Elastic Load Balancing, API Gateway, CloudFront
- **MESSAGING**: Amazon SQS, SNS, EventBridge, MSK
- **ANALYTICS**: Amazon Athena, EMR, Kinesis
- **SECURITY**: AWS IAM, Secrets Manager, KMS
- **MANAGEMENT**: CloudWatch, CloudTrail, Systems Manager

## Pattern Recognition

The analyzer identifies common architecture patterns:
- 3-tier architecture
- Microservices
- Event-driven
- Serverless
- Monolithic
- Client-server

## Specification Extraction

The module extracts the following specifications from documents:
- **CPU**: Core count and type
- **Memory**: RAM capacity
- **Storage**: Disk capacity
- **Performance requirements**: Latency, throughput
- **Scalability requirements**: Concurrent users, load
- **Security requirements**: Authentication, encryption
- **Integration points**: APIs, endpoints

## Error Handling

The implementation includes comprehensive error handling:
- Invalid S3 URI format validation
- Textract API error handling
- Missing parameter validation
- Exception logging and user-friendly error messages
- Bedrock Agent-compatible error responses

## Usage Example

```python
from agents.design_analyzer import DesignAnalyzer

# Initialize analyzer
analyzer = DesignAnalyzer()

# Analyze HLD document
hld_result = analyzer.analyze_hld('s3://my-bucket/hld.pdf')

# Analyze LLD document
lld_result = analyzer.analyze_lld('s3://my-bucket/lld.pdf')

# Get component mappings
mappings = analyzer.map_to_aws_categories()

# Get dependencies
dependencies = analyzer.detect_dependencies()
```

## Lambda Deployment

The module is designed to be deployed as an AWS Lambda function for Bedrock Agent action groups:

1. Package the module with dependencies
2. Deploy to AWS Lambda
3. Configure as Bedrock Agent action group
4. Set appropriate IAM permissions for S3 and Textract access

## Testing

Basic tests are provided in `tests/test_design_analyzer.py` covering:
- Component creation and serialization
- Component type classification
- Specification extraction
- Architecture pattern identification
- AWS category mapping
- Lambda handler structure

## Dependencies

- boto3 >= 1.35.0 (AWS SDK)
- Python 3.11+
- Standard library: json, re, typing, dataclasses, enum

## Next Steps

This implementation completes Task 5. The next tasks in the implementation plan are:
- Task 6: Implement Service Advisor Agent action groups
- Task 7: Implement Cost Analysis Agent action groups
- Task 8: Implement User Interaction Agent action groups
- Task 9: Implement Report Generator Agent action groups
