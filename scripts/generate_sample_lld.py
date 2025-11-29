#!/usr/bin/env python3
"""
Generate sample Low-Level Design (LLD) PDF for a 3-tier e-commerce application.
This document provides detailed technical specifications for each component.
"""

import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors


def create_lld_pdf(output_path: str):
    """Create the LLD PDF document."""
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
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    heading_style = styles['Heading2']
    subheading_style = styles['Heading3']
    normal_style = styles['BodyText']
    normal_style.alignment = TA_JUSTIFY
    code_style = ParagraphStyle(
        'Code',
        parent=styles['Code'],
        fontSize=8,
        leftIndent=20,
        fontName='Courier'
    )
    
    # Title
    title = Paragraph("Low-Level Design Document", title_style)
    elements.append(title)
    
    subtitle = Paragraph("E-Commerce Application Platform - Technical Specifications", styles['Heading3'])
    elements.append(subtitle)
    elements.append(Spacer(1, 12))
    
    # Document metadata
    metadata = [
        ['Document Version:', '1.0'],
        ['Date:', datetime.now().strftime('%B %d, %Y')],
        ['Author:', 'Technical Architecture Team'],
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
    
    # Introduction
    elements.append(Paragraph("1. Introduction", heading_style))
    elements.append(Spacer(1, 12))
    
    intro = """
    This Low-Level Design document provides detailed technical specifications for the ShopNow 
    e-commerce platform. It includes component-level details, API specifications, database schemas, 
    deployment configurations, and operational procedures. This document is intended for developers, 
    system administrators, and DevOps engineers.
    """
    elements.append(Paragraph(intro, normal_style))
    elements.append(Spacer(1, 20))
    
    # Load Balancer Details
    elements.append(Paragraph("2. Load Balancer Configuration", heading_style))
    elements.append(Spacer(1, 12))
    
    elements.append(Paragraph("2.1 Technical Specifications", subheading_style))
    elements.append(Spacer(1, 12))
    
    lb_specs = [
        ['Parameter', 'Value'],
        ['Software', 'Nginx 1.20.2'],
        ['Operating System', 'Ubuntu 20.04 LTS'],
        ['CPU', '4 cores @ 2.5 GHz'],
        ['Memory', '8 GB RAM'],
        ['Network', '10 Gbps'],
        ['Configuration Mode', 'Active-Passive'],
        ['Health Check Interval', '5 seconds'],
        ['Connection Timeout', '60 seconds'],
        ['Max Connections', '10,000']
    ]
    t = Table(lb_specs, colWidths=[2.5*inch, 3.5*inch])
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
    
    elements.append(Paragraph("2.2 Load Balancing Algorithm", subheading_style))
    elements.append(Spacer(1, 12))
    
    lb_algo = """
    The load balancer uses a weighted round-robin algorithm with session persistence (sticky sessions) 
    based on client IP address. SSL termination is performed at the load balancer level using 
    TLS 1.2/1.3 with strong cipher suites.
    """
    elements.append(Paragraph(lb_algo, normal_style))
    elements.append(Spacer(1, 20))
    
    # Web Server Details
    elements.append(Paragraph("3. Web Server Configuration", heading_style))
    elements.append(Spacer(1, 12))
    
    elements.append(Paragraph("3.1 Technical Specifications", subheading_style))
    elements.append(Spacer(1, 12))
    
    web_specs = [
        ['Parameter', 'Value'],
        ['Software', 'Apache Tomcat 9.0.65'],
        ['Operating System', 'Red Hat Enterprise Linux 8'],
        ['CPU', '8 cores @ 3.0 GHz'],
        ['Memory', '16 GB RAM'],
        ['Storage', '100 GB SSD'],
        ['JVM Version', 'OpenJDK 11.0.16'],
        ['JVM Heap Size', '-Xms8g -Xmx12g'],
        ['Thread Pool Size', '200'],
        ['Connection Timeout', '30 seconds'],
        ['Session Timeout', '30 minutes']
    ]
    t = Table(web_specs, colWidths=[2.5*inch, 3.5*inch])
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
    
    elements.append(Paragraph("3.2 Deployed Applications", subheading_style))
    elements.append(Spacer(1, 12))
    
    web_apps = """
    The web servers host the customer-facing web application (shopnow-web.war) which provides 
    the user interface for browsing products, managing shopping carts, and checkout. The application 
    is built using JSP, Servlets, and JavaScript (React.js for frontend).
    """
    elements.append(Paragraph(web_apps, normal_style))
    elements.append(Spacer(1, 20))
    
    elements.append(PageBreak())
    
    # Application Server Details
    elements.append(Paragraph("4. Application Server Configuration", heading_style))
    elements.append(Spacer(1, 12))
    
    elements.append(Paragraph("4.1 Technical Specifications", subheading_style))
    elements.append(Spacer(1, 12))
    
    app_specs = [
        ['Parameter', 'Value'],
        ['Software', 'Java Spring Boot 2.7.5'],
        ['Operating System', 'Red Hat Enterprise Linux 8'],
        ['CPU', '16 cores @ 3.2 GHz'],
        ['Memory', '32 GB RAM'],
        ['Storage', '200 GB SSD'],
        ['JVM Version', 'OpenJDK 11.0.16'],
        ['JVM Heap Size', '-Xms16g -Xmx28g'],
        ['Thread Pool Size', '500'],
        ['Database Connection Pool', '50 connections'],
        ['API Rate Limit', '1000 requests/minute']
    ]
    t = Table(app_specs, colWidths=[2.5*inch, 3.5*inch])
