"""
Feedback router - Firebase version.
Handles email feedback submissions and adaptive word count adjustment.
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse
from datetime import datetime, timezone

import firebase_models as fm

router = APIRouter(prefix="/api/feedback", tags=["Feedback"])


@router.get("/{token}")
def submit_feedback(
    token: str,
    rating: str = Query(..., description="Feedback rating: too_short, just_right, or too_long")
):
    """
    Handle feedback submission from email links.
    
    Adjusts user's target word count based on feedback:
    - too_long: decrease by 50 words
    - too_short: increase by 50 words
    - just_right: no change
    """
    if rating not in ["too_short", "just_right", "too_long"]:
        raise HTTPException(status_code=400, detail="Invalid rating. Must be: too_short, just_right, or too_long")
    
    try:
        # Find delivery log by token
        delivery = fm.get_delivery_log_by_token(token)
        
        if not delivery:
            return HTMLResponse(content=_render_feedback_page(
                success=False,
                message="Feedback link not found or expired."
            ), status_code=404)
        
        # Check if already submitted
        if delivery.get("feedback_received"):
            return HTMLResponse(content=_render_feedback_page(
                success=True,
                message=f"You already submitted feedback: {_format_rating(delivery['feedback_received'])}",
                already_submitted=True
            ))
        
        # Check if expired
        expires_at = delivery.get("feedback_expires_at")
        if expires_at and datetime.now(timezone.utc) > expires_at:
            return HTMLResponse(content=_render_feedback_page(
                success=False,
                message="This feedback link has expired."
            ))
        
        # Record feedback
        fm.update_delivery_log(delivery["id"], {
            "feedback_received": rating,
            "feedback_received_at": datetime.now(timezone.utc)
        })
        
        # Adjust user's target word count
        settings = fm.get_user_settings(delivery["user_id"])
        adjustment_message = ""
        
        if settings:
            old_word_count = settings.get("target_word_count", 500)
            
            if rating == "too_long":
                new_word_count = max(200, old_word_count - 50)
                fm.update_user_settings(delivery["user_id"], {"target_word_count": new_word_count})
                adjustment_message = f"Summary length decreased: {old_word_count} → {new_word_count} words"
            elif rating == "too_short":
                new_word_count = min(1000, old_word_count + 50)
                fm.update_user_settings(delivery["user_id"], {"target_word_count": new_word_count})
                adjustment_message = f"Summary length increased: {old_word_count} → {new_word_count} words"
            else:
                adjustment_message = f"Summary length unchanged: {old_word_count} words"
        
        print(f"[FEEDBACK] Token {token}: rating={rating}, {adjustment_message}")
        
        return HTMLResponse(content=_render_feedback_page(
            success=True,
            message="Thank you for your feedback!",
            rating=rating,
            adjustment=adjustment_message
        ))
        
    except Exception as e:
        print(f"[FEEDBACK] Error processing feedback: {e}")
        raise HTTPException(status_code=500, detail="Error processing feedback")


def _format_rating(rating: str) -> str:
    """Format rating for display."""
    return {
        "too_short": "📈 Too Short",
        "just_right": "✅ Just Right",
        "too_long": "📉 Too Long"
    }.get(rating, rating)


def _render_feedback_page(
    success: bool,
    message: str,
    rating: str = None,
    adjustment: str = None,
    already_submitted: bool = False
) -> str:
    """Render HTML feedback confirmation page."""
    
    icon = "✅" if success else "❌"
    color = "#10b981" if success else "#ef4444"
    
    rating_display = ""
    if rating:
        rating_display = f"""
        <div style="background: #f0f4f8; padding: 15px 25px; border-radius: 10px; margin: 20px 0;">
            <p style="margin: 0; font-size: 18px;">{_format_rating(rating)}</p>
        </div>
        """
    
    adjustment_display = ""
    if adjustment:
        adjustment_display = f"""
        <p style="color: #666; font-size: 14px; margin-top: 15px;">
            📊 {adjustment}
        </p>
        """
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Feedback Received - AI News Assistant</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }}
            .card {{
                background: white;
                border-radius: 20px;
                padding: 40px;
                max-width: 450px;
                width: 100%;
                text-align: center;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }}
            .icon {{
                font-size: 64px;
                margin-bottom: 20px;
            }}
            h1 {{
                color: #333;
                margin-bottom: 15px;
                font-size: 24px;
            }}
            .message {{
                color: #555;
                line-height: 1.6;
                margin-bottom: 25px;
            }}
            .footer {{
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #eee;
                color: #888;
                font-size: 13px;
            }}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="icon">{icon}</div>
            <h1 style="color: {color};">{'Feedback Received!' if success else 'Oops!'}</h1>
            <p class="message">{message}</p>
            {rating_display}
            {adjustment_display}
            <div class="footer">
                <p>🤖 AI News Assistant</p>
                <p style="margin-top: 5px;">Your feedback helps us improve.</p>
            </div>
        </div>
    </body>
    </html>
    """
