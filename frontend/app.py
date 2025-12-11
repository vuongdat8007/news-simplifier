import streamlit as st
import requests
import dateutil.parser

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="News Simplifier",
    page_icon="📰",
    layout="wide"
)

# --- Custom CSS for "Premium" Feel ---
st.markdown("""
<style>
    .reportview-container {
        background: #f0f2f6;
    }
    .main > div {
        padding-top: 2rem;
    }
    .news-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
        transition: transform 0.2s;
    }
    .news-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 15px rgba(0, 0, 0, 0.1);
    }
    .source-tag {
        font-size: 0.8rem;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 600;
        margin-bottom: 0.5rem;
        display: block;
    }
    .news-title {
        color: #1a1a1a;
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 700;
        margin-bottom: 0.8rem;
    }
    .news-summary {
        color: #4a4a4a;
        line-height: 1.6;
        margin-bottom: 1rem;
    }
    div.stButton > button:first-child {
        background-color: #000;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: background-color 0.2s;
    }
    div.stButton > button:first-child:hover {
        background-color: #333;
        color: white;
    }
    .simplified-box {
        background-color: #e3f2fd;
        border-left: 5px solid #2196f3;
        padding: 1rem;
        border-radius: 4px;
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# --- App Logic ---

def fetch_news():
    try:
        response = requests.get(f"{API_URL}/news")
        if response.status_code == 200:
            return response.json().get("news", [])
        else:
            st.error("Failed to fetch news.")
            return []
    except Exception as e:
        st.error(f"Error connecting to backend: {e}")
        return []

def simplify_article(text):
    try:
        response = requests.post(f"{API_URL}/simplify", json={"text": text})
        if response.status_code == 200:
            return response.json().get("simplified", "Could not simplify.")
        else:
            return "Error during simplification."
    except Exception as e:
        return f"Error connecting to backend: {e}"

def fetch_digest():
    """Fetch the generated news digest from the API."""
    try:
        response = requests.get(f"{API_URL}/digest")
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Failed to generate digest.")
            return None
    except Exception as e:
        st.error(f"Error connecting to backend: {e}")
        return None

def fetch_pdf():
    """Fetch the PDF digest from the API."""
    try:
        response = requests.get(f"{API_URL}/digest/pdf")
        if response.status_code == 200:
            return response.content
        else:
            st.error("Failed to generate PDF.")
            return None
    except Exception as e:
        st.error(f"Error connecting to backend: {e}")
        return None

def fetch_audio():
    """Fetch the audio digest from the API."""
    try:
        response = requests.get(f"{API_URL}/digest/audio")
        if response.status_code == 200:
            return response.content
        else:
            st.error("Failed to generate audio.")
            return None
    except Exception as e:
        st.error(f"Error connecting to backend: {e}")
        return None

# --- UI ---

with st.sidebar:
    st.title("📰 News Simplifier")
    st.markdown("---")
    
    # Daily Digest Section
    st.subheader("📋 Daily Digest")
    st.caption("Get all news summarized into one page")
    
    if st.button("🔄 Generate Digest", key="generate_digest", use_container_width=True):
        with st.spinner("Creating your personalized digest..."):
            digest = fetch_digest()
            if digest:
                st.session_state['digest'] = digest
                st.success(f"✅ Digest ready! ({digest.get('article_count', 0)} articles)")
    
    # Show download buttons if digest exists
    if 'digest' in st.session_state:
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📄 PDF", key="download_pdf", use_container_width=True):
                with st.spinner("Generating PDF..."):
                    pdf_data = fetch_pdf()
                    if pdf_data:
                        st.session_state['pdf_data'] = pdf_data
        
        with col2:
            if st.button("🔊 Audio", key="generate_audio", use_container_width=True):
                with st.spinner("Generating audio..."):
                    audio_data = fetch_audio()
                    if audio_data:
                        st.session_state['audio_data'] = audio_data
        
        # PDF Download button
        if 'pdf_data' in st.session_state:
            st.download_button(
                label="⬇️ Download PDF",
                data=st.session_state['pdf_data'],
                file_name="news_digest.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        
        # Audio player
        if 'audio_data' in st.session_state:
            st.audio(st.session_state['audio_data'], format='audio/mp3')
    
    st.markdown("---")
    st.markdown("""
    **About**
    
    This app aggregates news from top sources and uses AI to simplify complex articles into easy-to-read summaries.
    
    **Tech Stack**
    - Python (FastAPI)
    - Streamlit
    - OpenAI GPT
    - gTTS
    """)

# --- Display Digest if Generated ---
if 'digest' in st.session_state:
    st.markdown("## 📋 Your Daily Digest")
    
    digest_data = st.session_state['digest']
    
    # Metadata
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📰 Articles", digest_data.get('article_count', 0))
    with col2:
        st.metric("📍 Sources", len(digest_data.get('sources', [])))
    with col3:
        generated_at = digest_data.get('generated_at', '')
        if generated_at:
            # Simple date formatting
            st.metric("🕐 Generated", generated_at.split('T')[0] if 'T' in generated_at else generated_at[:10])
    
    # Digest content in styled box
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 12px; margin: 1rem 0;">
        <div style="background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
    """, unsafe_allow_html=True)
    
    st.markdown(digest_data.get('digest', 'No digest content available.'))
    
    st.markdown("</div></div>", unsafe_allow_html=True)
    
    st.markdown("---")

st.title("Latest Headlines")

if 'news_data' not in st.session_state:
    with st.spinner("Fetching latest news..."):
        st.session_state.news_data = fetch_news()

if not st.session_state.news_data:
    st.info("No news found. Ensure backend is running.")

for idx, article in enumerate(st.session_state.news_data):
    # Card Container
    with st.container():
        st.markdown(f"""
        <div class="news-card">
            <span class="source-tag">{article['source']} • {article['published']}</span>
            <h3 class="news-title">{article['title']}</h3>
            <p class="news-summary">{article['summary']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 5])
        
        with col1:
            if st.button(f"Simplify ✨", key=f"btn_{idx}"):
                with st.spinner("Simplifying..."):
                    summary = simplify_article(article['summary'])
                    st.session_state[f"simplified_{idx}"] = summary
        
        with col2:
            st.markdown(f"[Read Full Story]({article['link']})")

        # Display Simplified Text if it exists in session state
        if f"simplified_{idx}" in st.session_state:
            st.markdown(f"""
            <div class="simplified-box">
                <strong>🤖 Simple Summary:</strong><br>
                {st.session_state[f"simplified_{idx}"]}
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
