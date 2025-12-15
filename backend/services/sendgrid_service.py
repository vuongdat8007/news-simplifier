import os
import base64
from typing import List, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()


def get_sendgrid_config() -> dict:
    """Get SendGrid configuration from environment variables."""
    return {
        "api_key": os.getenv("SENDGRID_API_KEY", ""),
        "from_email": os.getenv("SENDGRID_FROM_EMAIL", "")
    }


def send_email_with_sendgrid(
    to_email: str,
    subject: str,
    html_content: str,
    plain_content: str = "",
    attachments: Optional[List[Tuple[str, bytes, str]]] = None
) -> Tuple[bool, str]:
    """
    Send an email using SendGrid API.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        html_content: HTML body content
        plain_content: Plain text body (fallback)
        attachments: List of (filename, content_bytes, mime_type) tuples
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import (
        Mail, Attachment, FileContent, FileName, 
        FileType, Disposition
    )
    
    config = get_sendgrid_config()
    
    if not config["api_key"] or config["api_key"] == "SG.your-sendgrid-api-key-here":
        return False, "SendGrid API key not configured"
    
    if not config["from_email"] or config["from_email"] == "your-verified-sender@domain.com":
        return False, "SendGrid sender email not configured"
    
    try:
        # Create mail object
        message = Mail(
            from_email=config["from_email"],
            to_emails=to_email,
            subject=subject,
            html_content=html_content,
            plain_text_content=plain_content or "Please view this email in an HTML-capable client."
        )
        
        # Add attachments
        if attachments:
            for filename, content_bytes, mime_type in attachments:
                encoded_content = base64.b64encode(content_bytes).decode('utf-8')
                
                attachment = Attachment(
                    FileContent(encoded_content),
                    FileName(filename),
                    FileType(mime_type),
                    Disposition('attachment')
                )
                message.add_attachment(attachment)
        
        # Send email
        sg = SendGridAPIClient(config["api_key"])
        response = sg.send(message)
        
        print(f"[SENDGRID] Email sent! Status: {response.status_code}")
        
        if response.status_code in [200, 201, 202]:
            return True, f"Email sent successfully to {to_email}"
        else:
            return False, f"SendGrid returned status {response.status_code}"
            
    except Exception as e:
        print(f"[SENDGRID] Error: {e}")
        return False, str(e)


def send_summary_email(
    to_email: str,
    summary_text: str,
    pdf_bytes: Optional[bytes] = None,
    audio_bytes: Optional[bytes] = None
) -> Tuple[bool, str]:
    """
    Send a news summary email with optional PDF and audio attachments.
    
    Args:
        to_email: Recipient email address
        summary_text: The news summary text
        pdf_bytes: Optional PDF attachment bytes
        audio_bytes: Optional audio attachment bytes
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    from datetime import datetime
    
    now = datetime.now()
    date_str = now.strftime("%B %d, %Y")
    time_str = now.strftime("%I:%M %p")
    
    subject = f"📰 Your AI News Summary - {date_str}"
    
    # Create HTML email body
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                background: #f5f5f5;
            }}
            .container {{
                background: white;
                border-radius: 16px;
                overflow: hidden;
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
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
                padding: 30px;
            }}
            .summary {{
                background: #f8f9fa;
                padding: 20px;
                border-radius: 12px;
                border-left: 4px solid #667eea;
                white-space: pre-wrap;
            }}
            .attachments {{
                background: #e8f4fd;
                padding: 15px 20px;
                border-radius: 8px;
                margin-top: 20px;
            }}
            .footer {{
                text-align: center;
                color: #888;
                font-size: 12px;
                padding: 20px;
                border-top: 1px solid #eee;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 AI News Summary</h1>
                <p>Generated on {date_str} at {time_str}</p>
            </div>
            
            <div class="content">
                <div class="summary">{summary_text}</div>
                
                {f'<div class="attachments"><strong>📎 Attachments included:</strong><br>' + 
                 ('• PDF Summary<br>' if pdf_bytes else '') + 
                 ('• Audio Summary (MP3)' if audio_bytes else '') + 
                 '</div>' if pdf_bytes or audio_bytes else ''}
            </div>
            
            <div class="footer">
                <p>Sent via AI News Assistant</p>
                <p>Powered by GPT-4o-mini & OpenAI TTS</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Prepare attachments
    attachments = []
    if pdf_bytes:
        attachments.append((
            f"news_summary_{now.strftime('%Y%m%d')}.pdf",
            pdf_bytes,
            "application/pdf"
        ))
    if audio_bytes:
        attachments.append((
            f"news_summary_{now.strftime('%Y%m%d')}.mp3",
            audio_bytes,
            "audio/mpeg"
        ))
    
    return send_email_with_sendgrid(
        to_email=to_email,
        subject=subject,
        html_content=html_content,
        plain_content=summary_text,
        attachments=attachments if attachments else None
    )


def send_summary_email_with_feedback(
    to_email: str,
    summary_text: str,
    pdf_bytes: Optional[bytes] = None,
    audio_bytes: Optional[bytes] = None,
    feedback_token: Optional[str] = None,
    app_base_url: str = None
) -> Tuple[bool, str]:
    """
    Send a news summary email with feedback buttons and optional attachments.
    
    Args:
        to_email: Recipient email address
        summary_text: The news summary text
        pdf_bytes: Optional PDF attachment bytes
        audio_bytes: Optional audio attachment bytes
        feedback_token: Unique token for feedback tracking
        app_base_url: Base URL for feedback links (default from env)
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    from datetime import datetime
    
    if not app_base_url:
        app_base_url = os.getenv("APP_BASE_URL", "http://localhost:8000")
    
    now = datetime.now()
    date_str = now.strftime("%B %d, %Y")
    time_str = now.strftime("%I:%M %p")
    
    subject = f"📰 Your AI News Summary - {date_str}"
    
    # Feedback buttons HTML (only if token provided)
    feedback_html = ""
    if feedback_token:
        feedback_html = f"""
        <div style="background: #f0f4f8; padding: 20px; border-radius: 12px; margin-top: 25px; text-align: center;">
            <p style="margin: 0 0 15px 0; font-weight: 600; color: #333;">How was this summary?</p>
            <p style="margin: 0 0 15px 0; font-size: 14px; color: #666;">Your feedback helps us improve future summaries.</p>
            <div style="display: inline-block;">
                <a href="{app_base_url}/api/feedback/{feedback_token}?rating=too_short" 
                   style="display: inline-block; background: #10b981; color: white; padding: 10px 20px; border-radius: 8px; text-decoration: none; margin: 5px; font-weight: 500;">
                    📈 Too Short
                </a>
                <a href="{app_base_url}/api/feedback/{feedback_token}?rating=just_right" 
                   style="display: inline-block; background: #667eea; color: white; padding: 10px 20px; border-radius: 8px; text-decoration: none; margin: 5px; font-weight: 500;">
                    ✅ Just Right
                </a>
                <a href="{app_base_url}/api/feedback/{feedback_token}?rating=too_long" 
                   style="display: inline-block; background: #f59e0b; color: white; padding: 10px 20px; border-radius: 8px; text-decoration: none; margin: 5px; font-weight: 500;">
                    📉 Too Long
                </a>
            </div>
        </div>
        """
    
    # Create HTML email body
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                background: #f5f5f5;
            }}
            .container {{
                background: white;
                border-radius: 16px;
                overflow: hidden;
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
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
                padding: 30px;
            }}
            .summary {{
                background: #f8f9fa;
                padding: 20px;
                border-radius: 12px;
                border-left: 4px solid #667eea;
                white-space: pre-wrap;
            }}
            .attachments {{
                background: #e8f4fd;
                padding: 15px 20px;
                border-radius: 8px;
                margin-top: 20px;
            }}
            .footer {{
                text-align: center;
                color: #888;
                font-size: 12px;
                padding: 20px;
                border-top: 1px solid #eee;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 AI News Summary</h1>
                <p>Generated on {date_str} at {time_str}</p>
            </div>
            
            <div class="content">
                <div class="summary">{summary_text}</div>
                
                {f'<div class="attachments"><strong>📎 Attachments included:</strong><br>' + 
                 ('• PDF Summary<br>' if pdf_bytes else '') + 
                 ('• Audio Summary (MP3)' if audio_bytes else '') + 
                 '</div>' if pdf_bytes or audio_bytes else ''}
                
                {feedback_html}
            </div>
            
            <div class="footer">
                <p>Sent via AI News Assistant</p>
                <p>Powered by GPT-4o-mini & OpenAI TTS</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Prepare attachments
    attachments = []
    if pdf_bytes:
        attachments.append((
            f"news_summary_{now.strftime('%Y%m%d')}.pdf",
            pdf_bytes,
            "application/pdf"
        ))
    if audio_bytes:
        attachments.append((
            f"news_summary_{now.strftime('%Y%m%d')}.mp3",
            audio_bytes,
            "audio/mpeg"
        ))
    
    return send_email_with_sendgrid(
        to_email=to_email,
        subject=subject,
        html_content=html_content,
        plain_content=summary_text,
        attachments=attachments if attachments else None
    )
