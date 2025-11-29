"""
Service Advisor Agent Action Groups

This module implements action group functions for the Service Advisor Agent,
which provides AWS service recommendations, queries AWS documentation via MCP,
compares service options, and ranks services based on criteria.

Requirements: 10.1, 10.2, 10.3, 10.4, 11.1, 11.2, 11.3
"""

import json
import boto3
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
from botocore.exceptions import ClientError


class ComponentType(Enum):
    """Component types for service recommendations"""
    COMPUTE = "compute"
    DATABASE = "database"
    STORAGE = "storage"
    NETWORK = "network"
    MESSAGING = "messaging"
    ANALYTICS = "analytics"
    SECURITY = "security"
    MANAGEMENT = "management"
    UNKNOWN = "unknown"


@dataclass
class ServiceOption:
    """Represents an AWS service recommendation option"""
    service_name: str
    configuration: Dict[str, Any]
    pros: List[str]
    cons: List[str]
    estimated_monthly_cost: float
    rank: int
    anz_approved: bool
    documentation_links: List[str]
    use_cases: List[str]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


@dataclass
class ServiceComparison:
    """Represents a comparison between multiple AWS services"""
    services: List[str]
    comparison_matrix: Dict[str, Dict[str, Any]]
    recommendation: str
    reasoning: str


