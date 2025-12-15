from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from services.news_fetcher import fetch_news
from services.simplifier import simplify_text
from io import BytesIO

# Import auth router
from auth_router import router as auth_router

# Import settings router
from settings_router import router as settings_router

# Import admin router
from admin_router import router as admin_router

# Import feedback router
from feedback_router import router as feedback_router

# Import delivery router
from delivery_router import router as delivery_router

# Import database
from database import engine, Base

app = FastAPI(title="News Simplifier API")

# Create database tables on startup
@app.on_event("startup")
async def startup_db():
    """Initialize database tables."""
    from models import User, UserSettings, EmailDeliveryLog
    Base.metadata.create_all(bind=engine)
    print("[DATABASE] Tables initialized")

# Include routers
app.include_router(auth_router)
app.include_router(settings_router)
app.include_router(admin_router)
app.include_router(feedback_router)
app.include_router(delivery_router)

# Configure CORS
origins = [
    "http://localhost:8501", # Streamlit default port
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SimplifyRequest(BaseModel):
    text: str

@app.get("/")
def read_root():
    return {"message": "Welcome to News Simplifier API"}

@app.get("/news")
def get_news(categories: str = None):
    """
    Get news articles, optionally filtered by categories.
    
    Args:
        categories: Comma-separated list of category keys (e.g., "technology,business")
    """
    from services.news_fetcher import fetch_news_by_categories, RSS_FEEDS_BY_CATEGORY
    
    if categories:
        category_list = [c.strip() for c in categories.split(",")]
        news = fetch_news_by_categories(category_list)
    else:
        news = fetch_news()
    
    return {"news": news}


@app.get("/categories")
def get_categories():
    """Get available news categories."""
    from services.news_fetcher import RSS_FEEDS_BY_CATEGORY
    
    categories = [
        {"key": key, "name": info["name"], "emoji": info["emoji"]}
        for key, info in RSS_FEEDS_BY_CATEGORY.items()
    ]
    return {"categories": categories}


@app.get("/sources")
def get_sources():
    """Get available news sources (individual publishers)."""
    from services.news_fetcher import NEWS_SOURCES
    
    sources = [
        {"key": key, "name": info["name"], "emoji": info["emoji"]}
        for key, info in NEWS_SOURCES.items()
    ]
    return {"sources": sources}


@app.get("/news/sources")
def get_news_by_sources(sources: str = None):
    """
    Get news from specific sources.
    
    Args:
        sources: Comma-separated list of source keys (e.g., "reuters,techcrunch")
    """
    from services.news_fetcher import fetch_news_by_sources
    
    if sources:
        source_list = [s.strip() for s in sources.split(",")]
        news = fetch_news_by_sources(source_list)
    else:
        news = []
    
    return {"news": news}


@app.get("/feedly/status")
def get_feedly_status():
    """Check if Feedly API is configured."""
    from services.feedly_fetcher import is_feedly_configured
    return {"configured": is_feedly_configured()}


@app.get("/feedly/articles")
def get_feedly_articles(count: int = 20):
    """
    Fetch articles from user's Feedly feeds.
    Requires FEEDLY_API_KEY to be configured.
    """
    from services.feedly_fetcher import fetch_feedly_articles, is_feedly_configured
    
    if not is_feedly_configured():
        raise HTTPException(status_code=503, detail="Feedly API not configured. Set FEEDLY_API_KEY environment variable.")
    
    articles = fetch_feedly_articles(count_per_feed=count)
    return {"news": articles}

@app.post("/simplify")
def simplify_news(request: SimplifyRequest):
    if not request.text:
        raise HTTPException(status_code=400, detail="No text provided")
    
    simplified = simplify_text(request.text)
    return {"simplified": simplified}


@app.get("/digest")
def get_digest():
    """Generate a one-page digest from all current news articles."""
    from services.digest_service import generate_digest
    digest = generate_digest()
    return digest


@app.get("/digest/pdf")
def get_digest_pdf():
    """Generate and download the news digest as a PDF."""
    from services.digest_service import generate_digest
    from services.pdf_service import create_pdf
    
    # Generate the digest
    digest_data = generate_digest()
    digest_text = digest_data.get("digest", "No content available")
    
    # Create PDF
    pdf_bytes = create_pdf(digest_text, "Daily News Digest")
    
    # Return as downloadable file
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=news_digest.pdf"}
    )


