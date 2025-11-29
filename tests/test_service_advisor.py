"""
Basic tests for Service Advisor Agent

These tests verify core functionality of the Service Advisor module.
"""

import json
from agents.service_advisor import (
    ServiceAdvisor,
    ServiceOption,
    ServiceComparison,
    ComponentType
)


def test_service_option_creation():
    """Test ServiceOption dataclass creation and serialization"""
    option = ServiceOption(
        service_name="Amazon EC2",
        configuration={"instance_type": "t3.xlarge"},
        pros=["Full control", "Flexible"],
        cons=["Requires management"],
        estimated_monthly_cost=120.00,
        rank=1,
        anz_approved=True,
        documentation_links=["https://docs.aws.amazon.com/ec2/"],
        use_cases=["General compute"]
    )
    
    # Test to_dict conversion
    option_dict = option.to_dict()
    assert option_dict['service_name'] == "Amazon EC2"
    assert option_dict['rank'] == 1
    assert option_dict['anz_approved'] is True
    print("✓ ServiceOption creation and serialization test passed")


def test_compute_recommendations():
    """Test compute service recommendations"""
    advisor = ServiceAdvisor()
    
    component = {
        "name": "Web Server",
        "type": "compute",
        "technology": "Apache Tomcat",
        "specifications": {"cpu": "4 cores", "memory": "16 GB"}
    }
    
    recommendations = advisor.recommend_services(component)
    
    # Verify we get recommendations
    assert len(recommendations) > 0
    
    # Verify structure
    assert 'service_name' in recommendations[0]
    assert 'pros' in recommendations[0]
    assert 'cons' in recommendations[0]
    assert 'estimated_monthly_cost' in recommendations[0]
    
    # Verify we get expected services
    service_names = [rec['service_name'] for rec in recommendations]
    assert any('EC2' in name for name in service_names)
    
    print("✓ Compute recommendations test passed")


def test_database_recommendations():
    """Test database service recommendations"""
    advisor = ServiceAdvisor()
    
    component = {
        "name": "Database",
        "type": "database",
        "technology": "MySQL",
        "specifications": {"storage": "100 GB"}
    }
    
    recommendations = advisor.recommend_services(component)
    
    # Verify we get recommendations
    assert len(recommendations) > 0
    
    # Verify we get database services
    service_names = [rec['service_name'] for rec in recommendations]
    assert any('RDS' in name or 'Aurora' in name for name in service_names)
    
    print("✓ Database recommendations test passed")


def test_storage_recommendations():
    """Test storage service recommendations"""
    advisor = ServiceAdvisor()
    
    component = {
        "name": "File Storage",
        "type": "storage",
        "technology": "NFS",
        "specifications": {}
    }
    
    recommendations = advisor.recommend_services(component)
    
    # Verify we get recommendations
    assert len(recommendations) > 0
    
    # Verify we get storage services
    service_names = [rec['service_name'] for rec in recommendations]
    assert any('S3' in name or 'EFS' in name or 'EBS' in name for name in service_names)
    
    print("✓ Storage recommendations test passed")



def test_messaging_recommendations():
    """Test messaging service recommendations"""
    advisor = ServiceAdvisor()
    
    component = {
        "name": "Message Queue",
        "type": "messaging",
        "technology": "RabbitMQ",
        "specifications": {}
    }
    
    recommendations = advisor.recommend_services(component)
    
    # Verify we get recommendations
    assert len(recommendations) > 0
    
    # Verify we get messaging services
    service_names = [rec['service_name'] for rec in recommendations]
    assert any('SQS' in name or 'SNS' in name for name in service_names)
    
    print("✓ Messaging recommendations test passed")


def test_query_aws_docs():
    """Test AWS documentation query"""
    advisor = ServiceAdvisor()
    
    # Query for RDS
    response = advisor.query_aws_docs("What is Amazon RDS?")
    response_data = json.loads(response)
    
    # Verify response structure
    assert 'query' in response_data or 'response' in response_data
    
    # Query for Lambda
    response2 = advisor.query_aws_docs("Tell me about AWS Lambda")
    response_data2 = json.loads(response2)
    
    assert response_data2 is not None
    
    print("✓ AWS documentation query test passed")


def test_compare_services():
    """Test service comparison"""
    advisor = ServiceAdvisor()
    
    services = ["Amazon RDS", "Amazon Aurora", "Amazon DynamoDB"]
    comparison = advisor.compare_services(services)
    
    # Verify comparison structure
    assert 'services' in comparison
    assert 'comparison_matrix' in comparison
    assert 'recommendation' in comparison
    assert 'reasoning' in comparison
    
    # Verify all services are in comparison
    assert len(comparison['services']) == 3
    assert 'Amazon RDS' in comparison['comparison_matrix']
    
    print("✓ Service comparison test passed")


def test_get_service_details():
    """Test getting service details"""
    advisor = ServiceAdvisor()
    
    # Get EC2 details
    details = advisor.get_service_details("Amazon EC2")
    
    # Verify details structure
    assert 'service_name' in details
    assert 'description' in details
    assert 'features' in details
    assert 'use_cases' in details
    assert 'pros' in details
    assert 'cons' in details
    
    # Verify ANZ approval status
    assert 'anz_approved' in details
    
    print("✓ Service details test passed")


def test_service_ranking():
    """Test service ranking logic"""
    advisor = ServiceAdvisor()
    
    # Create test services
    services = [
        ServiceOption(
            service_name="Service A",
            configuration={},
            pros=["Pro 1"],
            cons=["Con 1"],
            estimated_monthly_cost=100.00,
            rank=2,
            anz_approved=True,
            documentation_links=[],
            use_cases=[]
        ),
        ServiceOption(
            service_name="Service B",
            configuration={},
            pros=["Pro 1"],
            cons=["Con 1"],
            estimated_monthly_cost=150.00,
            rank=1,
            anz_approved=False,
            documentation_links=[],
            use_cases=[]
        )
    ]
    
    # Rank services
    ranked = advisor._rank_services(services, {})
    
    # Verify ranking
    assert len(ranked) == 2
    assert ranked[0].rank <= ranked[1].rank
    
    print("✓ Service ranking test passed")


def test_anz_approved_services():
    """Test ANZ approved services list"""
    advisor = ServiceAdvisor()
    
    # Verify ANZ approved services are loaded
    assert len(advisor.anz_approved_services) > 0
    
    # Verify common services are approved
    assert "Amazon EC2" in advisor.anz_approved_services
    assert "Amazon RDS" in advisor.anz_approved_services
    assert "Amazon S3" in advisor.anz_approved_services
    
    print("✓ ANZ approved services test passed")


def test_lambda_handler_structure():
    """Test Lambda handler event structure"""
    from agents.service_advisor import lambda_handler
    
    # Test recommend_services function
    event = {
        'actionGroup': 'ServiceAdvisor',
        'function': 'recommend_services',
        'parameters': [
            {
                'name': 'component',
                'value': json.dumps({
                    "name": "Web Server",
                    "type": "compute",
                    "technology": "Apache",
                    "specifications": {}
                })
            }
        ]
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
    print("\nRunning Service Advisor tests...\n")
    
    test_service_option_creation()
    test_compute_recommendations()
    test_database_recommendations()
    test_storage_recommendations()
    test_messaging_recommendations()
    test_query_aws_docs()
    test_compare_services()
    test_get_service_details()
    test_service_ranking()
    test_anz_approved_services()
    test_lambda_handler_structure()
    
    print("\n✅ All tests passed!\n")