class ServiceAdvisor:
    """Main advisor for AWS service recommendations and comparisons"""
    
    def __init__(self):
        # AWS service knowledge base (static for MVP, can be enhanced with MCP)
        self.service_catalog = self._initialize_service_catalog()
        self.anz_approved_services = self._load_anz_approved_services()
    
    def recommend_services(self, component: Dict) -> List[Dict]:
        """
        Recommend AWS services for a component
        
        Requirement 10.1: Accept queries about AWS services
        Requirement 11.1: Provide multiple AWS service options
        
        Args:
            component: Component dictionary with name, type, technology, specifications
            
        Returns:
            List of ServiceOption dictionaries ranked by suitability
        """
        component_type = component.get('type', 'unknown')
        component_name = component.get('name', 'Unknown Component')
        specifications = component.get('specifications', {})
        technology = component.get('technology', 'Unknown')
        
        # Get service recommendations based on component type
        recommendations = self._get_recommendations_by_type(
            component_type, 
            specifications, 
            technology
        )
        
        # Rank services
        ranked_services = self._rank_services(recommendations, specifications)
        
        return [service.to_dict() for service in ranked_services]
    
    def query_aws_docs(self, query: str) -> str:
        """
        Query AWS documentation via MCP (if available) or use static knowledge
        
        Requirement 10.2: Retrieve information from AWS documentation
        
        Args:
            query: Natural language query about AWS services
            
        Returns:
            Response with AWS service information
        """
        # For MVP, use static knowledge base
        # In production, this would integrate with MCP for real-time AWS docs
        
        query_lower = query.lower()
        
        # Search service catalog for relevant information
        relevant_services = []
        
        for service_name, service_info in self.service_catalog.items():
            # Check if query matches service name or description
            if (service_name.lower() in query_lower or 
                query_lower in service_info.get('description', '').lower() or
                any(keyword in query_lower for keyword in service_info.get('keywords', []))):
                relevant_services.append({
                    'service': service_name,
                    'description': service_info.get('description', ''),
                    'use_cases': service_info.get('use_cases', []),
                    'documentation_link': service_info.get('documentation_link', '')
                })
        
        if not relevant_services:
            return json.dumps({
                'response': 'No specific AWS service information found for your query. Please refine your question.',
                'suggestion': 'Try asking about specific AWS services like EC2, RDS, S3, Lambda, etc.'
            })
        
        return json.dumps({
            'query': query,
            'relevant_services': relevant_services,
            'count': len(relevant_services)
        })

    
    def compare_services(self, services: List[str]) -> Dict:
        """
        Compare multiple AWS services
        
        Requirement 10.4: Compare multiple AWS services when requested
        
        Args:
            services: List of AWS service names to compare
            
        Returns:
            ServiceComparison dictionary with comparison matrix
        """
        if len(services) < 2:
            return {
                'error': 'At least 2 services required for comparison'
            }
        
        comparison_matrix = {}
        
        for service_name in services:
            service_info = self.service_catalog.get(service_name, {})
            
            if not service_info:
                comparison_matrix[service_name] = {
                    'error': f'Service {service_name} not found in catalog'
                }
                continue
            
            comparison_matrix[service_name] = {
                'description': service_info.get('description', ''),
                'pricing_model': service_info.get('pricing_model', 'Unknown'),
                'management_level': service_info.get('management_level', 'Unknown'),
                'scalability': service_info.get('scalability', 'Unknown'),
                'use_cases': service_info.get('use_cases', []),
                'pros': service_info.get('pros', []),
                'cons': service_info.get('cons', []),
                'anz_approved': service_name in self.anz_approved_services
            }
        
        # Generate recommendation
        recommendation = self._generate_comparison_recommendation(services, comparison_matrix)
        
        comparison = ServiceComparison(
            services=services,
            comparison_matrix=comparison_matrix,
            recommendation=recommendation['service'],
            reasoning=recommendation['reasoning']
        )
        
        return asdict(comparison)
    
    def get_service_details(self, service_name: str) -> Dict:
        """
        Get detailed information about an AWS service
        
        Requirement 10.3: Provide detailed explanations of AWS service features
        
        Args:
            service_name: Name of the AWS service
            
        Returns:
            Dictionary with detailed service information
        """
        service_info = self.service_catalog.get(service_name, {})
        
        if not service_info:
            return {
                'error': f'Service {service_name} not found in catalog',
                'available_services': list(self.service_catalog.keys())
            }
        
        return {
            'service_name': service_name,
            'description': service_info.get('description', ''),
            'features': service_info.get('features', []),
            'use_cases': service_info.get('use_cases', []),
            'pricing_model': service_info.get('pricing_model', ''),
            'management_level': service_info.get('management_level', ''),
            'scalability': service_info.get('scalability', ''),
            'pros': service_info.get('pros', []),
            'cons': service_info.get('cons', []),
            'documentation_link': service_info.get('documentation_link', ''),
            'anz_approved': service_name in self.anz_approved_services
        }

    
    def _get_recommendations_by_type(
        self, 
        component_type: str, 
        specifications: Dict, 
        technology: str
    ) -> List[ServiceOption]:
        """
        Get service recommendations based on component type
        
        Requirement 11.2: Present service options with pros, cons, and cost implications
        """
        recommendations = []
        
        # Compute recommendations
        if component_type == 'compute':
            recommendations.extend(self._recommend_compute_services(specifications, technology))
        
        # Database recommendations
        elif component_type == 'database':
            recommendations.extend(self._recommend_database_services(specifications, technology))
        
        # Storage recommendations
        elif component_type == 'storage':
            recommendations.extend(self._recommend_storage_services(specifications))
        
        # Network recommendations
        elif component_type == 'network':
            recommendations.extend(self._recommend_network_services(specifications, technology))
        
        # Messaging recommendations
        elif component_type == 'messaging':
            recommendations.extend(self._recommend_messaging_services(specifications, technology))
        
        else:
            # Default recommendations for unknown types
            recommendations.append(ServiceOption(
                service_name="Manual Review Required",
                configuration={'note': 'Component type requires manual analysis'},
                pros=['Customized solution'],
                cons=['Requires expert consultation'],
                estimated_monthly_cost=0.0,
                rank=1,
                anz_approved=False,
                documentation_links=[],
                use_cases=['Unknown component types']
            ))
        
        return recommendations
    
    def _recommend_compute_services(self, specifications: Dict, technology: str) -> List[ServiceOption]:
        """Recommend compute services based on specifications"""
        recommendations = []
        
        # Amazon EC2
        recommendations.append(ServiceOption(
            service_name="Amazon EC2",
            configuration={
                'instance_type': 't3.xlarge',
                'vcpu': 4,
                'memory': '16 GB',
                'storage': 'EBS gp3'
            },
            pros=[
                'Full control over instance configuration',
                'Wide range of instance types',
                'Flexible pricing options (On-Demand, Reserved, Spot)',
                'Supports all operating systems and applications'
            ],
            cons=[
                'Requires manual management and patching',
                'Higher operational overhead',
                'Need to manage scaling manually or with Auto Scaling'
            ],
            estimated_monthly_cost=120.00,
            rank=2,
            anz_approved=True,
            documentation_links=['https://docs.aws.amazon.com/ec2/'],
            use_cases=['Legacy applications', 'Custom configurations', 'Long-running workloads']
        ))

        
        # AWS Elastic Beanstalk
        recommendations.append(ServiceOption(
            service_name="AWS Elastic Beanstalk",
            configuration={
                'platform': 'Java with Tomcat' if 'tomcat' in technology.lower() else 'Python',
                'instance_type': 't3.medium',
                'auto_scaling': 'enabled'
            },
            pros=[
                'Managed platform with automatic scaling',
                'Easy deployment and updates',
                'Built-in monitoring and health checks',
                'Supports multiple languages and frameworks'
            ],
            cons=[
                'Less control than EC2',
                'Platform limitations',
                'May not support all custom configurations'
            ],
            estimated_monthly_cost=150.00,
            rank=1,
            anz_approved=True,
            documentation_links=['https://docs.aws.amazon.com/elasticbeanstalk/'],
            use_cases=['Web applications', 'API backends', 'Microservices']
        ))
        
        # AWS Lambda (for suitable workloads)
        recommendations.append(ServiceOption(
            service_name="AWS Lambda",
            configuration={
                'memory': '1024 MB',
                'timeout': '15 minutes',
                'runtime': 'Python 3.11'
            },
            pros=[
                'Serverless - no infrastructure management',
                'Pay only for execution time',
                'Automatic scaling',
                'Integrated with AWS services'
            ],
            cons=[
                'Cold start latency',
                '15-minute execution limit',
                'Stateless execution model',
                'May require application refactoring'
            ],
            estimated_monthly_cost=50.00,
            rank=3,
            anz_approved=True,
            documentation_links=['https://docs.aws.amazon.com/lambda/'],
            use_cases=['Event-driven workloads', 'APIs', 'Batch processing', 'Microservices']
        ))
        
        return recommendations
    
    def _recommend_database_services(self, specifications: Dict, technology: str) -> List[ServiceOption]:
        """Recommend database services based on specifications"""
        recommendations = []
        tech_lower = technology.lower()
        
        # Determine if relational or NoSQL
        is_relational = any(db in tech_lower for db in ['mysql', 'postgresql', 'oracle', 'sql server'])
        is_nosql = any(db in tech_lower for db in ['mongodb', 'cassandra', 'dynamodb'])
        is_cache = any(db in tech_lower for db in ['redis', 'memcached'])
        
        if is_relational or 'sql' in tech_lower:
            # Amazon RDS
            recommendations.append(ServiceOption(
                service_name="Amazon RDS",
                configuration={
                    'engine': 'MySQL' if 'mysql' in tech_lower else 'PostgreSQL',
                    'instance_class': 'db.r5.large',
                    'storage': '100 GB gp3',
                    'multi_az': True
                },
                pros=[
                    'Managed relational database',
                    'Automated backups and patching',
                    'Multi-AZ for high availability',
                    'Read replicas for scaling'
                ],
                cons=[
                    'Less control than self-managed',
                    'Some features may not be available',
                    'Costs can be higher than EC2-based databases'
                ],
                estimated_monthly_cost=280.00,
                rank=1,
                anz_approved=True,
                documentation_links=['https://docs.aws.amazon.com/rds/'],
                use_cases=['Transactional workloads', 'OLTP', 'Traditional applications']
            ))

            
            # Amazon Aurora
            recommendations.append(ServiceOption(
                service_name="Amazon Aurora",
                configuration={
                    'engine': 'Aurora MySQL' if 'mysql' in tech_lower else 'Aurora PostgreSQL',
                    'instance_class': 'db.r5.large',
                    'storage': 'Auto-scaling',
                    'replicas': 2
                },
                pros=[
                    'High performance (5x MySQL, 3x PostgreSQL)',
                    'Auto-scaling storage',
                    'Up to 15 read replicas',
                    'Continuous backup to S3'
                ],
                cons=[
                    'Higher cost than RDS',
                    'MySQL/PostgreSQL compatibility only',
                    'Vendor lock-in'
                ],
                estimated_monthly_cost=400.00,
                rank=2,
                anz_approved=True,
                documentation_links=['https://docs.aws.amazon.com/aurora/'],
                use_cases=['High-performance applications', 'Large-scale databases', 'Read-heavy workloads']
            ))
        
        if is_nosql or not is_relational:
            # Amazon DynamoDB
            recommendations.append(ServiceOption(
                service_name="Amazon DynamoDB",
                configuration={
                    'capacity_mode': 'On-Demand',
                    'encryption': 'enabled',
                    'point_in_time_recovery': True
                },
                pros=[
                    'Fully managed NoSQL',
                    'Single-digit millisecond latency',
                    'Automatic scaling',
                    'Built-in security and backup'
                ],
                cons=[
                    'Different data model than relational',
                    'Query limitations',
                    'Requires data modeling expertise'
                ],
                estimated_monthly_cost=200.00,
                rank=1 if is_nosql else 3,
                anz_approved=True,
                documentation_links=['https://docs.aws.amazon.com/dynamodb/'],
                use_cases=['High-scale applications', 'Real-time applications', 'Serverless architectures']
            ))
        
        if is_cache:
            # Amazon ElastiCache
            recommendations.append(ServiceOption(
                service_name="Amazon ElastiCache",
                configuration={
                    'engine': 'Redis' if 'redis' in tech_lower else 'Memcached',
                    'node_type': 'cache.r5.large',
                    'num_nodes': 2
                },
                pros=[
                    'Managed in-memory cache',
                    'Sub-millisecond latency',
                    'Supports Redis and Memcached',
                    'Automatic failover'
                ],
                cons=[
                    'In-memory only (volatile)',
                    'Cost for high memory requirements',
                    'Requires cache strategy'
                ],
                estimated_monthly_cost=180.00,
                rank=1,
                anz_approved=True,
                documentation_links=['https://docs.aws.amazon.com/elasticache/'],
                use_cases=['Session storage', 'Caching layer', 'Real-time analytics']
            ))
        
        return recommendations

    
    def _recommend_storage_services(self, specifications: Dict) -> List[ServiceOption]:
        """Recommend storage services based on specifications"""
        recommendations = []
        
        # Amazon S3
        recommendations.append(ServiceOption(
            service_name="Amazon S3",
            configuration={
                'storage_class': 'S3 Standard',
                'versioning': 'enabled',
                'encryption': 'SSE-S3'
            },
            pros=[
                'Highly durable (99.999999999%)',
                'Unlimited scalability',
                'Multiple storage classes for cost optimization',
                'Integrated with most AWS services'
            ],
            cons=[
                'Object storage (not file system)',
                'Eventual consistency for some operations',
                'Requires application changes for file system workloads'
            ],
            estimated_monthly_cost=50.00,
            rank=1,
            anz_approved=True,
            documentation_links=['https://docs.aws.amazon.com/s3/'],
            use_cases=['Object storage', 'Backups', 'Data lakes', 'Static websites']
        ))
        
        # Amazon EFS
        recommendations.append(ServiceOption(
            service_name="Amazon EFS",
            configuration={
                'performance_mode': 'General Purpose',
                'throughput_mode': 'Bursting',
                'storage_class': 'Standard'
            },
            pros=[
                'Fully managed NFS file system',
                'Elastic scaling',
                'Multi-AZ availability',
                'POSIX-compliant'
            ],
            cons=[
                'Higher cost than S3',
                'Performance depends on size',
                'Linux only'
            ],
            estimated_monthly_cost=150.00,
            rank=2,
            anz_approved=True,
            documentation_links=['https://docs.aws.amazon.com/efs/'],
            use_cases=['Shared file storage', 'Content management', 'Web serving', 'Container storage']
        ))
        
        # Amazon EBS
        recommendations.append(ServiceOption(
            service_name="Amazon EBS",
            configuration={
                'volume_type': 'gp3',
                'size': '100 GB',
                'iops': 3000
            },
            pros=[
                'Block storage for EC2',
                'High performance',
                'Snapshots for backup',
                'Multiple volume types'
            ],
            cons=[
                'Attached to single EC2 instance',
                'AZ-specific',
                'Requires EC2 instance'
            ],
            estimated_monthly_cost=10.00,
            rank=3,
            anz_approved=True,
            documentation_links=['https://docs.aws.amazon.com/ebs/'],
            use_cases=['EC2 instance storage', 'Databases on EC2', 'Boot volumes']
        ))
        
        return recommendations

    
    def _recommend_network_services(self, specifications: Dict, technology: str) -> List[ServiceOption]:
        """Recommend network services based on specifications"""
        recommendations = []
        tech_lower = technology.lower()
        
        if 'load balancer' in tech_lower or 'lb' in tech_lower:
            # Application Load Balancer
            recommendations.append(ServiceOption(
                service_name="Application Load Balancer",
                configuration={
                    'scheme': 'internet-facing',
                    'ip_address_type': 'ipv4',
                    'cross_zone': True
                },
                pros=[
                    'Layer 7 load balancing',
                    'Content-based routing',
                    'WebSocket support',
                    'Integrated with AWS services'
                ],
                cons=[
                    'Higher cost than NLB',
                    'Not suitable for TCP/UDP',
                    'Adds latency'
                ],
                estimated_monthly_cost=25.00,
                rank=1,
                anz_approved=True,
                documentation_links=['https://docs.aws.amazon.com/elasticloadbalancing/'],
                use_cases=['HTTP/HTTPS applications', 'Microservices', 'Container applications']
            ))
            
            # Network Load Balancer
            recommendations.append(ServiceOption(
                service_name="Network Load Balancer",
                configuration={
                    'scheme': 'internet-facing',
                    'ip_address_type': 'ipv4',
                    'cross_zone': True
                },
                pros=[
                    'Layer 4 load balancing',
                    'Ultra-low latency',
                    'Static IP support',
                    'Millions of requests per second'
                ],
                cons=[
                    'No content-based routing',
                    'Less features than ALB',
                    'Higher cost for low traffic'
                ],
                estimated_monthly_cost=25.00,
                rank=2,
                anz_approved=True,
                documentation_links=['https://docs.aws.amazon.com/elasticloadbalancing/'],
                use_cases=['TCP/UDP applications', 'High performance', 'Static IP requirements']
            ))
        
        if 'gateway' in tech_lower or 'api' in tech_lower:
            # Amazon API Gateway
            recommendations.append(ServiceOption(
                service_name="Amazon API Gateway",
                configuration={
                    'type': 'REST API',
                    'endpoint_type': 'Regional',
                    'throttling': 'enabled'
                },
                pros=[
                    'Fully managed API service',
                    'Built-in authentication',
                    'Request/response transformation',
                    'Integrated with Lambda'
                ],
                cons=[
                    'Cost per request',
                    '29-second timeout',
                    'Learning curve'
                ],
                estimated_monthly_cost=35.00,
                rank=1,
                anz_approved=True,
                documentation_links=['https://docs.aws.amazon.com/apigateway/'],
                use_cases=['REST APIs', 'WebSocket APIs', 'Serverless backends']
            ))
        
        return recommendations

    
    def _recommend_messaging_services(self, specifications: Dict, technology: str) -> List[ServiceOption]:
        """Recommend messaging services based on specifications"""
        recommendations = []
        tech_lower = technology.lower()
        
        # Amazon SQS
        recommendations.append(ServiceOption(
            service_name="Amazon SQS",
            configuration={
                'queue_type': 'Standard',
                'message_retention': '4 days',
                'visibility_timeout': '30 seconds'
            },
            pros=[
                'Fully managed message queue',
                'Unlimited throughput',
                'No message loss',
                'Easy to use'
            ],
            cons=[
                'At-least-once delivery (Standard)',
                'No message ordering (Standard)',
                'Limited message size (256 KB)'
            ],
            estimated_monthly_cost=10.00,
            rank=1,
            anz_approved=True,
            documentation_links=['https://docs.aws.amazon.com/sqs/'],
            use_cases=['Decoupling microservices', 'Batch processing', 'Asynchronous workflows']
        ))
        
        # Amazon SNS
        recommendations.append(ServiceOption(
            service_name="Amazon SNS",
            configuration={
                'topic_type': 'Standard',
                'encryption': 'enabled'
            },
            pros=[
                'Pub/sub messaging',
                'Fan-out to multiple subscribers',
                'Mobile push notifications',
                'Email/SMS support'
            ],
            cons=[
                'No message persistence',
                'At-least-once delivery',
                'Limited filtering'
            ],
            estimated_monthly_cost=5.00,
            rank=2,
            anz_approved=True,
            documentation_links=['https://docs.aws.amazon.com/sns/'],
            use_cases=['Event notifications', 'Fan-out patterns', 'Mobile notifications']
        ))
        
        if 'kafka' in tech_lower:
            # Amazon MSK
            recommendations.append(ServiceOption(
                service_name="Amazon MSK",
                configuration={
                    'kafka_version': '3.5.1',
                    'broker_instance_type': 'kafka.m5.large',
                    'brokers_per_az': 1
                },
                pros=[
                    'Managed Apache Kafka',
                    'Kafka API compatible',
                    'High throughput',
                    'Exactly-once semantics'
                ],
                cons=[
                    'Higher cost than SQS/SNS',
                    'More complex to manage',
                    'Requires Kafka expertise'
                ],
                estimated_monthly_cost=300.00,
                rank=1,
                anz_approved=True,
                documentation_links=['https://docs.aws.amazon.com/msk/'],
                use_cases=['Event streaming', 'Log aggregation', 'Real-time analytics']
            ))
        
        return recommendations

    
    def _rank_services(
        self, 
        services: List[ServiceOption], 
        specifications: Dict
    ) -> List[ServiceOption]:
        """
        Rank services based on criteria
        
        Requirement 11.3: Rank service options based on ANZ preferences and best practices
        
        Ranking criteria:
        1. ANZ approval status
        2. Cost efficiency
        3. Management level (prefer managed services)
        4. Suitability for specifications
        """
        # Services are already ranked in recommendation functions
        # Sort by rank (lower is better)
        sorted_services = sorted(services, key=lambda s: s.rank)
        
        # Boost ANZ-approved services
        for service in sorted_services:
            if service.anz_approved and service.rank > 1:
                service.rank = max(1, service.rank - 1)
        
        # Re-sort after ANZ boost
        sorted_services = sorted(sorted_services, key=lambda s: s.rank)
        
        return sorted_services
    
    def _generate_comparison_recommendation(
        self, 
        services: List[str], 
        comparison_matrix: Dict
    ) -> Dict:
        """Generate recommendation from service comparison"""
        # Simple scoring based on ANZ approval and management level
        scores = {}
        
        for service_name, details in comparison_matrix.items():
            if 'error' in details:
                scores[service_name] = -1
                continue
            
            score = 0
            
            # ANZ approval adds points
            if details.get('anz_approved', False):
                score += 10
            
            # Managed services preferred
            if details.get('management_level') == 'Fully Managed':
                score += 5
            
            scores[service_name] = score
        
        # Find highest scoring service
        best_service = max(scores, key=scores.get)
        
        reasoning = f"{best_service} is recommended based on "
        reasons = []
        
        if comparison_matrix[best_service].get('anz_approved'):
            reasons.append("ANZ approval")
        if comparison_matrix[best_service].get('management_level') == 'Fully Managed':
            reasons.append("fully managed service")
        
        reasoning += " and ".join(reasons) if reasons else "overall suitability"
        
        return {
            'service': best_service,
            'reasoning': reasoning
        }

    
    def _initialize_service_catalog(self) -> Dict[str, Dict]:
        """
        Initialize AWS service catalog with static knowledge
        
        In production, this could be enhanced with MCP integration
        for real-time AWS documentation
        """
        return {
            'Amazon EC2': {
                'description': 'Virtual servers in the cloud',
                'pricing_model': 'Per hour/second',
                'management_level': 'Self-managed',
                'scalability': 'Manual or Auto Scaling',
                'features': ['Multiple instance types', 'Flexible configurations', 'Spot instances'],
                'use_cases': ['General compute', 'Legacy applications', 'Custom workloads'],
                'pros': ['Full control', 'Wide range of options', 'Flexible pricing'],
                'cons': ['Requires management', 'Operational overhead'],
                'documentation_link': 'https://docs.aws.amazon.com/ec2/',
                'keywords': ['compute', 'virtual machine', 'instance', 'server']
            },
            'AWS Lambda': {
                'description': 'Run code without provisioning servers',
                'pricing_model': 'Per request and duration',
                'management_level': 'Fully Managed',
                'scalability': 'Automatic',
                'features': ['Event-driven', 'Auto-scaling', 'Pay per use'],
                'use_cases': ['Serverless applications', 'Event processing', 'APIs'],
                'pros': ['No infrastructure management', 'Cost-efficient', 'Auto-scaling'],
                'cons': ['Cold starts', 'Execution limits', 'Stateless'],
                'documentation_link': 'https://docs.aws.amazon.com/lambda/',
                'keywords': ['serverless', 'function', 'event-driven', 'faas']
            },
            'Amazon RDS': {
                'description': 'Managed relational database service',
                'pricing_model': 'Per hour + storage',
                'management_level': 'Fully Managed',
                'scalability': 'Vertical scaling + Read replicas',
                'features': ['Automated backups', 'Multi-AZ', 'Read replicas'],
                'use_cases': ['Relational databases', 'OLTP', 'Traditional apps'],
                'pros': ['Managed service', 'High availability', 'Automated maintenance'],
                'cons': ['Less control', 'Cost', 'Some feature limitations'],
                'documentation_link': 'https://docs.aws.amazon.com/rds/',
                'keywords': ['database', 'relational', 'sql', 'mysql', 'postgresql']
            },
            'Amazon DynamoDB': {
                'description': 'Fast and flexible NoSQL database',
                'pricing_model': 'Per request or provisioned capacity',
                'management_level': 'Fully Managed',
                'scalability': 'Automatic',
                'features': ['Single-digit ms latency', 'Auto-scaling', 'Global tables'],
                'use_cases': ['NoSQL workloads', 'High-scale apps', 'Real-time'],
                'pros': ['High performance', 'Serverless option', 'Auto-scaling'],
                'cons': ['Different data model', 'Query limitations', 'Learning curve'],
                'documentation_link': 'https://docs.aws.amazon.com/dynamodb/',
                'keywords': ['nosql', 'database', 'key-value', 'document']
            },
            'Amazon S3': {
                'description': 'Object storage service',
                'pricing_model': 'Per GB stored + requests',
                'management_level': 'Fully Managed',
                'scalability': 'Unlimited',
                'features': ['11 9s durability', 'Versioning', 'Lifecycle policies'],
                'use_cases': ['Object storage', 'Backups', 'Data lakes', 'Static hosting'],
                'pros': ['Highly durable', 'Scalable', 'Cost-effective'],
                'cons': ['Object storage model', 'Eventual consistency'],
                'documentation_link': 'https://docs.aws.amazon.com/s3/',
                'keywords': ['storage', 'object', 'bucket', 'file']
            },
            'Application Load Balancer': {
                'description': 'Layer 7 load balancing',
                'pricing_model': 'Per hour + LCU',
                'management_level': 'Fully Managed',
                'scalability': 'Automatic',
                'features': ['Content-based routing', 'WebSocket', 'HTTP/2'],
                'use_cases': ['Web applications', 'Microservices', 'Containers'],
                'pros': ['Advanced routing', 'Integrated with AWS', 'Auto-scaling'],
                'cons': ['Cost', 'Latency', 'HTTP/HTTPS only'],
                'documentation_link': 'https://docs.aws.amazon.com/elasticloadbalancing/',
                'keywords': ['load balancer', 'alb', 'layer 7', 'http']
            },
            'Amazon SQS': {
                'description': 'Fully managed message queuing service',
                'pricing_model': 'Per request',
                'management_level': 'Fully Managed',
                'scalability': 'Unlimited',
                'features': ['At-least-once delivery', 'Dead letter queues', 'Long polling'],
                'use_cases': ['Decoupling', 'Async processing', 'Microservices'],
                'pros': ['Simple', 'Scalable', 'Reliable'],
                'cons': ['No ordering (Standard)', 'Message size limits'],
                'documentation_link': 'https://docs.aws.amazon.com/sqs/',
                'keywords': ['queue', 'message', 'messaging', 'async']
            }
        }
    
    def _load_anz_approved_services(self) -> List[str]:
        """
        Load ANZ-approved AWS services list
        
        In production, this would query the Knowledge Base
        """
        return [
            'Amazon EC2',
            'AWS Lambda',
            'AWS Elastic Beanstalk',
            'Amazon RDS',
            'Amazon Aurora',
            'Amazon DynamoDB',
            'Amazon S3',
            'Amazon EFS',
            'Amazon EBS',
            'Application Load Balancer',
            'Network Load Balancer',
            'Amazon API Gateway',
            'Amazon SQS',
            'Amazon SNS',
            'Amazon MSK',
            'Amazon ElastiCache'
        ]