@app.get("/digest/audio")
def get_digest_audio():
    """Generate and download the news digest as audio (MP3)."""
    from services.digest_service import generate_digest
    from services.tts_service import text_to_speech
    
    # Generate the digest
    digest_data = generate_digest()
    digest_text = digest_data.get("digest", "No content available")
    
    # Create audio
    audio_bytes = text_to_speech(digest_text)
    
    # Return as downloadable MP3 file
    return StreamingResponse(
        BytesIO(audio_bytes),
        media_type="audio/mpeg",
        headers={"Content-Disposition": "attachment; filename=news_digest.mp3"}
    )


class SummarizeRequest(BaseModel):
    text: str


@app.post("/summarize-combined")
def summarize_combined(request: SummarizeRequest):
    """Summarize combined news excerpts using GPT-4o-mini."""
    from services.openai_service import summarize_combined_excerpts
    
    if not request.text:
        raise HTTPException(status_code=400, detail="No text provided")
    
    summary = summarize_combined_excerpts(request.text)
    
    if summary is None:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured or error occurred")
    
    return {"summary": summary}


@app.post("/summary/pdf")
def get_summary_pdf(request: SummarizeRequest):
    """Generate a PDF from summary text."""
    from services.pdf_service import create_pdf
    
    if not request.text:
        raise HTTPException(status_code=400, detail="No text provided")
    
    pdf_bytes = create_pdf(request.text, "AI News Summary")
    
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=news_summary.pdf"}
    )


@app.post("/summary/audio")
def get_summary_audio(request: SummarizeRequest, current_user = None):
    """Generate audio from summary text using OpenAI TTS (Premium only)."""
    from services.tts_service import text_to_speech_openai
    from auth import get_current_user, decode_token
    from fastapi import Header
    
    if not request.text:
        raise HTTPException(status_code=400, detail="No text provided")
    
    # Note: For now, audio is available to all authenticated users
    # Premium check will be done on frontend
    
    audio_bytes = text_to_speech_openai(request.text, voice="nova")
    
    return StreamingResponse(
        BytesIO(audio_bytes),
        media_type="audio/mpeg",
        headers={"Content-Disposition": "attachment; filename=news_summary.mp3"}
    )


@app.get("/check-premium")
def check_premium(authorization: str = Header(None)):
    """Check if current user has premium access."""
    from auth import decode_token
    from database import SessionLocal
    from models import User
    
    if not authorization or not authorization.startswith("Bearer "):
        return {"is_premium": False, "is_admin": False}
    
    token = authorization.replace("Bearer ", "")
    payload = decode_token(token)
    
    if not payload:
        return {"is_premium": False, "is_admin": False}
    
    email = payload.get("sub")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user:
            return {
                "is_premium": user.is_premium or False,
                "is_admin": user.is_admin or False
            }
    finally:
        db.close()
    
    return {"is_premium": False, "is_admin": False}


class SendEmailRequest(BaseModel):
    email: str
    summary: str


