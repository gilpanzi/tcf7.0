import os
import json
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_quotation_pdf(project, fans_data, filepath):
    """Generates a professional PDF quotation."""
    doc = SimpleDocTemplate(filepath, pagesize=letter,
                            rightMargin=40, leftMargin=40,
                            topMargin=40, bottomMargin=40)
    
    Story = []
    styles = getSampleStyleSheet()
    
    # Custom Styles
    styles.add(ParagraphStyle(name='RightAlign', parent=styles['Normal'], alignment=2))
    styles.add(ParagraphStyle(name='CenterAlign', parent=styles['Normal'], alignment=1))
    
    # 1. Header (Logo/Company Info)
    header_data = [
        [Paragraph("<b>TCF India (Twin City Fan)</b><br/>Chennai, Tamil Nadu<br/>India", styles['Normal']), 
         Paragraph(f"<b>Quotation:</b> QT-{project['enquiry_number']}<br/><b>Date:</b> {datetime.now().strftime('%d-%b-%Y')}", styles['RightAlign'])]
    ]
    header_table = Table(header_data, colWidths=['60%', '40%'])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    Story.append(header_table)
    Story.append(Spacer(1, 20))
    Story.append(Paragraph("<hr/>", styles['Normal']))
    Story.append(Spacer(1, 20))
    
    # 2. Customer Info
    cust_data = [
        ["To:", project.get('customer_name', 'Valued Customer')],
        ["Attention:", "Purchase Department"],
        ["Reference:", project.get('enquiry_number', '')]
    ]
    cust_table = Table(cust_data, colWidths=[60, 400])
    cust_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    Story.append(cust_table)
    Story.append(Spacer(1, 20))
    
    # 3. Intro Text
    Story.append(Paragraph("Dear Sir/Madam,", styles['Normal']))
    Story.append(Spacer(1, 10))
    Story.append(Paragraph("We thank you for your enquiry and are pleased to quote for the following equipment:", styles['Normal']))
    Story.append(Spacer(1, 15))
    
    # 4. Itemized Table
    table_data = [['Item', 'Qty', 'Model / Details', 'Unit Price (INR)', 'Total Price (INR)']]
    
    total_cost = 0
    for idx, fan in enumerate(fans_data):
        specs = json.loads(fan.get('specifications', '{}'))
        costs = json.loads(fan.get('costs', '{}'))
        
        qty = 1 # Assuming 1 per fan entry for now
        unit_price = float(costs.get('total_selling_price', 0))
        total_price = unit_price * qty
        total_cost += total_price
        
        model = specs.get('model', 'Standard Centrifugal Fan')
        arr = specs.get('arrangement', 'Arr 4')
        
        details = f"{model} - {arr}"
        
        table_data.append([
            str(idx + 1),
            str(qty),
            details,
            f"{unit_price:,.2f}",
            f"{total_price:,.2f}"
        ])
        
    # Totals Row
    table_data.append(['', '', '', 'Sub Total:', f"{total_cost:,.2f}"])
    
    item_table = Table(table_data, colWidths=[40, 40, 240, 100, 100])
    item_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        
        ('BACKGROUND', (0,1), (-1,-2), colors.beige),
        ('ALIGN', (1,1), (-1,-1), 'RIGHT'),
        ('ALIGN', (2,1), (2,-2), 'LEFT'),
        
        ('FONTNAME', (3,-1), (4,-1), 'Helvetica-Bold'),
        ('LINEABOVE', (3,-1), (4,-1), 1, colors.black),
        ('LINEBELOW', (3,-1), (4,-1), 1, colors.black),
        
        ('GRID', (0,0), (-1,-2), 0.5, colors.black)
    ]))
    
    Story.append(item_table)
    Story.append(Spacer(1, 30))
    
    # 5. Terms & Conditions
    Story.append(Paragraph("<b>Terms & Conditions:</b>", styles['Normal']))
    Story.append(Spacer(1, 5))
    terms = [
        "1. Taxes: Extra as applicable at the time of dispatch.",
        "2. Validity: 30 days from the date of this quotation.",
        "3. Delivery: 6-8 weeks from the date of drawing approval.",
        "4. Payment: 30% advance, balance against proforma invoice before dispatch."
    ]
    for term in terms:
        Story.append(Paragraph(term, styles['Normal']))
        Story.append(Spacer(1, 2))
        
    Story.append(Spacer(1, 40))
    
    # 6. Sign off
    Story.append(Paragraph("For <b>Twin City Fan India Pvt Ltd</b>,", styles['Normal']))
    Story.append(Spacer(1, 40))
    Story.append(Paragraph(f"{project.get('sales_engineer', 'Sales Manager')}<br/>Authorized Signatory", styles['Normal']))

    doc.build(Story)
    return filepath
