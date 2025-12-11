from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from services.news_fetcher import fetch_news
from services.simplifier import simplify_text
from io import BytesIO

app = FastAPI(title="News Simplifier API")

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
def get_news():
    news = fetch_news()
    return {"news": news}

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
