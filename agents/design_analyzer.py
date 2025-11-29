"""
Design Analyzer Agent Action Groups

This module implements action group functions for the Design Analyzer Agent,
which analyzes HLD and LLD documents to extract architectural components,
technical specifications, dependencies, and AWS service mappings.

Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
"""

import json
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import boto3
from botocore.exceptions import ClientError


class ComponentType(Enum):
    """AWS service categories for component mapping"""
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
class Component:
    """Represents an application component extracted from design documents"""
    id: str
    name: str
    type: ComponentType
    technology: str
    specifications: Dict[str, Any]
    dependencies: List[str]
    aws_service_mapping: Optional[str] = None
    migration_complexity: str = "MEDIUM"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        result['type'] = self.type.value
        return result


@dataclass
class Dependency:
    """Represents a dependency between components"""
    source: str
    target: str
    dependency_type: str
    description: str


class DocumentParser:
    """Handles document parsing using Amazon Textract"""
    
    def __init__(self):
        self.textract_client = boto3.client('textract')
        self.s3_client = boto3.client('s3')
    
    def parse_document_from_s3(self, s3_uri: str) -> str:
        """
        Parse document from S3 using Amazon Textract
        
        Args:
            s3_uri: S3 URI in format s3://bucket/key
            
        Returns:
            Extracted text content
        """
        # Parse S3 URI
        if not s3_uri.startswith('s3://'):
            raise ValueError(f"Invalid S3 URI format: {s3_uri}")
        
        parts = s3_uri[5:].split('/', 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid S3 URI format: {s3_uri}")
        
        bucket, key = parts
        
        try:
            # Use Textract to extract text
            response = self.textract_client.detect_document_text(
                Document={
                    'S3Object': {
                        'Bucket': bucket,
                        'Name': key
                    }
                }
            )
            
            # Extract text from blocks
            text_content = []
            for block in response.get('Blocks', []):
                if block['BlockType'] == 'LINE':
                    text_content.append(block['Text'])
            
            return '\n'.join(text_content)
            
        except ClientError as e:
            raise Exception(f"Failed to parse document from S3: {str(e)}")


class DesignAnalyzer:
    """Main analyzer for extracting architecture information from design documents"""
    
    def __init__(self):
        self.parser = DocumentParser()
        self.components: List[Component] = []
        self.dependencies: List[Dependency] = []

    
    def analyze_hld(self, document_s3_uri: str) -> Dict:
        """
        Extract high-level architecture from HLD document
        
        Requirement 2.1: Identify all application components from HLD documents
        
        Args:
            document_s3_uri: S3 URI of the HLD document
            
        Returns:
            Dictionary containing extracted components and architecture patterns
        """
        # Parse document
        text_content = self.parser.parse_document_from_s3(document_s3_uri)
        
        # Extract components
        components = self._extract_components_from_text(text_content, doc_type='HLD')
        
        # Identify architecture patterns
        patterns = self._identify_architecture_patterns(text_content)
        
        return {
            'components': [comp.to_dict() for comp in components],
            'architecture_patterns': patterns,
            'document_type': 'HLD',
            'source_uri': document_s3_uri
        }
    
    def analyze_lld(self, document_s3_uri: str) -> Dict:
        """
        Extract detailed technical specifications from LLD document
        
        Requirement 2.2: Extract technical specifications from LLD documents
        
        Args:
            document_s3_uri: S3 URI of the LLD document
            
        Returns:
            Dictionary containing detailed technical specifications
        """
        # Parse document
        text_content = self.parser.parse_document_from_s3(document_s3_uri)
        
        # Extract detailed specifications
        components = self._extract_components_from_text(text_content, doc_type='LLD')
        
        # Extract technical details
        technical_specs = self._extract_technical_specifications(text_content)
        
        return {
            'components': [comp.to_dict() for comp in components],
            'technical_specifications': technical_specs,
            'document_type': 'LLD',
            'source_uri': document_s3_uri
        }
    
    def identify_components(self) -> List[Dict]:
        """
        List all application components with metadata
        
        Returns:
            List of component dictionaries
        """
        return [comp.to_dict() for comp in self.components]
    
    def map_to_aws_categories(self) -> Dict[str, str]:
        """
        Map components to AWS service categories
        
        Requirement 2.2: Map on-premises components to equivalent AWS services
        
        Returns:
            Dictionary mapping component names to AWS service categories
        """
        mapping = {}
        
        for component in self.components:
            # Map based on technology and type
            aws_category = self._determine_aws_category(component)
            mapping[component.name] = aws_category
            
            # Update component with mapping
            component.aws_service_mapping = aws_category
        
        return mapping
    
    def detect_dependencies(self) -> List[Dict]:
        """
        Identify component dependencies and integration points
        
        Requirement 2.3: Identify dependencies between components
        
        Returns:
            List of dependency dictionaries
        """
        return [asdict(dep) for dep in self.dependencies]
    
    def _extract_components_from_text(self, text: str, doc_type: str) -> List[Component]:
        """
        Extract components from document text using pattern matching
        
        Args:
            text: Document text content
            doc_type: Type of document (HLD or LLD)
            
        Returns:
            List of Component objects
        """
        components = []
        component_id = 1
        
        # Common component keywords and patterns
        component_patterns = [
            r'(?i)(web\s+server|application\s+server|database|load\s+balancer|cache|message\s+queue)',
            r'(?i)(frontend|backend|api\s+gateway|microservice)',
            r'(?i)(storage|file\s+system|object\s+store)',
        ]
        
        # Technology patterns
        tech_patterns = {
            'apache': 'Apache HTTP Server',
            'tomcat': 'Apache Tomcat',
            'nginx': 'Nginx',
            'mysql': 'MySQL',
            'postgresql': 'PostgreSQL',
            'oracle': 'Oracle Database',
            'mongodb': 'MongoDB',
            'redis': 'Redis',
            'rabbitmq': 'RabbitMQ',
            'kafka': 'Apache Kafka',
        }
        
        lines = text.split('\n')
        current_component = None
        
        for line in lines:
            line_lower = line.lower()
            
            # Check for component mentions
            for pattern in component_patterns:
                matches = re.finditer(pattern, line, re.IGNORECASE)
                for match in matches:
                    component_name = match.group(1).strip()
                    
                    # Determine technology
                    technology = "Unknown"
                    for tech_key, tech_name in tech_patterns.items():
                        if tech_key in line_lower:
                            technology = tech_name
                            break
                    
                    # Extract specifications from context
                    specs = self._extract_specifications_from_line(line)
                    
                    # Determine component type
                    comp_type = self._classify_component_type(component_name, technology)
                    
                    # Create component
                    component = Component(
                        id=f"comp_{component_id}",
                        name=component_name,
                        type=comp_type,
                        technology=technology,
                        specifications=specs,
                        dependencies=[]
                    )
                    
                    components.append(component)
                    component_id += 1
        
        # Store components
        self.components.extend(components)
        
        # Extract dependencies
        self._extract_dependencies_from_text(text)
        
        return components
    
    def _extract_specifications_from_line(self, line: str) -> Dict[str, Any]:
        """Extract technical specifications from a line of text"""
        specs = {}
        
        # CPU pattern
        cpu_match = re.search(r'(\d+)\s*(core|cpu|vcpu)', line, re.IGNORECASE)
        if cpu_match:
            specs['cpu'] = f"{cpu_match.group(1)} cores"
        
        # Memory pattern
        mem_match = re.search(r'(\d+)\s*(gb|mb|gib|mib)\s*(ram|memory)', line, re.IGNORECASE)
        if mem_match:
            specs['memory'] = f"{mem_match.group(1)} {mem_match.group(2).upper()}"
        
        # Storage pattern
        storage_match = re.search(r'(\d+)\s*(gb|tb|gib|tib)\s*(storage|disk)', line, re.IGNORECASE)
        if storage_match:
            specs['storage'] = f"{storage_match.group(1)} {storage_match.group(2).upper()}"
        
        return specs
    
    def _classify_component_type(self, name: str, technology: str) -> ComponentType:
        """Classify component into AWS service category"""
        name_lower = name.lower()
        tech_lower = technology.lower()
        
        # Database patterns
        if any(keyword in name_lower for keyword in ['database', 'db', 'sql', 'nosql']):
            return ComponentType.DATABASE
        if any(keyword in tech_lower for keyword in ['mysql', 'postgresql', 'oracle', 'mongodb', 'redis']):
            return ComponentType.DATABASE
        
        # Compute patterns
        if any(keyword in name_lower for keyword in ['server', 'compute', 'application', 'backend', 'frontend']):
            return ComponentType.COMPUTE
        if any(keyword in tech_lower for keyword in ['tomcat', 'apache', 'nginx']):
            return ComponentType.COMPUTE
        
        # Storage patterns
        if any(keyword in name_lower for keyword in ['storage', 'file', 'object', 'blob']):
            return ComponentType.STORAGE
        
        # Network patterns
        if any(keyword in name_lower for keyword in ['load balancer', 'gateway', 'proxy', 'firewall']):
            return ComponentType.NETWORK
        
        # Messaging patterns
        if any(keyword in name_lower for keyword in ['queue', 'message', 'event', 'stream']):
            return ComponentType.MESSAGING
        if any(keyword in tech_lower for keyword in ['rabbitmq', 'kafka', 'activemq']):
            return ComponentType.MESSAGING
        
        return ComponentType.UNKNOWN

    
    def _extract_dependencies_from_text(self, text: str):
        """
        Extract dependencies between components from text
        
        Requirement 2.3: Identify dependencies between components
        """
        # Dependency keywords
        dependency_keywords = [
            'depends on', 'requires', 'connects to', 'integrates with',
            'calls', 'uses', 'communicates with', 'sends to', 'receives from'
        ]
        
        lines = text.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            
            # Check for dependency keywords
            for keyword in dependency_keywords:
                if keyword in line_lower:
                    # Try to extract source and target components
                    for source_comp in self.components:
                        if source_comp.name.lower() in line_lower:
                            for target_comp in self.components:
                                if target_comp.name.lower() in line_lower and source_comp.id != target_comp.id:
                                    # Create dependency
                                    dependency = Dependency(
                                        source=source_comp.name,
                                        target=target_comp.name,
                                        dependency_type=keyword,
                                        description=line.strip()
                                    )
                                    self.dependencies.append(dependency)
                                    
                                    # Add to component's dependency list
                                    if target_comp.name not in source_comp.dependencies:
                                        source_comp.dependencies.append(target_comp.name)
    
    def _identify_architecture_patterns(self, text: str) -> List[str]:
        """Identify common architecture patterns in the document"""
        patterns = []
        text_lower = text.lower()
        
        # Pattern keywords
        pattern_map = {
            '3-tier': ['3-tier', 'three tier', 'presentation layer', 'business logic', 'data layer'],
            'microservices': ['microservice', 'micro-service', 'service-oriented'],
            'event-driven': ['event-driven', 'event driven', 'message queue', 'pub/sub'],
            'serverless': ['serverless', 'lambda', 'function as a service'],
            'monolithic': ['monolithic', 'monolith'],
            'client-server': ['client-server', 'client server'],
        }
        
        for pattern_name, keywords in pattern_map.items():
            if any(keyword in text_lower for keyword in keywords):
                patterns.append(pattern_name)
        
        return patterns if patterns else ['unknown']
    
    def _extract_technical_specifications(self, text: str) -> Dict[str, Any]:
        """Extract detailed technical specifications from LLD"""
        specs = {
            'performance_requirements': [],
            'scalability_requirements': [],
            'security_requirements': [],
            'integration_points': []
        }
        
        lines = text.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            
            # Performance requirements
            if any(keyword in line_lower for keyword in ['performance', 'latency', 'throughput', 'response time']):
                specs['performance_requirements'].append(line.strip())
            
            # Scalability requirements
            if any(keyword in line_lower for keyword in ['scalability', 'scale', 'concurrent', 'users']):
                specs['scalability_requirements'].append(line.strip())
            
            # Security requirements
            if any(keyword in line_lower for keyword in ['security', 'authentication', 'authorization', 'encryption']):
                specs['security_requirements'].append(line.strip())
            
            # Integration points
            if any(keyword in line_lower for keyword in ['integration', 'api', 'interface', 'endpoint']):
                specs['integration_points'].append(line.strip())
        
        return specs
    
    def _determine_aws_category(self, component: Component) -> str:
        """
        Determine AWS service category for a component
        
        Requirement 2.4: Map components to AWS service categories
        """
        type_to_aws_category = {
            ComponentType.COMPUTE: "Amazon EC2 / AWS Lambda / ECS",
            ComponentType.DATABASE: "Amazon RDS / DynamoDB / Aurora",
            ComponentType.STORAGE: "Amazon S3 / EBS / EFS",
            ComponentType.NETWORK: "Elastic Load Balancing / API Gateway / CloudFront",
            ComponentType.MESSAGING: "Amazon SQS / SNS / EventBridge / MSK",
            ComponentType.ANALYTICS: "Amazon Athena / EMR / Kinesis",
            ComponentType.SECURITY: "AWS IAM / Secrets Manager / KMS",
            ComponentType.MANAGEMENT: "CloudWatch / CloudTrail / Systems Manager",
            ComponentType.UNKNOWN: "Requires manual review"
        }
        
        return type_to_aws_category.get(component.type, "Unknown")


# Lambda-compatible handler functions for Bedrock Agent Action Groups

def lambda_handler(event, context):
    """
    Main Lambda handler for Design Analyzer Agent action groups
    
    This handler routes requests to appropriate action group functions
    based on the action specified in the event.
    """
    action = event.get('actionGroup', '')
    function = event.get('function', '')
    parameters = event.get('parameters', [])
    
    # Convert parameters list to dictionary
    params_dict = {}
    for param in parameters:
        params_dict[param['name']] = param['value']
    
    # Initialize analyzer
    analyzer = DesignAnalyzer()
    
    try:
        # Route to appropriate function
        if function == 'analyze_hld':
            result = analyze_hld_handler(params_dict, analyzer)
        elif function == 'analyze_lld':
            result = analyze_lld_handler(params_dict, analyzer)
        elif function == 'identify_components':
            result = identify_components_handler(params_dict, analyzer)
        elif function == 'map_to_aws_categories':
            result = map_to_aws_categories_handler(params_dict, analyzer)
        elif function == 'detect_dependencies':
            result = detect_dependencies_handler(params_dict, analyzer)
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


def analyze_hld_handler(params: Dict, analyzer: DesignAnalyzer) -> Dict:
    """Handler for analyze_hld action"""
    document_s3_uri = params.get('document_s3_uri', '')
    
    if not document_s3_uri:
        return {'error': 'Missing required parameter: document_s3_uri'}
    
    return analyzer.analyze_hld(document_s3_uri)


def analyze_lld_handler(params: Dict, analyzer: DesignAnalyzer) -> Dict:
    """Handler for analyze_lld action"""
    document_s3_uri = params.get('document_s3_uri', '')
    
    if not document_s3_uri:
        return {'error': 'Missing required parameter: document_s3_uri'}
    
    return analyzer.analyze_lld(document_s3_uri)


def identify_components_handler(params: Dict, analyzer: DesignAnalyzer) -> Dict:
    """Handler for identify_components action"""
    components = analyzer.identify_components()
    return {
        'components': components,
        'count': len(components)
    }


def map_to_aws_categories_handler(params: Dict, analyzer: DesignAnalyzer) -> Dict:
    """Handler for map_to_aws_categories action"""
    mapping = analyzer.map_to_aws_categories()
    return {
        'mappings': mapping,
        'count': len(mapping)
    }


def detect_dependencies_handler(params: Dict, analyzer: DesignAnalyzer) -> Dict:
    """Handler for detect_dependencies action"""
    dependencies = analyzer.detect_dependencies()
    return {
        'dependencies': dependencies,
        'count': len(dependencies)
    }
