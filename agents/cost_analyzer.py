"""
Cost Analysis Agent Action Groups

This module implements action group functions for the Cost Analysis Agent,
which performs AWS cost estimation, applies ANZ discounts, identifies cost
optimization opportunities, and compares on-premises vs AWS costs.

Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
"""

import json
import boto3
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from decimal import Decimal
from botocore.exceptions import ClientError


@dataclass
class ServiceCost:
    """Represents cost for a single AWS service"""
    service_name: str
    configuration: Dict[str, Any]
    monthly_cost: float
    unit_cost: float
    units: int
    pricing_model: str
    region: str = "us-east-1"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


@dataclass
class CostOptimization:
    """Represents a cost optimization opportunity"""
    recommendation: str
    current_cost: float
    optimized_cost: float
    potential_savings: float
    effort: str  # LOW, MEDIUM, HIGH
    priority: str  # LOW, MEDIUM, HIGH
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


@dataclass
class CostComparison:
    """Represents comparison between on-premises and AWS costs"""
    onprem_monthly_cost: float
    aws_monthly_cost: float
    difference: float
    percentage_change: float
    breakeven_months: Optional[int]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


@dataclass
class CostEstimate:
    """Complete cost estimate for an architecture"""
    total_monthly_cost: float
    breakdown: List[ServiceCost]
    optimizations: List[CostOptimization]
    anz_discount_applied: float
    comparison_with_onprem: Optional[CostComparison]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        result['breakdown'] = [item.to_dict() if hasattr(item, 'to_dict') else item for item in self.breakdown]
        result['optimizations'] = [item.to_dict() if hasattr(item, 'to_dict') else item for item in self.optimizations]
        if self.comparison_with_onprem:
            result['comparison_with_onprem'] = self.comparison_with_onprem.to_dict()
        return result


