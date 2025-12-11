from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.colors import HexColor


def create_pdf(digest_text: str, title: str = "Daily News Digest") -> bytes:
    """
    Generate a PDF document from the digest text.
    Returns PDF as bytes.
    """
    buffer = BytesIO()
    
    # Create the PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=20,
        textColor=HexColor('#1a1a1a'),
        alignment=1  # Center
    )
    
    date_style = ParagraphStyle(
        'DateStyle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=HexColor('#666666'),
        alignment=1,  # Center
        spaceAfter=30
    )
    
    body_style = ParagraphStyle(
        'BodyStyle',
        parent=styles['Normal'],
        fontSize=11,
        leading=16,
        textColor=HexColor('#333333'),
        spaceAfter=12
    )
    
    heading_style = ParagraphStyle(
        'HeadingStyle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=HexColor('#2196f3'),
        spaceBefore=15,
        spaceAfter=10
    )
    
    # Build content
    story = []
    
    # Title
    story.append(Paragraph(title, title_style))
    
    # Date
    today = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    story.append(Paragraph(f"Generated on {today}", date_style))
    
    # Spacer
    story.append(Spacer(1, 0.25 * inch))
    
    # Process digest text - handle markdown-style formatting
    lines = digest_text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            story.append(Spacer(1, 0.1 * inch))
            continue
        
        # Handle headers
        if line.startswith('# '):
            story.append(Paragraph(line[2:], heading_style))
        elif line.startswith('## '):
            story.append(Paragraph(line[3:], heading_style))
        elif line.startswith('**') and line.endswith('**'):
            # Bold text
            clean = line.strip('*')
            story.append(Paragraph(f"<b>{clean}</b>", body_style))
        elif line.startswith('---'):
            story.append(Spacer(1, 0.2 * inch))
        elif line.startswith('*') and line.endswith('*'):
            # Italic text
            clean = line.strip('*')
            story.append(Paragraph(f"<i>{clean}</i>", body_style))
        else:
            # Regular paragraph - escape any HTML-like content
            safe_line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            # But preserve our intentional bold/italic
            safe_line = safe_line.replace('**', '')
            story.append(Paragraph(safe_line, body_style))
    
    # Build PDF
    doc.build(story)
    
    # Get PDF bytes
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes
