#!/usr/bin/env python3
"""
Generate sample ANZ VPC Configuration Standards PDF.
This document will be used for testing the Knowledge Base and User Interaction Agent.
"""

import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors


def create_anz_vpc_standards_pdf(output_path: str):
    """Create the ANZ VPC Configuration Standards PDF document."""
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Create PDF
    doc = SimpleDocTemplate(output_path, pagesize=letter,
                           rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=18)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#003366'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        textColor=colors.HexColor('#003366')
    )
    normal_style = styles['BodyText']
    normal_style.alignment = TA_JUSTIFY
    
    # Title
    title = Paragraph("ANZ VPC Configuration Standards", title_style)
    elements.append(title)
    
    subtitle = Paragraph("AWS Cloud Infrastructure Guidelines", styles['Heading3'])
    elements.append(subtitle)
    elements.append(Spacer(1, 12))
    
    # Document metadata
    metadata = [
        ['Document Version:', '2.1'],
        ['Date:', datetime.now().strftime('%B %d, %Y')],
        ['Classification:', 'Internal Use Only'],
        ['Owner:', 'ANZ Cloud Architecture Team'],
        ['Status:', 'Approved']
    ]
    t = Table(metadata, colWidths=[2*inch, 4*inch])
    t.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 30))
    
    # Introduction
    elements.append(Paragraph("1. Introduction", heading_style))
    elements.append(Spacer(1, 12))
    
    intro = """
    This document defines the standard VPC (Virtual Private Cloud) configuration requirements 
    for all AWS deployments within ANZ. These standards ensure consistency, security, and 
    compliance across all cloud infrastructure. All migration projects must adhere to these 
    guidelines unless explicitly approved by the Cloud Architecture Review Board.
    """
    elements.append(Paragraph(intro, normal_style))
    elements.append(Spacer(1, 20))
    
    # Standard VPC Architecture
    elements.append(Paragraph("2. Standard VPC Architecture", heading_style))
    elements.append(Spacer(1, 12))
    
    vpc_arch = """
    ANZ requires a multi-tier VPC architecture with clear separation between public, private, 
    and data subnets. All production workloads must be deployed across at least two Availability 
    Zones for high availability. The standard architecture includes dedicated subnets for 
    application tiers, databases, and management functions.
    """
    elements.append(Paragraph(vpc_arch, normal_style))
    elements.append(Spacer(1, 20))
    
    # VPC Configuration Requirements
    elements.append(Paragraph("3. VPC Configuration Requirements", heading_style))
    elements.append(Spacer(1, 12))
    
    # VPC Requirements Table
    vpc_requirements = [
        ['Requirement', 'Standard', 'Rationale'],
        ['VPC CIDR Block', '/16 (65,536 IPs)', 'Sufficient IP space for growth'],
        ['Availability Zones', 'Minimum 2 AZs', 'High availability and fault tolerance'],
        ['Public Subnets', '/24 per AZ', 'Load balancers and NAT gateways'],
        ['Private Subnets', '/20 per AZ', 'Application servers and services'],
        ['Data Subnets', '/22 per AZ', 'Databases and data stores'],
        ['Management Subnets', '/24 per AZ', 'Bastion hosts and admin tools'],
    ]
    t = Table(vpc_requirements, colWidths=[1.8*inch, 1.8*inch, 2.4*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 20))
    
    # IP Address Allocation
    elements.append(Paragraph("4. IP Address Allocation", heading_style))
    elements.append(Spacer(1, 12))
    
    ip_allocation = """
    ANZ maintains a centralized IP address management system. All VPC CIDR blocks must be 
    requested through the Cloud Infrastructure team to avoid conflicts with existing networks 
    and to ensure proper routing for hybrid cloud connectivity.
    """
    elements.append(Paragraph(ip_allocation, normal_style))
    elements.append(Spacer(1, 12))
    
    # Standard CIDR Ranges
    cidr_ranges = [
        ['Environment', 'CIDR Range', 'Purpose'],
        ['Production', '10.100.0.0/16 - 10.109.0.0/16', 'Production workloads'],
        ['Non-Production', '10.110.0.0/16 - 10.119.0.0/16', 'Dev, Test, UAT environments'],
        ['Shared Services', '10.120.0.0/16 - 10.124.0.0/16', 'Shared infrastructure'],
        ['Management', '10.125.0.0/16 - 10.127.0.0/16', 'Admin and monitoring'],
    ]
    t = Table(cidr_ranges, colWidths=[1.5*inch, 2.5*inch, 2*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 20))
    
    elements.append(PageBreak())
    
    # Network Security
    elements.append(Paragraph("5. Network Security Requirements", heading_style))
    elements.append(Spacer(1, 12))
    
    security_intro = """
    Network security is paramount in all ANZ cloud deployments. The following security 
    controls must be implemented in every VPC configuration.
    """
    elements.append(Paragraph(security_intro, normal_style))
    elements.append(Spacer(1, 12))
    
    # Security Requirements
    security_requirements = [
        ['Control', 'Requirement', 'Implementation'],
        ['Network ACLs', 'Mandatory', 'Default deny, explicit allow rules'],
        ['Security Groups', 'Mandatory', 'Least privilege, no 0.0.0.0/0 inbound'],
        ['Flow Logs', 'Mandatory', 'Enabled for all VPCs, 7-day retention'],
        ['NAT Gateways', 'Mandatory', 'One per AZ for high availability'],
        ['Internet Gateway', 'Conditional', 'Only for public subnets'],
        ['VPC Endpoints', 'Recommended', 'For AWS services (S3, DynamoDB)'],
    ]
    t = Table(security_requirements, colWidths=[1.5*inch, 1.5*inch, 3*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 20))
    
    # Connectivity Requirements
    elements.append(Paragraph("6. Connectivity Requirements", heading_style))
    elements.append(Spacer(1, 12))
    
    connectivity = """
    All VPCs must be connected to the ANZ corporate network through AWS Transit Gateway. 
    This provides centralized routing and simplifies network management. Direct Connect 
    connections are available for high-bandwidth, low-latency requirements.
    """
    elements.append(Paragraph(connectivity, normal_style))
    elements.append(Spacer(1, 12))
    
    # Connectivity Options
    connectivity_options = [
        ['Connection Type', 'Use Case', 'Bandwidth', 'Latency'],
        ['Transit Gateway', 'Standard connectivity', 'Up to 50 Gbps', '< 5ms'],
        ['Direct Connect', 'High-bandwidth workloads', '1-100 Gbps', '< 2ms'],
        ['VPN', 'Backup/temporary', 'Up to 1.25 Gbps', '< 20ms'],
        ['VPC Peering', 'VPC-to-VPC (same region)', 'No limit', '< 1ms'],
    ]
    t = Table(connectivity_options, colWidths=[1.5*inch, 2*inch, 1.3*inch, 1.2*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 20))
    
    # Naming Conventions
    elements.append(Paragraph("7. Naming Conventions", heading_style))
    elements.append(Spacer(1, 12))
    
    naming = """
    Consistent naming conventions are essential for managing cloud resources at scale. 
    All VPC resources must follow the ANZ naming standard.
    """
    elements.append(Paragraph(naming, normal_style))
    elements.append(Spacer(1, 12))
    
    # Naming Standards
    naming_standards = [
        ['Resource Type', 'Naming Pattern', 'Example'],
        ['VPC', 'anz-{env}-{region}-{app}-vpc', 'anz-prod-apse2-ecom-vpc'],
        ['Subnet', 'anz-{env}-{tier}-{az}-sn', 'anz-prod-app-2a-sn'],
        ['Route Table', 'anz-{env}-{tier}-rt', 'anz-prod-private-rt'],
        ['Security Group', 'anz-{env}-{app}-{function}-sg', 'anz-prod-ecom-web-sg'],
        ['NAT Gateway', 'anz-{env}-{az}-nat', 'anz-prod-2a-nat'],
        ['Internet Gateway', 'anz-{env}-{app}-igw', 'anz-prod-ecom-igw'],
    ]
    t = Table(naming_standards, colWidths=[1.5*inch, 2.3*inch, 2.2*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 20))
    
    elements.append(PageBreak())
    
    # Tagging Requirements
    elements.append(Paragraph("8. Tagging Requirements", heading_style))
    elements.append(Spacer(1, 12))
    
    tagging_intro = """
    All VPC resources must be tagged according to ANZ tagging standards. Tags enable 
    cost allocation, resource management, and compliance reporting.
    """
    elements.append(Paragraph(tagging_intro, normal_style))
    elements.append(Spacer(1, 12))
    
    # Required Tags
    required_tags = [
        ['Tag Key', 'Description', 'Example Value', 'Required'],
        ['Environment', 'Deployment environment', 'Production', 'Yes'],
        ['Application', 'Application name', 'E-Commerce', 'Yes'],
        ['CostCenter', 'Cost allocation code', 'CC-12345', 'Yes'],
        ['Owner', 'Technical owner email', 'team@anz.com', 'Yes'],
        ['Compliance', 'Compliance requirements', 'PCI-DSS', 'Conditional'],
        ['DataClassification', 'Data sensitivity', 'Confidential', 'Yes'],
        ['BackupPolicy', 'Backup requirements', 'Daily', 'Conditional'],
    ]
    t = Table(required_tags, colWidths=[1.5*inch, 1.8*inch, 1.5*inch, 1.2*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 20))
    
    # Monitoring and Logging
    elements.append(Paragraph("9. Monitoring and Logging", heading_style))
    elements.append(Spacer(1, 12))
    
    monitoring = """
    All VPCs must have comprehensive monitoring and logging enabled. VPC Flow Logs must 
    be sent to a centralized logging account for security analysis and compliance auditing. 
    CloudWatch alarms must be configured for critical network events.
    """
    elements.append(Paragraph(monitoring, normal_style))
    elements.append(Spacer(1, 12))
    
    # Monitoring Requirements
    monitoring_requirements = [
        ['Monitoring Type', 'Requirement', 'Retention'],
        ['VPC Flow Logs', 'All traffic, all VPCs', '90 days'],
        ['CloudWatch Metrics', 'NAT Gateway, VPN, TGW', '15 months'],
        ['CloudTrail', 'All API calls', '7 years'],
        ['GuardDuty', 'Threat detection', 'Real-time'],
    ]
    t = Table(monitoring_requirements, colWidths=[2*inch, 2.5*inch, 1.5*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 20))
    
    # Compliance and Governance
    elements.append(Paragraph("10. Compliance and Governance", heading_style))
    elements.append(Spacer(1, 12))
    
    compliance = """
    All VPC configurations must comply with ANZ security policies and relevant regulatory 
    requirements. Regular audits are conducted to ensure ongoing compliance. Any deviations 
    from these standards require formal approval from the Cloud Architecture Review Board.
    """
    elements.append(Paragraph(compliance, normal_style))
    elements.append(Spacer(1, 20))
    
    # Approval Process
    elements.append(Paragraph("11. Exception and Approval Process", heading_style))
    elements.append(Spacer(1, 12))
    
    approval = """
    Requests for exceptions to these standards must be submitted through the Cloud 
    Architecture Review Board (CARB) with detailed justification. All exceptions are 
    reviewed quarterly and may be revoked if circumstances change.
    """
    elements.append(Paragraph(approval, normal_style))
    
    # Build PDF
    doc.build(elements)
    print(f"ANZ VPC Standards PDF generated successfully: {output_path}")
    
    return output_path


if __name__ == "__main__":
    output_dir = "sample_documents/anz"
    output_file = os.path.join(output_dir, "anz_vpc_configuration_standards.pdf")
    create_anz_vpc_standards_pdf(output_file)