class CostAnalyzer:
    """Main analyzer for AWS cost estimation and optimization"""
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.pricing_client = boto3.client('pricing', region_name='us-east-1')  # Pricing API only in us-east-1
        
        # Mock pricing data for MVP (in production, use Pricing API)
        self.pricing_catalog = self._initialize_pricing_catalog()
        
        # ANZ discount rates (mock data)
        self.anz_discount_rate = 0.10  # 10% discount
    
    def estimate_service_cost(self, service: str, configuration: Dict) -> Dict:
        """
        Estimate cost for a specific AWS service
        
        Requirement 5.1: Estimate monthly AWS costs for proposed architecture
        
        Args:
            service: AWS service name (e.g., "Amazon EC2", "Amazon RDS")
            configuration: Service configuration dictionary
            
        Returns:
            Dictionary with cost estimate details
        """
        service_pricing = self.pricing_catalog.get(service, {})
        
        if not service_pricing:
            return {
                'error': f'Pricing data not available for service: {service}',
                'service': service,
                'estimated_monthly_cost': 0.0
            }
        
        # Calculate cost based on service type
        monthly_cost = self._calculate_service_cost(service, configuration, service_pricing)
        
        service_cost = ServiceCost(
            service_name=service,
            configuration=configuration,
            monthly_cost=monthly_cost,
            unit_cost=service_pricing.get('unit_cost', 0.0),
            units=configuration.get('units', 1),
            pricing_model=service_pricing.get('pricing_model', 'On-Demand'),
            region=self.region
        )
        
        return service_cost.to_dict()

    
    def calculate_total_cost(self, architecture: Dict) -> Dict:
        """
        Calculate total monthly cost for architecture
        
        Requirement 5.2: Calculate total monthly cost for architecture
        
        Args:
            architecture: Dictionary containing list of services and configurations
            
        Returns:
            Complete cost estimate dictionary
        """
        services = architecture.get('services', [])
        
        if not services:
            return {
                'error': 'No services provided in architecture',
                'total_monthly_cost': 0.0
            }
        
        # Calculate cost for each service
        breakdown = []
        total_cost = 0.0
        
        for service_config in services:
            service_name = service_config.get('service_name', '')
            configuration = service_config.get('configuration', {})
            
            cost_result = self.estimate_service_cost(service_name, configuration)
            
            if 'error' not in cost_result:
                service_cost = ServiceCost(**cost_result)
                breakdown.append(service_cost)
                total_cost += service_cost.monthly_cost
        
        # Apply ANZ discount
        anz_discount = total_cost * self.anz_discount_rate
        total_with_discount = total_cost - anz_discount
        
        # Identify optimizations
        optimizations = self.identify_cost_optimizations(breakdown)
        
        # Create cost estimate
        cost_estimate = CostEstimate(
            total_monthly_cost=round(total_with_discount, 2),
            breakdown=breakdown,
            optimizations=optimizations,
            anz_discount_applied=round(anz_discount, 2),
            comparison_with_onprem=None
        )
        
        return cost_estimate.to_dict()
    
    def apply_anz_discounts(self, base_cost: float) -> Dict:
        """
        Apply ANZ-specific pricing agreements and discounts
        
        Requirement 5.4: Apply ANZ-specific pricing agreements and discounts
        
        Args:
            base_cost: Base monthly cost before discounts
            
        Returns:
            Dictionary with discount details
        """
        discount_amount = base_cost * self.anz_discount_rate
        final_cost = base_cost - discount_amount
        
        return {
            'base_cost': round(base_cost, 2),
            'discount_rate': self.anz_discount_rate,
            'discount_amount': round(discount_amount, 2),
            'final_cost': round(final_cost, 2),
            'discount_type': 'ANZ Enterprise Agreement',
            'savings_percentage': round(self.anz_discount_rate * 100, 1)
        }
    
    def identify_cost_optimizations(self, breakdown: List[ServiceCost]) -> List[CostOptimization]:
        """
        Identify cost optimization opportunities
        
        Requirement 5.3: Identify cost optimization opportunities
        
        Args:
            breakdown: List of ServiceCost objects
            
        Returns:
            List of CostOptimization objects
        """
        optimizations = []
        
        for service_cost in breakdown:
            service_name = service_cost.service_name
            config = service_cost.configuration
            current_cost = service_cost.monthly_cost
            
            # EC2 optimizations
            if service_name == "Amazon EC2":
                # Reserved Instance recommendation
                if config.get('pricing_model', 'On-Demand') == 'On-Demand':
                    ri_savings = current_cost * 0.40  # 40% savings with 1-year RI
                    optimizations.append(CostOptimization(
                        recommendation=f"Use Reserved Instances for {service_name}",
                        current_cost=current_cost,
                        optimized_cost=current_cost - ri_savings,
                        potential_savings=ri_savings,
                        effort="LOW",
                        priority="HIGH"
                    ))
                
                # Right-sizing recommendation
                instance_type = config.get('instance_type', '')
                if 'xlarge' in instance_type or 'large' in instance_type:
                    rightsizing_savings = current_cost * 0.25  # 25% savings
                    optimizations.append(CostOptimization(
                        recommendation=f"Right-size {service_name} instances based on utilization",
                        current_cost=current_cost,
                        optimized_cost=current_cost - rightsizing_savings,
                        potential_savings=rightsizing_savings,
                        effort="MEDIUM",
                        priority="MEDIUM"
                    ))
            
            # RDS optimizations
            elif service_name == "Amazon RDS":
                # Reserved Instance recommendation
                if config.get('pricing_model', 'On-Demand') == 'On-Demand':
                    ri_savings = current_cost * 0.35  # 35% savings with 1-year RI
                    optimizations.append(CostOptimization(
                        recommendation=f"Use Reserved Instances for {service_name}",
                        current_cost=current_cost,
                        optimized_cost=current_cost - ri_savings,
                        potential_savings=ri_savings,
                        effort="LOW",
                        priority="HIGH"
                    ))
                
                # Multi-AZ optimization
                if config.get('multi_az', False):
                    multi_az_savings = current_cost * 0.50  # 50% savings by disabling Multi-AZ for non-prod
                    optimizations.append(CostOptimization(
                        recommendation=f"Disable Multi-AZ for non-production {service_name} instances",
                        current_cost=current_cost,
                        optimized_cost=current_cost - multi_az_savings,
                        potential_savings=multi_az_savings,
                        effort="LOW",
                        priority="MEDIUM"
                    ))
            
            # S3 optimizations
            elif service_name == "Amazon S3":
                # Lifecycle policy recommendation
                storage_class = config.get('storage_class', 'S3 Standard')
                if storage_class == 'S3 Standard':
                    lifecycle_savings = current_cost * 0.30  # 30% savings with lifecycle policies
                    optimizations.append(CostOptimization(
                        recommendation=f"Implement S3 lifecycle policies to transition to cheaper storage classes",
                        current_cost=current_cost,
                        optimized_cost=current_cost - lifecycle_savings,
                        potential_savings=lifecycle_savings,
                        effort="LOW",
                        priority="MEDIUM"
                    ))
            
            # Lambda optimizations
            elif service_name == "AWS Lambda":
                # Memory optimization
                memory = config.get('memory', 1024)
                if memory > 512:
                    memory_savings = current_cost * 0.20  # 20% savings with optimized memory
                    optimizations.append(CostOptimization(
                        recommendation=f"Optimize Lambda memory allocation based on actual usage",
                        current_cost=current_cost,
                        optimized_cost=current_cost - memory_savings,
                        potential_savings=memory_savings,
                        effort="MEDIUM",
                        priority="LOW"
                    ))
            
            # EBS optimizations
            elif service_name == "Amazon EBS":
                # Volume type optimization
                volume_type = config.get('volume_type', 'gp3')
                if volume_type == 'gp2':
                    gp3_savings = current_cost * 0.20  # 20% savings with gp3
                    optimizations.append(CostOptimization(
                        recommendation=f"Migrate EBS volumes from gp2 to gp3",
                        current_cost=current_cost,
                        optimized_cost=current_cost - gp3_savings,
                        potential_savings=gp3_savings,
                        effort="LOW",
                        priority="MEDIUM"
                    ))
        
        # Sort by potential savings (highest first)
        optimizations.sort(key=lambda x: x.potential_savings, reverse=True)
        
        return optimizations
    
    def compare_costs(self, onprem_cost: float, aws_cost: float) -> Dict:
        """
        Compare on-premises vs AWS costs
        
        Requirement 5.5: Compare on-premises costs with AWS costs
        
        Args:
            onprem_cost: Monthly on-premises cost
            aws_cost: Monthly AWS cost
            
        Returns:
            CostComparison dictionary
        """
        difference = aws_cost - onprem_cost
        percentage_change = (difference / onprem_cost * 100) if onprem_cost > 0 else 0
        
        # Calculate breakeven (if AWS is more expensive initially)
        # Assume on-prem has upfront costs that are amortized
        breakeven_months = None
        if difference > 0:
            # Assume on-prem has 20% of annual cost as upfront
            onprem_upfront = onprem_cost * 12 * 0.20
            if difference > 0:
                breakeven_months = int(onprem_upfront / difference)
        
        comparison = CostComparison(
            onprem_monthly_cost=round(onprem_cost, 2),
            aws_monthly_cost=round(aws_cost, 2),
            difference=round(difference, 2),
            percentage_change=round(percentage_change, 2),
            breakeven_months=breakeven_months
        )
        
        return comparison.to_dict()
    
    def _calculate_service_cost(
        self, 
        service: str, 
        configuration: Dict, 
        pricing: Dict
    ) -> float:
        """
        Calculate monthly cost for a service based on configuration
        
        Args:
            service: Service name
            configuration: Service configuration
            pricing: Pricing information from catalog
            
        Returns:
            Monthly cost in USD
        """
        base_cost = pricing.get('base_monthly_cost', 0.0)
        unit_cost = pricing.get('unit_cost', 0.0)
        
        # Service-specific calculations
        if service == "Amazon EC2":
            instance_type = configuration.get('instance_type', 't3.medium')
            instances = configuration.get('instances', 1)
            hours_per_month = 730  # Average hours per month
            
            # Get instance pricing
            instance_pricing = pricing.get('instance_types', {}).get(instance_type, 0.05)
            monthly_cost = instance_pricing * hours_per_month * instances
            
            return monthly_cost
        
        elif service == "Amazon RDS":
            instance_class = configuration.get('instance_class', 'db.t3.medium')
            storage_gb = int(configuration.get('storage', '100').split()[0])
            multi_az = configuration.get('multi_az', False)
            hours_per_month = 730
            
            # Get instance pricing
            instance_pricing = pricing.get('instance_classes', {}).get(instance_class, 0.068)
            storage_pricing = pricing.get('storage_cost_per_gb', 0.115)
            
            instance_cost = instance_pricing * hours_per_month
            storage_cost = storage_gb * storage_pricing
            
            monthly_cost = instance_cost + storage_cost
            
            # Double cost for Multi-AZ
            if multi_az:
                monthly_cost *= 2
            
            return monthly_cost
        
        elif service == "Amazon Aurora":
            instance_class = configuration.get('instance_class', 'db.r5.large')
            storage_gb = configuration.get('storage_gb', 100)
            replicas = configuration.get('replicas', 0)
            hours_per_month = 730
            
            # Get instance pricing
            instance_pricing = pricing.get('instance_classes', {}).get(instance_class, 0.29)
            storage_pricing = pricing.get('storage_cost_per_gb', 0.10)
            io_pricing = pricing.get('io_cost_per_million', 0.20)
            
            # Primary instance
            primary_cost = instance_pricing * hours_per_month
            
            # Replicas
            replica_cost = instance_pricing * hours_per_month * replicas
            
            # Storage (auto-scaling, estimate)
            storage_cost = storage_gb * storage_pricing
            
            # IO (estimate 1M requests per month)
            io_cost = io_pricing
            
            monthly_cost = primary_cost + replica_cost + storage_cost + io_cost
            
            return monthly_cost
        
        elif service == "Amazon DynamoDB":
            capacity_mode = configuration.get('capacity_mode', 'On-Demand')
            
            if capacity_mode == 'On-Demand':
                # Estimate based on typical usage
                read_units = configuration.get('estimated_read_units', 1000000)
                write_units = configuration.get('estimated_write_units', 500000)
                
                read_cost = (read_units / 1000000) * pricing.get('on_demand_read_per_million', 0.25)
                write_cost = (write_units / 1000000) * pricing.get('on_demand_write_per_million', 1.25)
                
                monthly_cost = read_cost + write_cost
            else:
                # Provisioned capacity
                read_capacity = configuration.get('read_capacity_units', 5)
                write_capacity = configuration.get('write_capacity_units', 5)
                hours_per_month = 730
                
                read_cost = read_capacity * pricing.get('provisioned_read_per_hour', 0.00013) * hours_per_month
                write_cost = write_capacity * pricing.get('provisioned_write_per_hour', 0.00065) * hours_per_month
                
                monthly_cost = read_cost + write_cost
            
            # Add storage cost
            storage_gb = configuration.get('storage_gb', 10)
            storage_cost = storage_gb * pricing.get('storage_cost_per_gb', 0.25)
            
            monthly_cost += storage_cost
            
            return monthly_cost
        
        elif service == "Amazon S3":
            storage_gb = configuration.get('storage_gb', 100)
            storage_class = configuration.get('storage_class', 'S3 Standard')
            requests = configuration.get('requests_per_month', 10000)
            
            # Storage cost
            storage_pricing = pricing.get('storage_classes', {}).get(storage_class, 0.023)
            storage_cost = storage_gb * storage_pricing
            
            # Request cost (per 1000 requests)
            request_cost = (requests / 1000) * pricing.get('request_cost_per_1000', 0.0004)
            
            monthly_cost = storage_cost + request_cost
            
            return monthly_cost
        
        elif service == "Amazon EBS":
            volume_type = configuration.get('volume_type', 'gp3')
            size_gb = int(configuration.get('size', '100').split()[0])
            volumes = configuration.get('volumes', 1)
            
            # Get volume pricing
            volume_pricing = pricing.get('volume_types', {}).get(volume_type, 0.08)
            
            monthly_cost = size_gb * volume_pricing * volumes
            
            return monthly_cost
        
        elif service == "AWS Lambda":
            memory_mb = configuration.get('memory', 1024)
            invocations = configuration.get('invocations_per_month', 1000000)
            avg_duration_ms = configuration.get('avg_duration_ms', 200)
            
            # Request cost
            request_cost = (invocations / 1000000) * pricing.get('request_cost_per_million', 0.20)
            
            # Compute cost (GB-seconds)
            gb_seconds = (memory_mb / 1024) * (avg_duration_ms / 1000) * invocations
            compute_cost = (gb_seconds / 1000000) * pricing.get('compute_cost_per_million_gb_seconds', 16.67)
            
            monthly_cost = request_cost + compute_cost
            
            return monthly_cost
        
        elif service == "Application Load Balancer" or service == "Network Load Balancer":
            hours_per_month = 730
            lcu_hours = configuration.get('lcu_hours', 730)  # Assume 1 LCU per hour
            
            # Fixed cost
            fixed_cost = hours_per_month * pricing.get('hourly_cost', 0.0225)
            
            # LCU cost
            lcu_cost = lcu_hours * pricing.get('lcu_cost', 0.008)
            
            monthly_cost = fixed_cost + lcu_cost
            
            return monthly_cost
        
        elif service == "Amazon ElastiCache":
            node_type = configuration.get('node_type', 'cache.t3.medium')
            num_nodes = configuration.get('num_nodes', 1)
            hours_per_month = 730
            
            # Get node pricing
            node_pricing = pricing.get('node_types', {}).get(node_type, 0.068)
            
            monthly_cost = node_pricing * hours_per_month * num_nodes
            
            return monthly_cost
        
        elif service == "Amazon SQS":
            requests = configuration.get('requests_per_month', 1000000)
            
            # First 1M requests free
            billable_requests = max(0, requests - 1000000)
            
            monthly_cost = (billable_requests / 1000000) * pricing.get('cost_per_million_requests', 0.40)
            
            return monthly_cost
        
        elif service == "Amazon SNS":
            requests = configuration.get('requests_per_month', 1000000)
            
            # First 1M requests free
            billable_requests = max(0, requests - 1000000)
            
            monthly_cost = (billable_requests / 1000000) * pricing.get('cost_per_million_requests', 0.50)
            
            return monthly_cost
        
        elif service == "Amazon API Gateway":
            requests = configuration.get('requests_per_month', 1000000)
            
            # First 1M requests at higher rate
            if requests <= 1000000:
                monthly_cost = (requests / 1000000) * pricing.get('cost_per_million_first_tier', 3.50)
            else:
                first_tier = 3.50
                remaining = ((requests - 1000000) / 1000000) * pricing.get('cost_per_million_next_tier', 3.00)
                monthly_cost = first_tier + remaining
            
            return monthly_cost
        
        else:
            # Default calculation
            units = configuration.get('units', 1)
            return base_cost + (unit_cost * units)

    
    def _initialize_pricing_catalog(self) -> Dict[str, Dict]:
        """
        Initialize AWS pricing catalog with mock data for MVP
        
        In production, this would use the AWS Pricing API for real-time pricing
        """
        return {
            'Amazon EC2': {
                'base_monthly_cost': 0.0,
                'unit_cost': 0.0,
                'pricing_model': 'Per hour',
                'instance_types': {
                    't3.micro': 0.0104,
                    't3.small': 0.0208,
                    't3.medium': 0.0416,
                    't3.large': 0.0832,
                    't3.xlarge': 0.1664,
                    't3.2xlarge': 0.3328,
                    'm5.large': 0.096,
                    'm5.xlarge': 0.192,
                    'm5.2xlarge': 0.384,
                    'c5.large': 0.085,
                    'c5.xlarge': 0.17,
                    'r5.large': 0.126,
                    'r5.xlarge': 0.252
                }
            },
            'Amazon RDS': {
                'base_monthly_cost': 0.0,
                'unit_cost': 0.0,
                'pricing_model': 'Per hour + storage',
                'instance_classes': {
                    'db.t3.micro': 0.017,
                    'db.t3.small': 0.034,
                    'db.t3.medium': 0.068,
                    'db.t3.large': 0.136,
                    'db.r5.large': 0.24,
                    'db.r5.xlarge': 0.48,
                    'db.m5.large': 0.192,
                    'db.m5.xlarge': 0.384
                },
                'storage_cost_per_gb': 0.115
            },
            'Amazon Aurora': {
                'base_monthly_cost': 0.0,
                'unit_cost': 0.0,
                'pricing_model': 'Per hour + storage + I/O',
                'instance_classes': {
                    'db.r5.large': 0.29,
                    'db.r5.xlarge': 0.58,
                    'db.r5.2xlarge': 1.16,
                    'db.r6g.large': 0.26,
                    'db.r6g.xlarge': 0.52
                },
                'storage_cost_per_gb': 0.10,
                'io_cost_per_million': 0.20
            },
            'Amazon DynamoDB': {
                'base_monthly_cost': 0.0,
                'unit_cost': 0.0,
                'pricing_model': 'On-Demand or Provisioned',
                'on_demand_read_per_million': 0.25,
                'on_demand_write_per_million': 1.25,
                'provisioned_read_per_hour': 0.00013,
                'provisioned_write_per_hour': 0.00065,
                'storage_cost_per_gb': 0.25
            },
            'Amazon S3': {
                'base_monthly_cost': 0.0,
                'unit_cost': 0.0,
                'pricing_model': 'Per GB + requests',
                'storage_classes': {
                    'S3 Standard': 0.023,
                    'S3 Intelligent-Tiering': 0.023,
                    'S3 Standard-IA': 0.0125,
                    'S3 One Zone-IA': 0.01,
                    'S3 Glacier Instant Retrieval': 0.004,
                    'S3 Glacier Flexible Retrieval': 0.0036,
                    'S3 Glacier Deep Archive': 0.00099
                },
                'request_cost_per_1000': 0.0004
            },
            'Amazon EBS': {
                'base_monthly_cost': 0.0,
                'unit_cost': 0.0,
                'pricing_model': 'Per GB-month',
                'volume_types': {
                    'gp2': 0.10,
                    'gp3': 0.08,
                    'io1': 0.125,
                    'io2': 0.125,
                    'st1': 0.045,
                    'sc1': 0.015
                }
            },
            'Amazon EFS': {
                'base_monthly_cost': 0.0,
                'unit_cost': 0.30,
                'pricing_model': 'Per GB-month',
                'storage_classes': {
                    'Standard': 0.30,
                    'Infrequent Access': 0.025
                }
            },
            'AWS Lambda': {
                'base_monthly_cost': 0.0,
                'unit_cost': 0.0,
                'pricing_model': 'Per request + compute',
                'request_cost_per_million': 0.20,
                'compute_cost_per_million_gb_seconds': 16.67
            },
            'AWS Elastic Beanstalk': {
                'base_monthly_cost': 0.0,
                'unit_cost': 0.0,
                'pricing_model': 'No additional charge (pay for underlying resources)',
                'note': 'Cost based on EC2, RDS, and other resources used'
            },
            'Application Load Balancer': {
                'base_monthly_cost': 0.0,
                'unit_cost': 0.0,
                'pricing_model': 'Per hour + LCU',
                'hourly_cost': 0.0225,
                'lcu_cost': 0.008
            },
            'Network Load Balancer': {
                'base_monthly_cost': 0.0,
                'unit_cost': 0.0,
                'pricing_model': 'Per hour + LCU',
                'hourly_cost': 0.0225,
                'lcu_cost': 0.006
            },
            'Amazon ElastiCache': {
                'base_monthly_cost': 0.0,
                'unit_cost': 0.0,
                'pricing_model': 'Per hour',
                'node_types': {
                    'cache.t3.micro': 0.017,
                    'cache.t3.small': 0.034,
                    'cache.t3.medium': 0.068,
                    'cache.r5.large': 0.188,
                    'cache.r5.xlarge': 0.376,
                    'cache.m5.large': 0.161,
                    'cache.m5.xlarge': 0.322
                }
            },
            'Amazon SQS': {
                'base_monthly_cost': 0.0,
                'unit_cost': 0.0,
                'pricing_model': 'Per million requests',
                'cost_per_million_requests': 0.40,
                'free_tier': 1000000
            },
            'Amazon SNS': {
                'base_monthly_cost': 0.0,
                'unit_cost': 0.0,
                'pricing_model': 'Per million requests',
                'cost_per_million_requests': 0.50,
                'free_tier': 1000000
            },
            'Amazon MSK': {
                'base_monthly_cost': 0.0,
                'unit_cost': 0.0,
                'pricing_model': 'Per broker hour + storage',
                'broker_types': {
                    'kafka.t3.small': 0.038,
                    'kafka.m5.large': 0.21,
                    'kafka.m5.xlarge': 0.42,
                    'kafka.m5.2xlarge': 0.84
                },
                'storage_cost_per_gb': 0.10
            },
            'Amazon API Gateway': {
                'base_monthly_cost': 0.0,
                'unit_cost': 0.0,
                'pricing_model': 'Per million requests',
                'cost_per_million_first_tier': 3.50,
                'cost_per_million_next_tier': 3.00
            }
        }


