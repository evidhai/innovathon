"""
Basic tests for Design Analyzer Agent

These tests verify core functionality of the Design Analyzer module.
"""

import json
from agents.design_analyzer import (
    DesignAnalyzer,
    Component,
    ComponentType,
    Dependency
)


def test_component_creation():
    """Test Component dataclass creation and serialization"""
    component = Component(
        id="comp_1",
        name="Web Server",
        type=ComponentType.COMPUTE,
        technology="Apache Tomcat",
        specifications={"cpu": "4 cores", "memory": "16 GB"},
        dependencies=["Database Server"]
    )
    
    # Test to_dict conversion
    comp_dict = component.to_dict()
    assert comp_dict['name'] == "Web Server"
    assert comp_dict['type'] == "compute"
    assert comp_dict['technology'] == "Apache Tomcat"
    print("✓ Component creation and serialization test passed")


def test_component_classification():
    """Test component type classification"""
    analyzer = DesignAnalyzer()
    
    # Test database classification
    db_type = analyzer._classify_component_type("MySQL Database", "MySQL")
    assert db_type == ComponentType.DATABASE
    
    # Test compute classification
    compute_type = analyzer._classify_component_type("Web Server", "Apache")
    assert compute_type == ComponentType.COMPUTE
    
    # Test storage classification
    storage_type = analyzer._classify_component_type("File Storage", "NFS")
    assert storage_type == ComponentType.STORAGE
    
    # Test messaging classification
    messaging_type = analyzer._classify_component_type("Message Queue", "RabbitMQ")
    assert messaging_type == ComponentType.MESSAGING
    
    print("✓ Component classification test passed")


def test_specification_extraction():
    """Test extraction of specifications from text"""
    analyzer = DesignAnalyzer()
    
    # Test CPU extraction
    line1 = "The server has 8 cores and 32 GB RAM"
    specs1 = analyzer._extract_specifications_from_line(line1)
    assert specs1.get('cpu') == "8 cores"
    assert specs1.get('memory') == "32 GB"
    
    # Test storage extraction
    line2 = "Storage capacity is 500 GB disk"
    specs2 = analyzer._extract_specifications_from_line(line2)
    assert specs2.get('storage') == "500 GB"
    
    print("✓ Specification extraction test passed")


def test_architecture_pattern_identification():
    """Test identification of architecture patterns"""
    analyzer = DesignAnalyzer()
    
    # Test 3-tier pattern
    text1 = "The application uses a 3-tier architecture with presentation layer, business logic, and data layer"
    patterns1 = analyzer._identify_architecture_patterns(text1)
    assert '3-tier' in patterns1
    
    # Test microservices pattern
    text2 = "The system is built using microservices architecture"
    patterns2 = analyzer._identify_architecture_patterns(text2)
    assert 'microservices' in patterns2
    
    print("✓ Architecture pattern identification test passed")


def test_aws_category_mapping():
    """Test AWS service category mapping"""
    analyzer = DesignAnalyzer()
    
    # Create test components
    db_component = Component(
        id="comp_1",
        name="Database",
        type=ComponentType.DATABASE,
        technology="MySQL",
        specifications={},
        dependencies=[]
    )
    
    compute_component = Component(
        id="comp_2",
        name="App Server",
        type=ComponentType.COMPUTE,
        technology="Tomcat",
        specifications={},
        dependencies=[]
    )
    
    analyzer.components = [db_component, compute_component]
    
    # Test mapping
    mapping = analyzer.map_to_aws_categories()
    assert "Database" in mapping
    assert "App Server" in mapping
    assert "RDS" in mapping["Database"] or "DynamoDB" in mapping["Database"]
    assert "EC2" in mapping["App Server"] or "Lambda" in mapping["App Server"]
    
    print("✓ AWS category mapping test passed")


def test_lambda_handler_structure():
    """Test Lambda handler event structure"""
    from agents.design_analyzer import lambda_handler
    
    # Test event structure
    event = {
        'actionGroup': 'DesignAnalyzer',
        'function': 'identify_components',
        'parameters': []
    }
    
    context = {}
    
    # Call handler
    response = lambda_handler(event, context)
    
    # Verify response structure
    assert 'messageVersion' in response
    assert 'response' in response
    assert 'functionResponse' in response['response']
    
    print("✓ Lambda handler structure test passed")


if __name__ == '__main__':
    print("\nRunning Design Analyzer tests...\n")
    
    test_component_creation()
    test_component_classification()
    test_specification_extraction()
    test_architecture_pattern_identification()
    test_aws_category_mapping()
    test_lambda_handler_structure()
    
    print("\n✅ All tests passed!\n")