# Lambda-compatible handler functions for Bedrock Agent Action Groups

def lambda_handler(event, context):
    """
    Main Lambda handler for Service Advisor Agent action groups
    
    This handler routes requests to appropriate action group functions
    based on the action specified in the event.
    
    Requirements: 10.1, 10.2, 10.3, 10.4, 11.1, 11.2, 11.3
    """
    action = event.get('actionGroup', '')
    function = event.get('function', '')
    parameters = event.get('parameters', [])
    
    # Convert parameters list to dictionary
    params_dict = {}
    for param in parameters:
        params_dict[param['name']] = param['value']
    
    # Initialize advisor
    advisor = ServiceAdvisor()
    
    try:
        # Route to appropriate function
        if function == 'recommend_services':
            result = recommend_services_handler(params_dict, advisor)
        elif function == 'query_aws_docs':
            result = query_aws_docs_handler(params_dict, advisor)
        elif function == 'compare_services':
            result = compare_services_handler(params_dict, advisor)
        elif function == 'get_service_details':
            result = get_service_details_handler(params_dict, advisor)
        else:
            result = {
                'error': f'Unknown function: {function}'
            }
        
        # Return response in Bedrock Agent format
        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': action,
                'function': function,
                'functionResponse': {
                    'responseBody': {
                        'TEXT': {
                            'body': json.dumps(result)
                        }
                    }
                }
            }
        }
    
    except Exception as e:
        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': action,
                'function': function,
                'functionResponse': {
                    'responseBody': {
                        'TEXT': {
                            'body': json.dumps({
                                'error': str(e)
                            })
                        }
                    }
                }
            }
        }