# Lambda-compatible handler functions for Bedrock Agent Action Groups

def lambda_handler(event, context):
    """
    Main Lambda handler for Cost Analysis Agent action groups
    
    This handler routes requests to appropriate action group functions
    based on the action specified in the event.
    
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
    """
    action = event.get('actionGroup', '')
    function = event.get('function', '')
    parameters = event.get('parameters', [])
    
    # Convert parameters list to dictionary
    params_dict = {}
    for param in parameters:
        params_dict[param['name']] = param['value']
    
    # Initialize analyzer
    region = params_dict.get('region', 'us-east-1')
    analyzer = CostAnalyzer(region=region)
    
    try:
        # Route to appropriate function
        if function == 'estimate_service_cost':
            result = estimate_service_cost_handler(params_dict, analyzer)
        elif function == 'calculate_total_cost':
            result = calculate_total_cost_handler(params_dict, analyzer)
        elif function == 'apply_anz_discounts':
            result = apply_anz_discounts_handler(params_dict, analyzer)
        elif function == 'identify_cost_optimizations':
            result = identify_cost_optimizations_handler(params_dict, analyzer)
        elif function == 'compare_costs':
            result = compare_costs_handler(params_dict, analyzer)
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


def estimate_service_cost_handler(params: Dict, analyzer: CostAnalyzer) -> Dict:
    """
    Handler for estimate_service_cost action
    
    Requirement 5.1: Estimate cost for individual AWS services
    """
    service = params.get('service', '')
    configuration = params.get('configuration', {})
    
    # Configuration can be passed as JSON string or dict
    if isinstance(configuration, str):
        try:
            configuration = json.loads(configuration)
        except json.JSONDecodeError:
            return {'error': 'Invalid configuration JSON format'}
    
    if not service:
        return {'error': 'Missing required parameter: service'}
    
    return analyzer.estimate_service_cost(service, configuration)