@app.post("/send-summary-email")
def send_summary_email(request: SendEmailRequest):
    """Send summary with PDF and audio attachments via SendGrid."""
    from services.pdf_service import create_pdf
    from services.tts_service import text_to_speech_openai
    from services.sendgrid_service import send_summary_email as sg_send
    
    if not request.email:
        raise HTTPException(status_code=400, detail="Email address required")
    
    if not request.summary:
        raise HTTPException(status_code=400, detail="Summary text required")
    
    try:
        # Generate PDF
        print(f"[EMAIL] Generating PDF for {request.email}...")
        pdf_bytes = create_pdf(request.summary, "AI News Summary")
        
        # Generate audio
        print(f"[EMAIL] Generating audio...")
        audio_bytes = text_to_speech_openai(request.summary, voice="nova")
        
        # Send email
        print(f"[EMAIL] Sending via SendGrid...")
        success, message = sg_send(
            to_email=request.email,
            summary_text=request.summary,
            pdf_bytes=pdf_bytes,
            audio_bytes=audio_bytes
        )
        
        if success:
            return {"success": True, "message": message}
        else:
            raise HTTPException(status_code=500, detail=message)
            
    except Exception as e:
        print(f"[EMAIL] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============== Scheduler Endpoints ==============

@app.on_event("startup")
async def startup_event():
    """Start the scheduler when the app starts."""
    from services.scheduler_service import start_scheduler
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Only start scheduler if email is configured
    if os.getenv("SMTP_USER") and os.getenv("SMTP_PASSWORD"):
        start_scheduler(interval_hours=12)
        print("[STARTUP] Scheduler started for 12-hour email delivery")
    else:
        print("[STARTUP] Email not configured - scheduler not started")
        print("[STARTUP] Set SMTP_USER, SMTP_PASSWORD, EMAIL_RECIPIENTS in .env to enable")


@app.on_event("shutdown")
async def shutdown_event():
    """Stop the scheduler when the app shuts down."""
    from services.scheduler_service import stop_scheduler
    stop_scheduler()
    print("[SHUTDOWN] Scheduler stopped")


@app.get("/scheduler/status")
def get_scheduler_status():
    """Get the current scheduler status."""
    from services.scheduler_service import get_scheduler_status as get_status
    return get_status()


@app.post("/scheduler/trigger")
def trigger_scheduler():
    """Manually trigger the scheduled news email job."""
    from services.scheduler_service import trigger_job_now
    success = trigger_job_now()
    return {"triggered": success, "message": "Job triggered" if success else "Failed to trigger job"}


@app.post("/scheduler/trigger-user/{user_id}")
def trigger_user_scheduler(user_id: int):
    """Manually trigger the scheduled news email for a specific user."""
    from services.user_scheduler_service import trigger_user_job
    success = trigger_user_job(user_id)
    return {
        "triggered": success, 
        "user_id": user_id,
        "message": f"Job triggered for user {user_id}" if success else f"Failed to trigger job for user {user_id}"
    }


class EmailConfigRequest(BaseModel):
    recipients: list[str]


@app.post("/scheduler/config")
def update_email_config(request: EmailConfigRequest):
    """Update email recipients (runtime only, does not persist)."""
    import os
    os.environ["EMAIL_RECIPIENTS"] = ",".join(request.recipients)
    return {"message": f"Recipients updated to: {request.recipients}"}


@app.post("/scheduler/test-email")
def test_email():
    """Send a test email to verify configuration."""
    from services.email_service import send_email, get_smtp_config
    
    config = get_smtp_config()
    if not config["user"] or not config["password"]:
        raise HTTPException(status_code=400, detail="SMTP not configured. Set SMTP_USER and SMTP_PASSWORD in .env")
    
    if not config["recipients"] or not any(r.strip() for r in config["recipients"]):
        raise HTTPException(status_code=400, detail="No recipients configured. Set EMAIL_RECIPIENTS in .env")
    
    success = send_email(
        to=config["recipients"],
        subject="🧪 Test Email from News Simplifier",
        body_html="<h1>Test Email</h1><p>Your email configuration is working correctly!</p>",
        body_text="Test Email - Your email configuration is working correctly!"
    )
    
    if success:
        return {"message": f"Test email sent to {config['recipients']}"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send test email. Check server logs.")
