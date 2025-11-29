"""
Bedrock agent action group implementations for the AWS Migration Agent System.
"""

from .design_analyzer import (
    DesignAnalyzer,
    DocumentParser,
    Component,
    ComponentType,
    Dependency,
    lambda_handler as design_analyzer_handler
)

from .service_advisor import (
    ServiceAdvisor,
    ServiceOption,
    ServiceComparison,
    ComponentType as ServiceComponentType,
    lambda_handler as service_advisor_handler
)

__all__ = [
    'DesignAnalyzer',
    'DocumentParser',
    'Component',
    'ComponentType',
    'Dependency',
    'design_analyzer_handler',
    'ServiceAdvisor',
    'ServiceOption',
    'ServiceComparison',
    'ServiceComponentType',
    'service_advisor_handler'
]