def calculate_total_cost_handler(params: Dict, analyzer: CostAnalyzer) -> Dict:
    """
    Handler for calculate_total_cost action
    
    Requirement 5.2: Calculate total monthly cost for architecture
    """
    architecture = params.get('architecture', {})
    
    # Architecture can be passed as JSON string or dict
    if isinstance(architecture, str):
        try:
            architecture = json.loads(architecture)
        except json.JSONDecodeError:
            return {'error': 'Invalid architecture JSON format'}
    
    if not architecture:
        return {'error': 'Missing required parameter: architecture'}
    
    return analyzer.calculate_total_cost(architecture)


def apply_anz_discounts_handler(params: Dict, analyzer: CostAnalyzer) -> Dict:
    """
    Handler for apply_anz_discounts action
    
    Requirement 5.4: Apply ANZ-specific pricing agreements and discounts
    """
    base_cost = params.get('base_cost', 0.0)
    
    # Convert string to float if needed
    if isinstance(base_cost, str):
        try:
            base_cost = float(base_cost)
        except ValueError:
            return {'error': 'Invalid base_cost format, must be a number'}
    
    if base_cost <= 0:
        return {'error': 'base_cost must be greater than 0'}
    
    return analyzer.apply_anz_discounts(base_cost)


def identify_cost_optimizations_handler(params: Dict, analyzer: CostAnalyzer) -> Dict:
    """
    Handler for identify_cost_optimizations action
    
    Requirement 5.3: Identify cost optimization opportunities
    """
    breakdown = params.get('breakdown', [])
    
    # Breakdown can be passed as JSON string or list
    if isinstance(breakdown, str):
        try:
            breakdown = json.loads(breakdown)
        except json.JSONDecodeError:
            return {'error': 'Invalid breakdown JSON format'}
    
    if not breakdown:
        return {'error': 'Missing required parameter: breakdown'}
    
    # Convert dictionaries to ServiceCost objects
    service_costs = []
    for item in breakdown:
        try:
            service_cost = ServiceCost(**item)
            service_costs.append(service_cost)
        except TypeError as e:
            return {'error': f'Invalid ServiceCost format: {str(e)}'}
    
    optimizations = analyzer.identify_cost_optimizations(service_costs)
    
    return {
        'optimizations': [opt.to_dict() for opt in optimizations],
        'count': len(optimizations),
        'total_potential_savings': round(sum(opt.potential_savings for opt in optimizations), 2)
    }


def compare_costs_handler(params: Dict, analyzer: CostAnalyzer) -> Dict:
    """
    Handler for compare_costs action
    
    Requirement 5.5: Compare on-premises costs with AWS costs
    """
    onprem_cost = params.get('onprem_cost', 0.0)
    aws_cost = params.get('aws_cost', 0.0)
    
    # Convert strings to float if needed
    if isinstance(onprem_cost, str):
        try:
            onprem_cost = float(onprem_cost)
        except ValueError:
            return {'error': 'Invalid onprem_cost format, must be a number'}
    
    if isinstance(aws_cost, str):
        try:
            aws_cost = float(aws_cost)
        except ValueError:
            return {'error': 'Invalid aws_cost format, must be a number'}
    
    if onprem_cost < 0 or aws_cost < 0:
        return {'error': 'Costs must be non-negative'}
    
    return analyzer.compare_costs(onprem_cost, aws_cost)
