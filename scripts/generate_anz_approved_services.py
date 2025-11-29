#!/usr/bin/env python3
"""
Generate sample ANZ Approved AWS Services List PDF.
This document will be used for testing the Knowledge Base and Service Advisor Agent.
"""

import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors


def create_anz_approved_services_pdf(output_path: str):
    """Create the ANZ Approved AWS Services List PDF document."""
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
    title = Paragraph("ANZ Approved AWS Services", title_style)
    elements.append(title)
    
    subtitle = Paragraph("Cloud Service Catalog and Usage Guidelines", styles['Heading3'])
    elements.append(subtitle)
    elements.append(Spacer(1, 12))
    
    # Document metadata
    metadata = [
        ['Document Version:', '3.2'],
        ['Date:', datetime.now().strftime('%B %d, %Y')],
        ['Classification:', 'Internal Use Only'],
        ['Owner:', 'ANZ Cloud Governance Team'],
        ['Review Cycle:', 'Quarterly']
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
    This document provides the official list of AWS services approved for use within ANZ. 
    Services are categorized by approval status: Approved, Conditional, and Restricted. 
    All cloud deployments must use services from the Approved or Conditional categories. 
    Use of Restricted services requires explicit approval from the Cloud Security team.
    """
    elements.append(Paragraph(intro, normal_style))
    elements.append(Spacer(1, 20))
    
    # Service Categories
    elements.append(Paragraph("2. Service Approval Categories", heading_style))
    elements.append(Spacer(1, 12))
    
    categories_desc = """
    <b>Approved:</b> Services that have completed security review and are approved for 
    general use in production environments.<br/><br/>
    <b>Conditional:</b> Services approved with specific conditions or restrictions. 
    Review conditions before use.<br/><br/>
    <b>Restricted:</b> Services not approved for general use. Requires security review 
    and CARB approval.
    """
    elements.append(Paragraph(categories_desc, normal_style))
    elements.append(Spacer(1, 20))
    
    # Compute Services
    elements.append(Paragraph("3. Compute Services", heading_style))
    elements.append(Spacer(1, 12))
    
    compute_services = [
        ['Service', 'Status', 'Use Case', 'Notes'],
        ['Amazon EC2', 'Approved', 'Virtual servers', 'Use approved AMIs only'],
        ['AWS Lambda', 'Approved', 'Serverless compute', 'Max 15-min timeout'],
        ['Amazon ECS', 'Approved', 'Container orchestration', 'Fargate preferred'],
        ['Amazon EKS', 'Conditional', 'Kubernetes', 'Requires container security'],
        ['AWS Batch', 'Approved', 'Batch processing', 'For HPC workloads'],
        ['AWS Elastic Beanstalk', 'Approved', 'PaaS deployment', 'Managed platform'],
        ['AWS App Runner', 'Conditional', 'Container apps', 'Under evaluation'],
    ]
    t = Table(compute_services, colWidths=[1.5*inch, 1*inch, 1.5*inch, 2*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 20))
    
    # Storage Services
    elements.append(Paragraph("4. Storage Services", heading_style))
    elements.append(Spacer(1, 12))
    
    storage_services = [
        ['Service', 'Status', 'Use Case', 'Notes'],
        ['Amazon S3', 'Approved', 'Object storage', 'Encryption mandatory'],
        ['Amazon EBS', 'Approved', 'Block storage', 'Encryption mandatory'],
        ['Amazon EFS', 'Approved', 'File storage', 'For shared file systems'],
        ['AWS Storage Gateway', 'Approved', 'Hybrid storage', 'On-prem integration'],
        ['Amazon FSx', 'Conditional', 'Managed file systems', 'Windows/Lustre only'],
        ['AWS Backup', 'Approved', 'Backup management', 'Preferred backup solution'],
    ]
    t = Table(storage_services, colWidths=[1.5*inch, 1*inch, 1.5*inch, 2*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 20))
    
    elements.append(PageBreak())
    
    # Database Services
    elements.append(Paragraph("5. Database Services", heading_style))
    elements.append(Spacer(1, 12))
    
    database_services = [
        ['Service', 'Status', 'Use Case', 'Notes'],
        ['Amazon RDS', 'Approved', 'Relational databases', 'PostgreSQL, MySQL, Oracle'],
        ['Amazon Aurora', 'Approved', 'High-perf relational', 'Preferred for new apps'],
        ['Amazon DynamoDB', 'Approved', 'NoSQL database', 'For key-value workloads'],
        ['Amazon ElastiCache', 'Approved', 'In-memory cache', 'Redis preferred'],
        ['Amazon DocumentDB', 'Conditional', 'MongoDB compatible', 'Requires justification'],
        ['Amazon Neptune', 'Conditional', 'Graph database', 'Specific use cases only'],
        ['Amazon Redshift', 'Approved', 'Data warehouse', 'For analytics workloads'],
        ['Amazon Timestream', 'Conditional', 'Time-series data', 'Under evaluation'],
    ]
    t = Table(database_services, colWidths=[1.5*inch, 1*inch, 1.5*inch, 2*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 20))
    
    # Networking Services
    elements.append(Paragraph("6. Networking and Content Delivery", heading_style))
    elements.append(Spacer(1, 12))
    
    networking_services = [
        ['Service', 'Status', 'Use Case', 'Notes'],
        ['Amazon VPC', 'Approved', 'Virtual network', 'Follow VPC standards'],
        ['AWS Transit Gateway', 'Approved', 'Network hub', 'Mandatory for multi-VPC'],
        ['AWS Direct Connect', 'Approved', 'Dedicated connection', 'For hybrid cloud'],
        ['Amazon Route 53', 'Approved', 'DNS service', 'Use ANZ hosted zones'],
        ['Elastic Load Balancing', 'Approved', 'Load balancing', 'ALB/NLB approved'],
        ['Amazon CloudFront', 'Approved', 'CDN', 'For public content only'],
        ['AWS Global Accelerator', 'Conditional', 'Network optimization', 'Specific use cases'],
        ['AWS VPN', 'Approved', 'VPN connectivity', 'For remote access'],
    ]
    t = Table(networking_services, colWidths=[1.5*inch, 1*inch, 1.5*inch, 2*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 20))
    
    # Security Services
    elements.append(Paragraph("7. Security, Identity, and Compliance", heading_style))
    elements.append(Spacer(1, 12))
    
    security_services = [
        ['Service', 'Status', 'Use Case', 'Notes'],
        ['AWS IAM', 'Approved', 'Access management', 'MFA mandatory'],
        ['AWS KMS', 'Approved', 'Key management', 'For encryption keys'],
        ['AWS Secrets Manager', 'Approved', 'Secrets storage', 'Preferred over hardcoding'],
        ['AWS Certificate Manager', 'Approved', 'SSL/TLS certificates', 'For public certs'],
        ['Amazon GuardDuty', 'Approved', 'Threat detection', 'Mandatory for prod'],
        ['AWS Security Hub', 'Approved', 'Security posture', 'Centralized security'],
        ['AWS WAF', 'Approved', 'Web firewall', 'For public-facing apps'],
        ['AWS Shield', 'Approved', 'DDoS protection', 'Standard included'],
        ['Amazon Macie', 'Conditional', 'Data discovery', 'For sensitive data'],
    ]
    t = Table(security_services, colWidths=[1.5*inch, 1*inch, 1.5*inch, 2*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 20))
    
    elements.append(PageBreak())
    
    # Management and Governance
    elements.append(Paragraph("8. Management and Governance", heading_style))
    elements.append(Spacer(1, 12))
    
    management_services = [
        ['Service', 'Status', 'Use Case', 'Notes'],
        ['AWS CloudWatch', 'Approved', 'Monitoring', 'Mandatory for all resources'],
        ['AWS CloudTrail', 'Approved', 'Audit logging', 'Mandatory for compliance'],
        ['AWS Config', 'Approved', 'Resource tracking', 'For compliance monitoring'],
        ['AWS Systems Manager', 'Approved', 'Operations management', 'For patch management'],
        ['AWS CloudFormation', 'Approved', 'Infrastructure as Code', 'Preferred IaC tool'],
        ['AWS Service Catalog', 'Approved', 'Service catalog', 'For standardized deploys'],
        ['AWS Organizations', 'Approved', 'Account management', 'Multi-account strategy'],
        ['AWS Control Tower', 'Approved', 'Landing zone', 'For new accounts'],
    ]
    t = Table(management_services, colWidths=[1.5*inch, 1*inch, 1.5*inch, 2*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 20))
    
    # Analytics and Machine Learning
    elements.append(Paragraph("9. Analytics and Machine Learning", heading_style))
    elements.append(Spacer(1, 12))
    
    analytics_services = [
        ['Service', 'Status', 'Use Case', 'Notes'],
        ['Amazon Athena', 'Approved', 'Query S3 data', 'For ad-hoc queries'],
        ['AWS Glue', 'Approved', 'ETL service', 'For data pipelines'],
        ['Amazon EMR', 'Approved', 'Big data processing', 'For Hadoop/Spark'],
        ['Amazon Kinesis', 'Approved', 'Streaming data', 'For real-time analytics'],
        ['Amazon SageMaker', 'Conditional', 'Machine learning', 'Requires ML expertise'],
        ['Amazon Bedrock', 'Conditional', 'Generative AI', 'Under evaluation'],
        ['Amazon QuickSight', 'Approved', 'Business intelligence', 'For dashboards'],
    ]
    t = Table(analytics_services, colWidths=[1.5*inch, 1*inch, 1.5*inch, 2*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 20))
    
    # Application Integration
    elements.append(Paragraph("10. Application Integration", heading_style))
    elements.append(Spacer(1, 12))
    
    integration_services = [
        ['Service', 'Status', 'Use Case', 'Notes'],
        ['Amazon SQS', 'Approved', 'Message queuing', 'For async processing'],
        ['Amazon SNS', 'Approved', 'Pub/sub messaging', 'For notifications'],
        ['Amazon EventBridge', 'Approved', 'Event bus', 'For event-driven arch'],
        ['AWS Step Functions', 'Approved', 'Workflow orchestration', 'For complex workflows'],
        ['Amazon API Gateway', 'Approved', 'API management', 'For REST/WebSocket APIs'],
        ['AWS AppSync', 'Conditional', 'GraphQL API', 'Requires justification'],
    ]
    t = Table(integration_services, colWidths=[1.5*inch, 1*inch, 1.5*inch, 2*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 20))
    
    # Service Request Process
    elements.append(Paragraph("11. New Service Request Process", heading_style))
    elements.append(Spacer(1, 12))
    
    request_process = """
    To request approval for a service not on this list or to request an exception for a 
    Restricted service, submit a Service Request Form to the Cloud Governance team. Include 
    business justification, security considerations, and cost analysis. Requests are reviewed 
    within 10 business days.
    """
    elements.append(Paragraph(request_process, normal_style))
    elements.append(Spacer(1, 20))
    
    # Review and Updates
    elements.append(Paragraph("12. Document Review and Updates", heading_style))
    elements.append(Spacer(1, 12))
    
    review = """
    This document is reviewed quarterly and updated as new AWS services are evaluated and 
    approved. Check the ANZ Cloud Portal for the latest version. Questions should be directed 
    to cloudgovernance@anz.com.
    """
    elements.append(Paragraph(review, normal_style))
    
    # Build PDF
    doc.build(elements)
    print(f"ANZ Approved Services PDF generated successfully: {output_path}")
    
    return output_path


if __name__ == "__main__":
    output_dir = "sample_documents/anz"
    output_file = os.path.join(output_dir, "anz_approved_aws_services.pdf")
    create_anz_approved_services_pdf(output_file)