def recommend_services_handler(params: Dict, advisor: ServiceAdvisor) -> Dict:
    """
    Handler for recommend_services action
    
    Requirement 11.1: Provide multiple AWS service options for each component
    """
    # Component can be passed as JSON string or dict
    component = params.get('component', {})
    
    if isinstance(component, str):
        try:
            component = json.loads(component)
        except json.JSONDecodeError:
            return {'error': 'Invalid component JSON format'}
    
    if not component:
        return {'error': 'Missing required parameter: component'}
    
    recommendations = advisor.recommend_services(component)
    
    return {
        'component_name': component.get('name', 'Unknown'),
        'recommendations': recommendations,
        'count': len(recommendations)
    }


def query_aws_docs_handler(params: Dict, advisor: ServiceAdvisor) -> Dict:
    """
    Handler for query_aws_docs action
    
    Requirement 10.2: Retrieve information from AWS documentation via MCP
    """
    query = params.get('query', '')
    
    if not query:
        return {'error': 'Missing required parameter: query'}
    
    response = advisor.query_aws_docs(query)
    
    # Response is already JSON string
    return json.loads(response)


def compare_services_handler(params: Dict, advisor: ServiceAdvisor) -> Dict:
    """
    Handler for compare_services action
    
    Requirement 10.4: Compare multiple AWS services when requested
    """
    # Services can be passed as JSON array string or list
    services = params.get('services', [])
    
    if isinstance(services, str):
        try:
            services = json.loads(services)
        except json.JSONDecodeError:
            return {'error': 'Invalid services JSON format'}
    
    if not services or len(services) < 2:
        return {'error': 'At least 2 services required for comparison'}
    
    return advisor.compare_services(services)


def get_service_details_handler(params: Dict, advisor: ServiceAdvisor) -> Dict:
    """
    Handler for get_service_details action
    
    Requirement 10.3: Provide detailed explanations of AWS service features
    """
    service_name = params.get('service_name', '')
    
    if not service_name:
        return {'error': 'Missing required parameter: service_name'}
    
    return advisor.get_service_details(service_name)
