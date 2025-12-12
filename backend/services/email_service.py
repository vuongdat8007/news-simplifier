import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Tuple
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()


def get_smtp_config() -> dict:
    """Get SMTP configuration from environment variables."""
    return {
        "host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
        "port": int(os.getenv("SMTP_PORT", "587")),
        "user": os.getenv("SMTP_USER", ""),
        "password": os.getenv("SMTP_PASSWORD", ""),
        "recipients": os.getenv("EMAIL_RECIPIENTS", "").split(",")
    }


def send_email(
    to: List[str],
    subject: str,
    body_html: str,
    body_text: str = "",
    attachments: Optional[List[Tuple[str, bytes, str]]] = None
) -> bool:
    """
    Send an email via SMTP.
    
    Args:
        to: List of recipient email addresses
        subject: Email subject
        body_html: HTML body content
        body_text: Plain text body (fallback)
        attachments: List of (filename, content_bytes, mime_type) tuples
    
    Returns:
        True if email sent successfully, False otherwise
    """
    config = get_smtp_config()
    
    if not config["user"] or not config["password"]:
        print("[ERROR] SMTP credentials not configured")
        return False
    
    if not to or not any(t.strip() for t in to):
        print("[ERROR] No recipients configured")
        return False
    
    # Filter empty recipients
    recipients = [r.strip() for r in to if r.strip()]
    
    try:
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = config["user"]
        msg["To"] = ", ".join(recipients)
        
        # Add text and HTML parts
        if body_text:
            msg.attach(MIMEText(body_text, "plain"))
        msg.attach(MIMEText(body_html, "html"))
        
        # Add attachments
        if attachments:
            for filename, content, mime_type in attachments:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(content)
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={filename}"
                )
                msg.attach(part)
        
        # Send email
        print(f"[DEBUG] Connecting to SMTP: {config['host']}:{config['port']}")
        with smtplib.SMTP(config["host"], config["port"]) as server:
            server.starttls()
            server.login(config["user"], config["password"])
            server.sendmail(config["user"], recipients, msg.as_string())
        
        print(f"[DEBUG] Email sent successfully to {len(recipients)} recipients")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")
        return False


def send_news_summary_email(
    summary: str,
    pdf_bytes: Optional[bytes] = None,
    audio_bytes: Optional[bytes] = None,
    recipients: Optional[List[str]] = None
) -> bool:
    """
    Send a news summary email with optional PDF and audio attachments.
    
    Args:
        summary: The news summary text
        pdf_bytes: Optional PDF attachment bytes
        audio_bytes: Optional audio attachment bytes
        recipients: Optional list of recipients (uses config if not provided)
    
    Returns:
        True if email sent successfully, False otherwise
    """
    config = get_smtp_config()
    to_list = recipients or config["recipients"]
    
    now = datetime.now()
    date_str = now.strftime("%B %d, %Y")
    time_str = now.strftime("%I:%M %p")
    
    subject = f"📰 Your Daily News Summary - {date_str}"
    
    # Create HTML email body
    body_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                border-radius: 12px;
                text-align: center;
                margin-bottom: 20px;
            }}
            .header h1 {{
                margin: 0;
                font-size: 24px;
            }}
            .header p {{
                margin: 10px 0 0 0;
                opacity: 0.9;
            }}
            .content {{
                background: #f8f9fa;
                padding: 25px;
                border-radius: 12px;
                border-left: 4px solid #667eea;
            }}
            .footer {{
                text-align: center;
                color: #666;
                font-size: 12px;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #eee;
            }}
            .attachments {{
                background: #e3f2fd;
                padding: 15px;
                border-radius: 8px;
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📰 Daily News Summary</h1>
            <p>Generated on {date_str} at {time_str}</p>
        </div>
        
        <div class="content">
            {summary.replace(chr(10), '<br>')}
        </div>
        
        {"<div class='attachments'><strong>📎 Attachments:</strong> " + 
         ("PDF Summary" if pdf_bytes else "") + 
         (" • " if pdf_bytes and audio_bytes else "") + 
         ("Audio Summary (MP3)" if audio_bytes else "") + 
         "</div>" if pdf_bytes or audio_bytes else ""}
        
        <div class="footer">
            <p>This email was automatically generated by News Simplifier</p>
            <p>Powered by GPT-4o-mini and OpenAI TTS</p>
        </div>
    </body>
    </html>
    """
    
    # Plain text fallback
    body_text = f"""
Daily News Summary - {date_str}
Generated at {time_str}

{summary}

---
This email was automatically generated by News Simplifier
    """
    
    # Prepare attachments
    attachments = []
    if pdf_bytes:
        attachments.append((f"news_summary_{now.strftime('%Y%m%d')}.pdf", pdf_bytes, "application/pdf"))
    if audio_bytes:
        attachments.append((f"news_summary_{now.strftime('%Y%m%d')}.mp3", audio_bytes, "audio/mpeg"))
    
    return send_email(to_list, subject, body_html, body_text, attachments if attachments else None)
