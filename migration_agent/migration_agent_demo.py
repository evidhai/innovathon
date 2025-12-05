"""
Demo version of migration agent for testing without AWS credentials
"""
import json
import time
import base64
from pathlib import Path

def hld_lld_input_agent_demo(payload):
    """
    Demo version of HLD/LLD Input Agent for testing without AWS credentials
    """
    print(f"Demo HLD/LLD Input Agent called with payload keys: {list(payload.keys()) if isinstance(payload, dict) else 'string'}")
    
    # Simulate processing time
    time.sleep(2)
    
    # Mock analysis result
    mock_analysis = {
        "architecture_analysis": {
            "system_type": "3-tier web application",
            "complexity_level": "medium",
            "components": [
                {
                    "name": "Web Server",
                    "type": "frontend",
                    "current_technology": "Apache/Nginx",
                    "aws_equivalent": "Application Load Balancer + EC2",
                    "migration_complexity": "low"
                },
                {
                    "name": "Application Server",
                    "type": "backend",
                    "current_technology": "Java/Node.js",
                    "aws_equivalent": "EC2 + Auto Scaling Group",
                    "migration_complexity": "medium"
                },
                {
                    "name": "Database",
                    "type": "data",
                    "current_technology": "MySQL/PostgreSQL",
                    "aws_equivalent": "RDS",
                    "migration_complexity": "medium"
                }
            ],
            "data_flows": [
                {
                    "source": "Web Server",
                    "destination": "Application Server",
                    "protocol": "HTTPS",
                    "data_type": "HTTP requests"
                },
                {
                    "source": "Application Server",
                    "destination": "Database",
                    "protocol": "TCP",
                    "data_type": "SQL queries"
                }
            ]
        },
        "migration_strategy": {
            "recommended_approach": "re-platform",
            "migration_phases": [
                {
                    "phase": "Phase 1: Infrastructure Setup",
                    "components": ["VPC", "Security Groups", "Load Balancer"],
                    "estimated_duration": "1-2 weeks",
                    "dependencies": []
                },
                {
                    "phase": "Phase 2: Database Migration",
                    "components": ["RDS Setup", "Data Migration"],
                    "estimated_duration": "2-3 weeks",
                    "dependencies": ["Phase 1"]
                },
                {
                    "phase": "Phase 3: Application Migration",
                    "components": ["EC2 Setup", "Application Deployment"],
                    "estimated_duration": "3-4 weeks",
                    "dependencies": ["Phase 1", "Phase 2"]
                }
            ],
            "aws_services": [
                {
                    "service": "Amazon VPC",
                    "purpose": "Network isolation and security",
                    "configuration_notes": "Multi-AZ setup recommended"
                },
                {
                    "service": "Application Load Balancer",
                    "purpose": "Distribute incoming traffic",
                    "configuration_notes": "Enable health checks and SSL termination"
                },
                {
                    "service": "Amazon EC2",
                    "purpose": "Host application servers",
                    "configuration_notes": "Use Auto Scaling Groups for high availability"
                },
                {
                    "service": "Amazon RDS",
                    "purpose": "Managed database service",
                    "configuration_notes": "Enable Multi-AZ for production"
                }
            ]
        },
        "infrastructure_requirements": {
            "compute": {
                "instance_types": ["t3.medium", "t3.large"],
                "scaling_requirements": "Auto scaling based on CPU and memory"
            },
            "storage": {
                "types": ["EBS gp3", "RDS storage"],
                "capacity_estimate": "500GB - 1TB"
            },
            "networking": {
                "vpc_requirements": "Multi-AZ VPC with public and private subnets",
                "connectivity_needs": ["Internet Gateway", "NAT Gateway", "VPC Endpoints"]
            }
        },
        "cost_estimation": {
            "monthly_estimate_range": "$800 - $1,500 USD",
            "cost_optimization_opportunities": [
                "Use Reserved Instances for predictable workloads",
                "Implement auto-scaling to optimize resource usage",
                "Use S3 for static content delivery"
            ]
        },
        "security_considerations": {
            "current_security_measures": ["Firewall", "SSL certificates", "Database encryption"],
            "aws_security_services": ["Security Groups", "NACLs", "AWS WAF", "CloudTrail"],
            "compliance_requirements": ["SOC 2", "PCI DSS"]
        },
        "risks_and_challenges": [
            {
                "risk": "Data migration downtime",
                "impact": "high",
                "mitigation": "Use AWS DMS for minimal downtime migration"
            },
            {
                "risk": "Application compatibility issues",
                "impact": "medium",
                "mitigation": "Thorough testing in staging environment"
            }
        ],
        "next_steps": [
            "Set up AWS account and IAM roles",
            "Create VPC and networking infrastructure",
            "Set up RDS instance and migrate data",
            "Deploy application to EC2 instances",
            "Configure monitoring and logging",
            "Perform load testing and optimization"
        ]
    }
    
    # Check if image data was provided
    has_image = isinstance(payload, dict) and ("image_data" in payload or "image_base64" in payload)
    
    result = f"""## HLD/LLD Analysis Complete (Demo Mode)

### Input Analysis:
- Image provided: {'Yes' if has_image else 'No'}
- Query: {payload.get('query', 'No specific query') if isinstance(payload, dict) else str(payload)[:100]}

### Vision Analysis Summary:
**Demo Analysis**: The uploaded architecture diagram shows a typical 3-tier web application with web servers, application servers, and a database layer. The system appears to be designed for moderate scale with load balancing and database replication considerations.

### Structured Migration Plan:
```json
{json.dumps(mock_analysis, indent=2)}
```

### Key Insights:
- Architecture complexity: {mock_analysis['architecture_analysis']['complexity_level']}
- Recommended approach: {mock_analysis['migration_strategy']['recommended_approach']}
- Primary AWS services needed: {len(mock_analysis['migration_strategy']['aws_services'])} services identified

**Note**: This is a demo response. In production, this would use Amazon Nova Vision for image analysis and Amazon Titan Text for structured output generation.

This structured analysis can now be used by other migration tools for detailed planning and cost estimation.
"""
    
    return result

def migration_assistant_demo(payload):
    """
    Demo version of migration assistant for testing without AWS credentials
    """
    # Handle both dict and string inputs
    if isinstance(payload, str):
        user_input = payload
        user_id = "demo_user"
        context = {}
        image_data = None
    else:
        user_input = payload.get("input") or payload.get("prompt", "")
        user_id = payload.get("user_id", "demo_user")
        context = payload.get("context", {})
        image_data = payload.get("image_data")
    
    session_id = context.get("session_id", f"demo_session_{int(time.time())}")
    
    print(f"Demo Migration Assistant")
    print(f"User ID: {user_id}")
    print(f"Session ID: {session_id}")
    print(f"Input: {user_input}")
    print(f"Has Image Data: {bool(image_data)}")
    
    # If image data is provided or HLD/LLD analysis is requested
    if image_data or any(keyword in user_input.lower() for keyword in ['analyze', 'hld', 'lld', 'diagram']):
        print("🖼️ Processing with Demo HLD/LLD Input Agent...")
        hld_payload = {
            "image_data": image_data,
            "image_format": payload.get("image_format", "png") if isinstance(payload, dict) else "png",
            "query": user_input
        }
        return hld_lld_input_agent_demo(hld_payload)
    
    # For other queries, provide demo responses
    time.sleep(1)  # Simulate processing time
    
    if "cost" in user_input.lower():
        return """## AWS Cost Analysis (Demo Mode)

Based on your query about AWS costs, here's a sample analysis:

### EC2 Pricing (us-east-1):
- **t3.medium**: ~$30.37/month (On-Demand)
- **t3.large**: ~$60.74/month (On-Demand)

### RDS MySQL Pricing:
- **db.t3.medium**: ~$52.56/month (On-Demand)

### Total Estimated Monthly Cost:
- **Basic Setup**: $83-113/month
- **Production Setup**: $200-400/month (with redundancy)

### Cost Optimization Recommendations:
1. Use Reserved Instances for 40-60% savings
2. Implement Auto Scaling to optimize usage
3. Use Spot Instances for non-critical workloads

*Note: This is a demo response. Real pricing would be fetched from AWS Pricing API.*"""
    
    elif "architecture" in user_input.lower() or "diagram" in user_input.lower():
        return """## AWS Architecture Recommendation (Demo Mode)

For a serverless web application, I recommend:

### Architecture Components:
1. **Amazon S3** - Static website hosting
2. **Amazon CloudFront** - Content delivery network
3. **Amazon API Gateway** - RESTful API management
4. **AWS Lambda** - Serverless compute
5. **Amazon DynamoDB** - NoSQL database

### Benefits:
- **Scalability**: Automatic scaling based on demand
- **Cost-effective**: Pay only for what you use
- **High availability**: Built-in redundancy across AZs
- **Low maintenance**: Fully managed services

### Next Steps:
1. Set up S3 bucket for static content
2. Configure CloudFront distribution
3. Create API Gateway endpoints
4. Deploy Lambda functions
5. Set up DynamoDB tables

*Note: This is a demo response. Real architecture diagrams would be generated using AWS Diagram MCP server.*"""
    
    elif "migration" in user_input.lower():
        return """## AWS Migration Strategy (Demo Mode)

### Migration Approaches:

1. **Lift and Shift (Rehost)**
   - Fastest migration path
   - Minimal code changes
   - Use EC2 and RDS

2. **Re-platform**
   - Moderate changes for cloud optimization
   - Use managed services like RDS, ELB
   - Better performance and cost optimization

3. **Refactor/Re-architect**
   - Significant changes for cloud-native benefits
   - Use serverless, containers, microservices
   - Maximum cloud benefits

### Migration Tools:
- **AWS Application Migration Service** - Lift and shift
- **AWS Database Migration Service** - Database migrations
- **AWS Server Migration Service** - VM migrations

### Best Practices:
1. Start with a pilot application
2. Assess dependencies and data flows
3. Plan for security and compliance
4. Test thoroughly in staging environment
5. Plan rollback procedures

*Note: This is a demo response. Real migration planning would use AWS documentation and pricing tools.*"""
    
    else:
        return f"""## AWS Migration Assistant (Demo Mode)

Thank you for your query: "{user_input}"

### Available Capabilities:
1. **HLD/LLD Analysis** - Upload architecture diagrams for AI analysis
2. **Cost Estimation** - Get AWS pricing information
3. **Architecture Design** - Generate AWS architecture recommendations
4. **Migration Planning** - Strategic migration guidance
5. **AWS Documentation** - Service information and best practices

### Sample Queries:
- "Help me migrate a 3-tier web application to AWS"
- "What's the cost of running EC2 t3.medium?"
- "Create an architecture for a serverless application"
- "Analyze my uploaded HLD diagram"

### To Get Started:
1. Upload your architecture diagrams for analysis
2. Ask specific questions about AWS services
3. Request cost estimates for your workloads
4. Get migration strategy recommendations

*Note: This is a demo mode. In production, this would connect to AWS services and provide real-time information.*"""

if __name__ == "__main__":
    # Test the demo functions
    test_payload = "Help me migrate a web application to AWS"
    result = migration_assistant_demo(test_payload)
    print("Demo Result:")
    print(result)