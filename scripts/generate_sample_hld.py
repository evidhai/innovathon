#!/usr/bin/env python3
"""
Generate sample High-Level Design (HLD) PDF for a 3-tier e-commerce application.
This document will be used for testing the Design Analyzer Agent.
"""

import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image
from reportlab.lib import colors
from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.compute import Server
from diagrams.onprem.network import Nginx
from diagrams.onprem.database import PostgreSQL
from diagrams.onprem.inmemory import Redis


def generate_architecture_diagram(output_path: str):
    """Generate architecture diagram for the e-commerce application."""
    diagram_path = output_path.replace('.pdf', '_diagram')
    
    with Diagram("E-Commerce Application Architecture", 
                 filename=diagram_path,
                 show=False,
                 direction="TB"):
        
        with Cluster("Presentation Tier"):
            lb = Nginx("Load Balancer\n2x Nginx")
            web_servers = [
                Server("Web Server 1\nApache Tomcat"),
                Server("Web Server 2\nApache Tomcat"),
                Server("Web Server 3\nApache Tomcat")
            ]
        
        with Cluster("Application Tier"):
            app_servers = [
                Server("App Server 1\nJava Spring Boot"),
                Server("App Server 2\nJava Spring Boot"),
                Server("App Server 3\nJava Spring Boot"),
                Server("App Server 4\nJava Spring Boot"),
                Server("App Server 5\nJava Spring Boot")
            ]
            cache = Redis("Redis Cache\n16GB")
        
        with Cluster("Data Tier"):
            db_primary = PostgreSQL("PostgreSQL Primary\n500GB")
            db_replica = PostgreSQL("PostgreSQL Replica\n500GB")
        
        # Define connections
        lb >> Edge(label="HTTPS") >> web_servers
        web_servers >> Edge(label="HTTP") >> app_servers
        app_servers >> Edge(label="Cache") >> cache
        app_servers >> Edge(label="SQL") >> db_primary
        db_primary >> Edge(label="Replication") >> db_replica
    
    return f"{diagram_path}.png"


