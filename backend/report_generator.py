"""
report_generator.py
Generates clean, professional PDF reports for customer credit risk predictions
using ReportLab.
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from datetime import datetime


def generate_pdf_report(customer_data, output_path):
    """
    Creates a clean, professional PDF credit default risk report.
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#1a2a40'),
        alignment=0
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#555555')
    )

    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#1a2a40'),
        spaceBefore=12,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#222222')
    )

    bullet_style = ParagraphStyle(
        'BulletStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor('#333333'),
        leftIndent=15
    )

    story = []

    # Title & Header
    story.append(Paragraph("AI-Based Credit Default Risk Assessment Report", title_style))
    story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')} | Confidential Banking Document", subtitle_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#1a2a40'), spaceBefore=2, spaceAfter=15))

    # Determine risk badge color
    risk_cat = customer_data.get("risk_category", "Moderate Risk")
    if "Low" in risk_cat:
        risk_color = colors.HexColor('#27ae60')
    elif "High" in risk_cat:
        risk_color = colors.HexColor('#e74c3c')
    else:
        risk_color = colors.HexColor('#f39c12')

    # Executive Summary Table
    summary_data = [
        [
            Paragraph("<b>Customer ID:</b>", body_style),
            Paragraph(f"<b>{customer_data.get('customer_id', 'N/A')}</b>", body_style),
            Paragraph("<b>Review Status:</b>", body_style),
            Paragraph(f"{customer_data.get('review_status', 'Not Reviewed')}", body_style)
        ],
        [
            Paragraph("<b>Default Probability:</b>", body_style),
            Paragraph(f"<b>{customer_data.get('probability', 0.0)}%</b>", body_style),
            Paragraph("<b>ML Prediction:</b>", body_style),
            Paragraph(f"<b>{customer_data.get('prediction', 'N/A')}</b>", body_style)
        ],
        [
            Paragraph("<b>Risk Category:</b>", body_style),
            Paragraph(f"<b>{risk_cat}</b>", ParagraphStyle('RiskBadge', parent=body_style, textColor=risk_color, fontName='Helvetica-Bold')),
            Paragraph("<b>Decision Threshold:</b>", body_style),
            Paragraph(f"{customer_data.get('decision_threshold', 0.50)}", body_style)
        ]
    ]

    t_summary = Table(summary_data, colWidths=[120, 140, 120, 140])
    t_summary.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#dcdfe6')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#ebeef5')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_summary)
    story.append(Spacer(1, 15))

    # Financial Profile
    story.append(Paragraph("1. Customer Financial Profile", section_heading))
    financial_data = [
        [
            Paragraph("<b>Credit Limit:</b>", body_style),
            Paragraph(f"NT$ {float(customer_data.get('limit_bal', 0)):,.0f}", body_style),
            Paragraph("<b>Age:</b>", body_style),
            Paragraph(f"{customer_data.get('age', 'N/A')} years", body_style)
        ],
        [
            Paragraph("<b>Latest Bill Statement:</b>", body_style),
            Paragraph(f"NT$ {float(customer_data.get('bill_amt1', 0)):,.0f}", body_style),
            Paragraph("<b>Latest Payment Paid:</b>", body_style),
            Paragraph(f"NT$ {float(customer_data.get('pay_amt1', 0)):,.0f}", body_style)
        ],
        [
            Paragraph("<b>Recent Payment Status (PAY_1):</b>", body_style),
            Paragraph(f"{customer_data.get('pay_1', 0)} month(s) delay", body_style),
            Paragraph("<b>Evaluation Date:</b>", body_style),
            Paragraph(f"{customer_data.get('created_at', datetime.now().strftime('%Y-%m-%d'))}", body_style)
        ]
    ]
    t_fin = Table(financial_data, colWidths=[140, 120, 130, 130])
    t_fin.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('BOX', (0, 0), (-1, -1), 0.8, colors.HexColor('#dcdfe6')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#ebeef5')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_fin)
    story.append(Spacer(1, 15))

    # Explainable AI Insights (SHAP)
    story.append(Paragraph("2. Explainable AI Insights (Key Risk Drivers)", section_heading))
    reasons = customer_data.get("top_reasons", [])
    if reasons:
        story.append(Paragraph("The Machine Learning model evaluated customer payment patterns and identified the following primary contributing factors:", body_style))
        story.append(Spacer(1, 5))
        for r in reasons:
            story.append(Paragraph(f"• {r}", bullet_style))
            story.append(Spacer(1, 3))
    else:
        story.append(Paragraph("No significant negative risk factors detected.", body_style))
    story.append(Spacer(1, 15))

    # Credit Policy Recommendations
    story.append(Paragraph("3. Recommended Credit Actions", section_heading))
    if "High" in risk_cat:
        rec_text = "<b>High Risk Warning:</b> Customer has high probability of defaulting on their next payment. Recommended actions include placing an alert, following up for early payment reminder, and conducting a formal credit line review before extending further credit."
    elif "Moderate" in risk_cat:
        rec_text = "<b>Moderate Risk Notice:</b> Customer exhibits moderate risk. Regular automated monthly reminders and ongoing payment behavior monitoring are suggested."
    else:
        rec_text = "<b>Low Risk Good Standing:</b> Customer has strong repayment history and healthy credit utilization. Standard billing procedures apply."
    
    story.append(Paragraph(rec_text, body_style))
    story.append(Spacer(1, 20))

    # Disclaimer Footer
    story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor('#dcdfe6'), spaceBefore=10, spaceAfter=10))
    disclaimer = (
        "<b>Important Notice:</b> Whitelist or review status indicates human oversight and does not alter the underlying "
        "machine learning statistical default risk probability. All evaluations are generated using the trained XGBoost model."
    )
    story.append(Paragraph(disclaimer, ParagraphStyle('Disclaimer', parent=styles['Normal'], fontSize=8, leading=11, textColor=colors.HexColor('#777777'))))

    doc.build(story)
    return output_path