def create_hld_pdf(output_path: str):
    """Create the HLD PDF document."""
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Generate architecture diagram
    diagram_path = generate_architecture_diagram(output_path)
    
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
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    heading_style = styles['Heading2']
    normal_style = styles['BodyText']
    normal_style.alignment = TA_JUSTIFY
    
    # Title
    title = Paragraph("High-Level Design Document", title_style)
    elements.append(title)
    
    subtitle = Paragraph("E-Commerce Application Platform", styles['Heading3'])
    elements.append(subtitle)
    elements.append(Spacer(1, 12))
    
    # Document metadata
    metadata = [
        ['Document Version:', '1.0'],
        ['Date:', datetime.now().strftime('%B %d, %Y')],
        ['Author:', 'Enterprise Architecture Team'],
        ['Status:', 'Final']
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
    
    # Executive Summary
    elements.append(Paragraph("1. Executive Summary", heading_style))
    elements.append(Spacer(1, 12))
    
    exec_summary = """
    This document describes the high-level architecture for the ShopNow e-commerce platform, 
    a mission-critical application serving over 500,000 daily active users. The platform 
    processes approximately 10,000 transactions per day with peak loads reaching 2,000 
    concurrent users during promotional events. The current on-premises infrastructure consists 
    of a traditional 3-tier architecture deployed across two data centers for high availability.
    """
    elements.append(Paragraph(exec_summary, normal_style))
    elements.append(Spacer(1, 20))
    
    # System Overview
    elements.append(Paragraph("2. System Overview", heading_style))
    elements.append(Spacer(1, 12))
    
    overview = """
    The ShopNow platform is a comprehensive e-commerce solution that enables customers to browse 
    products, manage shopping carts, process payments, and track orders. The system integrates 
    with multiple third-party services including payment gateways (Stripe, PayPal), shipping 
    providers (FedEx, UPS), and inventory management systems.
    """
    elements.append(Paragraph(overview, normal_style))
    elements.append(Spacer(1, 20))
    
    # Architecture Overview
    elements.append(Paragraph("3. Architecture Overview", heading_style))
    elements.append(Spacer(1, 12))
    
    arch_overview = """
    The application follows a classic 3-tier architecture pattern consisting of presentation, 
    application, and data tiers. This separation of concerns provides modularity, scalability, 
    and maintainability. Each tier can be scaled independently based on demand.
    """
    elements.append(Paragraph(arch_overview, normal_style))
    elements.append(Spacer(1, 20))
    
    # Add architecture diagram
    if os.path.exists(diagram_path):
        img = Image(diagram_path, width=6*inch, height=4*inch)
        elements.append(img)
        elements.append(Spacer(1, 12))
        elements.append(Paragraph("<i>Figure 1: E-Commerce Application Architecture</i>", 
                                 ParagraphStyle('Caption', parent=normal_style, 
                                              fontSize=9, textColor=colors.grey)))
    
    elements.append(PageBreak())
    
    # Component Details
    elements.append(Paragraph("4. Component Details", heading_style))
    elements.append(Spacer(1, 12))
    
    # Presentation Tier
    elements.append(Paragraph("4.1 Presentation Tier", styles['Heading3']))
    elements.append(Spacer(1, 12))
    
    pres_tier = """
    The presentation tier handles all user-facing interactions and consists of load balancers 
    and web servers. The load balancers distribute incoming HTTPS traffic across multiple web 
    servers to ensure high availability and optimal performance.
    """
    elements.append(Paragraph(pres_tier, normal_style))
    elements.append(Spacer(1, 12))
    
    # Component table for Presentation Tier
    pres_components = [
        ['Component', 'Technology', 'Quantity', 'Specifications'],
        ['Load Balancer', 'Nginx 1.20', '2', '4 CPU cores, 8GB RAM, Active-Passive'],
        ['Web Server', 'Apache Tomcat 9.0', '3', '8 CPU cores, 16GB RAM, 100GB SSD']
    ]
    t = Table(pres_components, colWidths=[1.5*inch, 1.5*inch, 1*inch, 2.5*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
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
    
    # Application Tier
    elements.append(Paragraph("4.2 Application Tier", styles['Heading3']))
    elements.append(Spacer(1, 12))
    
    app_tier = """
    The application tier contains the business logic and processes all transactions. It consists 
    of multiple Java Spring Boot application servers that handle order processing, inventory 
    management, user authentication, and payment processing. A Redis cache layer reduces database 
    load by caching frequently accessed data such as product catalogs and user sessions.
    """
    elements.append(Paragraph(app_tier, normal_style))
    elements.append(Spacer(1, 12))
    
    # Component table for Application Tier
    app_components = [
        ['Component', 'Technology', 'Quantity', 'Specifications'],
        ['Application Server', 'Java Spring Boot 2.7', '5', '16 CPU cores, 32GB RAM, 200GB SSD'],
        ['Cache Server', 'Redis 6.2', '1', '8 CPU cores, 16GB RAM, In-Memory']
    ]
    t = Table(app_components, colWidths=[1.5*inch, 1.5*inch, 1*inch, 2.5*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
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
    
    # Data Tier
    elements.append(Paragraph("4.3 Data Tier", styles['Heading3']))
    elements.append(Spacer(1, 12))
    
    data_tier = """
    The data tier manages all persistent data storage using PostgreSQL databases. The primary 
    database handles all write operations and real-time reads, while a read replica serves 
    reporting queries and provides disaster recovery capabilities. The database stores customer 
    information, product catalogs, order history, and transaction records.
    """
    elements.append(Paragraph(data_tier, normal_style))
    elements.append(Spacer(1, 12))
    
    # Component table for Data Tier
    data_components = [
        ['Component', 'Technology', 'Quantity', 'Specifications'],
        ['Primary Database', 'PostgreSQL 13', '1', '32 CPU cores, 128GB RAM, 500GB SSD'],
        ['Read Replica', 'PostgreSQL 13', '1', '32 CPU cores, 128GB RAM, 500GB SSD']
    ]
    t = Table(data_components, colWidths=[1.5*inch, 1.5*inch, 1*inch, 2.5*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
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
    
    # Dependencies and Integration Points
    elements.append(Paragraph("5. Dependencies and Integration Points", heading_style))
    elements.append(Spacer(1, 12))
    
    dependencies = """
    The e-commerce platform integrates with multiple external systems and services to provide 
    complete functionality. These integrations are critical for payment processing, shipping, 
    and inventory management.
    """
    elements.append(Paragraph(dependencies, normal_style))
    elements.append(Spacer(1, 12))
    
    # Integration table
    integrations = [
        ['Integration', 'Purpose', 'Protocol', 'Dependency Level'],
        ['Stripe API', 'Payment Processing', 'REST/HTTPS', 'Critical'],
        ['PayPal API', 'Alternative Payment', 'REST/HTTPS', 'High'],
        ['FedEx API', 'Shipping Tracking', 'REST/HTTPS', 'Medium'],
        ['UPS API', 'Shipping Tracking', 'REST/HTTPS', 'Medium'],
        ['Inventory System', 'Stock Management', 'SOAP/HTTPS', 'Critical'],
        ['Email Service', 'Notifications', 'SMTP', 'Medium']
    ]
    t = Table(integrations, colWidths=[1.5*inch, 1.8*inch, 1.2*inch, 1.5*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
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
    
    # Performance Requirements
    elements.append(Paragraph("6. Performance Requirements", heading_style))
    elements.append(Spacer(1, 12))
    
    performance = [
        ['Metric', 'Target', 'Current Performance'],
        ['Page Load Time', '< 2 seconds', '1.8 seconds'],
        ['Transaction Processing', '< 3 seconds', '2.5 seconds'],
        ['Concurrent Users', '2,000', '2,000'],
        ['Daily Transactions', '10,000', '8,500'],
        ['Database Query Time', '< 100ms', '85ms'],
        ['System Uptime', '99.9%', '99.7%']
    ]
    t = Table(performance, colWidths=[2*inch, 2*inch, 2*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
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
    
    # Security Considerations
    elements.append(Paragraph("7. Security Considerations", heading_style))
    elements.append(Spacer(1, 12))
    
    security = """
    The platform implements multiple layers of security including SSL/TLS encryption for all 
    data in transit, encrypted storage for sensitive customer data, role-based access control 
    (RBAC) for administrative functions, and PCI-DSS compliance for payment card processing. 
    Regular security audits and penetration testing are conducted quarterly.
    """
    elements.append(Paragraph(security, normal_style))
    elements.append(Spacer(1, 20))
    
    # Disaster Recovery
    elements.append(Paragraph("8. Disaster Recovery", heading_style))
    elements.append(Spacer(1, 12))
    
    dr = """
    The system maintains a Recovery Time Objective (RTO) of 4 hours and Recovery Point Objective 
    (RPO) of 1 hour. Daily backups are performed for all databases and stored in a secondary 
    data center. The read replica can be promoted to primary in case of primary database failure.
    """
    elements.append(Paragraph(dr, normal_style))
    
    # Build PDF
    doc.build(elements)
    print(f"HLD PDF generated successfully: {output_path}")
    
    return output_path


if __name__ == "__main__":
    output_dir = "sample_documents"
    output_file = os.path.join(output_dir, "ecommerce_hld.pdf")
    create_hld_pdf(output_file)
