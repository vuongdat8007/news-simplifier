import streamlit as st
import requests
import dateutil.parser
import html as html_module

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="AI News Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- AI Assistant UI Theme ---
st.markdown("""
<style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Global Styles */
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Dark sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    }
    
    [data-testid="stSidebar"] * {
        color: #e8e8e8 !important;
    }
    
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3 {
        color: #ffffff !important;
    }
    
    [data-testid="stSidebar"] .stMarkdown p {
        color: #b8b8b8 !important;
    }
    
    /* Main content area */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    
    /* AI Chat bubble style for messages */
    .ai-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.25rem 1.5rem;
        border-radius: 18px 18px 18px 4px;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        max-width: 85%;
    }
    
    .user-message {
        background: #f0f2f5;
        color: #1a1a1a;
        padding: 1.25rem 1.5rem;
        border-radius: 18px 18px 4px 18px;
        margin: 1rem 0 1rem auto;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        max-width: 85%;
    }
    
    /* News cards with modern feel */
    .news-card {
        background: white;
        padding: 1.5rem;
        border-radius: 16px;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
        margin-bottom: 1rem;
        border: 1px solid #e8e8e8;
        transition: all 0.3s ease;
    }
    
    .news-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
        border-color: #667eea;
    }
    
    /* Source tag styling */
    .source-tag {
        display: inline-block;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.75rem;
    }
    
    .news-title {
        color: #1a1a1a;
        font-weight: 600;
        font-size: 1.1rem;
        line-height: 1.4;
        margin-bottom: 0.5rem;
    }
    
    .news-summary {
        color: #5a5a5a;
        line-height: 1.6;
        font-size: 0.95rem;
    }
    
    /* Primary buttons - AI style */
    div.stButton > button[kind="primary"],
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px;
        padding: 0.6rem 1.5rem;
        font-weight: 600;
        font-size: 0.9rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    div.stButton > button[kind="primary"]:hover,
    div.stButton > button:first-child:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
        color: white !important;
    }
    
    /* Sidebar buttons specifically */
    [data-testid="stSidebar"] div.stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
    }
    
    [data-testid="stSidebar"] div.stButton > button:hover {
        color: white !important;
    }
    
    /* Secondary buttons */
    div.stButton > button[kind="secondary"] {
        background: #f0f2f5;
        color: #1a1a1a;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: #f8f9fa;
        border-radius: 12px;
        font-weight: 500;
    }
    
    /* Text areas */
    .stTextArea textarea {
        border-radius: 12px;
        border: 2px solid #e0e0e0;
        font-family: 'Inter', sans-serif;
    }
    
    .stTextArea textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.15);
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
        color: #667eea;
    }
    
    /* Headers */
    h1 {
        font-weight: 700;
        color: #1a1a1a;
    }
    
    h2, h3 {
        font-weight: 600;
        color: #2a2a2a;
    }
    
    /* Simplified box - AI response style */
    .simplified-box {
        background: linear-gradient(135deg, #f0f4ff 0%, #f5f0ff 100%);
        border-left: 4px solid #667eea;
        padding: 1.25rem;
        border-radius: 0 12px 12px 0;
        margin-top: 1rem;
    }
    
    /* Stat cards */
    .stat-card {
        background: white;
        padding: 1.5rem;
        border-radius: 16px;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
        text-align: center;
        border: 1px solid #e8e8e8;
    }
    
    .stat-number {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0;
    }
    
    .stat-label {
        font-size: 0.85rem;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin: 0.5rem 0 0 0;
        font-weight: 500;
    }
    
    /* Audio player */
    audio {
        border-radius: 12px;
        width: 100%;
    }
    
    /* Download buttons */
    .stDownloadButton button {
        background: #f0f2f5;
        color: #1a1a1a;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
    }
    
    .stDownloadButton button:hover {
        background: #e8e8e8;
        border-color: #667eea;
    }
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: #667eea !important;
    }
</style>
""", unsafe_allow_html=True)

# --- App Logic ---

def fetch_news(categories=None):
    """Fetch news, optionally filtered by categories."""
    try:
        url = f"{API_URL}/news"
        if categories:
            url += f"?categories={','.join(categories)}"
        response = requests.get(url)
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
    # AI Assistant Header
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0;">
        <div style="font-size: 3rem; margin-bottom: 0.5rem;">🤖</div>
        <h1 style="margin: 0; font-size: 1.4rem; font-weight: 700;">AI News Assistant</h1>
        <p style="margin: 0.5rem 0 0 0; font-size: 0.85rem; opacity: 0.7;">Your intelligent news curator</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Status indicator
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 0.5rem; padding: 0.75rem; background: rgba(102, 126, 234, 0.15); border-radius: 12px; margin-bottom: 1rem;">
        <div style="width: 8px; height: 8px; background: #10b981; border-radius: 50%; animation: pulse 2s infinite;"></div>
        <span style="font-size: 0.8rem;">Online & Ready</span>
    </div>
    <style>
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
    </style>
    """, unsafe_allow_html=True)
    
    # --- Category Selection ---
    st.markdown("### 🏷️ Categories")
    
    # Define available categories
    CATEGORIES = {
        "top_stories": "📰 Top Stories",
        "world": "🌍 World",
        "nation": "🇺🇸 U.S.",
        "business": "💼 Business",
        "technology": "💻 Technology",
        "entertainment": "🎬 Entertainment",
        "sports": "⚽ Sports",
        "science": "🔬 Science",
        "health": "🏥 Health"
    }
    
    # Initialize selected categories in session state
    if 'selected_categories' not in st.session_state:
        st.session_state.selected_categories = ["top_stories", "technology", "business"]
    
    # Category multiselect
    selected = st.multiselect(
        "Select news categories",
        options=list(CATEGORIES.keys()),
        default=st.session_state.selected_categories,
        format_func=lambda x: CATEGORIES[x],
        label_visibility="collapsed"
    )
    
    # Update session state
    st.session_state.selected_categories = selected
    
    # Refresh news button
    if st.button("🔄 Refresh News", key="refresh_categories", use_container_width=True):
        # Clear existing news data to force refetch
        if 'news_data' in st.session_state:
            del st.session_state['news_data']
        st.rerun()
    
    st.markdown("---")
    
    # Daily Digest Section
    st.markdown("### 📋 AI Digest")
    st.caption("Generate an AI-powered news summary")
    
    if st.button("✨ Generate Digest", key="generate_digest", use_container_width=True):
        with st.spinner("AI is analyzing today's news..."):
            digest = fetch_digest()
            if digest:
                st.session_state['digest'] = digest
                st.success(f"✅ Ready! ({digest.get('article_count', 0)} articles)")
    
    # Show download buttons if digest exists
    if 'digest' in st.session_state:
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📄 PDF", key="download_pdf", use_container_width=True):
                with st.spinner("Creating PDF..."):
                    pdf_data = fetch_pdf()
                    if pdf_data:
                        st.session_state['pdf_data'] = pdf_data
        
        with col2:
            if st.button("🔊 Audio", key="generate_audio", use_container_width=True):
                with st.spinner("Generating voice..."):
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
    
    # Combined Raw News Section
    st.markdown("### 📰 Raw Data")
    st.caption("Access the source content")
    
    if st.button("👁️ View Source Data", key="view_raw", use_container_width=True):
        st.session_state['show_raw_news'] = True
    
    st.markdown("---")
    
    # About section with AI branding
    st.markdown("""
    <div style="padding: 1rem; background: rgba(255,255,255,0.05); border-radius: 12px; font-size: 0.8rem;">
        <p style="margin: 0 0 0.75rem 0; font-weight: 600;">About</p>
        <p style="margin: 0; opacity: 0.8; line-height: 1.5;">
            Powered by GPT-4o-mini, this assistant curates and simplifies news from top sources.
        </p>
    </div>
    """, unsafe_allow_html=True)


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

# --- Display Combined Raw News if requested ---
if st.session_state.get('show_raw_news', False):
    # Beautiful header with gradient
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); padding: 2rem; border-radius: 16px; margin-bottom: 1.5rem; box-shadow: 0 10px 40px rgba(0,0,0,0.15);">
        <h2 style="color: white; margin: 0; font-weight: 700; font-size: 1.8rem;">📄 Combined Raw News Content</h2>
        <p style="color: rgba(255,255,255,0.8); margin: 0.5rem 0 0 0; font-size: 1rem;">Raw content from RSS feeds and article scraping</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Refresh button to force re-fetch
    col_refresh, col_spacer = st.columns([1, 3])
    with col_refresh:
        if st.button("🔄 Refresh News Data", use_container_width=True):
            categories = st.session_state.get('selected_categories', ["top_stories", "technology", "business"])
            with st.spinner("Fetching fresh news data..."):
                st.session_state.news_data = fetch_news(categories)
                st.rerun()
    
    # Fetch news if not already fetched
    if 'news_data' not in st.session_state:
        categories = st.session_state.get('selected_categories', ["top_stories", "technology", "business"])
        with st.spinner("Fetching news..."):
            st.session_state.news_data = fetch_news(categories)
    
    if st.session_state.news_data:
        # Build combined content for download
        combined_content = []
        for idx, article in enumerate(st.session_state.news_data, 1):
            content = article.get('content')
            title = article.get('title', 'Untitled')
            source = article.get('source', 'Unknown')
            
            article_section = f"--- ARTICLE {idx}: {title} ({source}) ---\n"
            if content:
                article_section += content
            else:
                article_section += "[Content not available - scraping failed]"
            article_section += "\n\n"
            combined_content.append(article_section)
        
        full_combined = "\n".join(combined_content)
        articles_with_content = sum(1 for a in st.session_state.news_data if a.get('content'))
        total_chars = sum(len(a.get('content') or '') for a in st.session_state.news_data)
        
        # Stats cards with beautiful styling
        st.markdown("""
        <style>
            .stat-card {
                background: white;
                padding: 1.2rem;
                border-radius: 12px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.08);
                text-align: center;
                border: 1px solid #eee;
            }
            .stat-number {
                font-size: 2rem;
                font-weight: 700;
                color: #1e3c72;
                margin: 0;
            }
            .stat-label {
                font-size: 0.85rem;
                color: #666;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                margin: 0;
            }
        </style>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div class="stat-card">
                <p class="stat-number">{len(st.session_state.news_data)}</p>
                <p class="stat-label">Total Articles</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="stat-card">
                <p class="stat-number">{articles_with_content}</p>
                <p class="stat-label">Successfully Scraped</p>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="stat-card">
                <p class="stat-number">{total_chars:,}</p>
                <p class="stat-label">Total Characters</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Single combined content display
        st.markdown("""
        <div style="background: white; border-radius: 12px; padding: 1.5rem; box-shadow: 0 4px 15px rgba(0,0,0,0.08); margin-bottom: 1rem;">
            <h3 style="margin: 0 0 1rem 0; color: #1a1a1a;">📰 All RSS Excerpts Combined</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Build combined content from RSS excerpts
        clean_combined = []
        for idx, article in enumerate(st.session_state.news_data, 1):
            title = article.get('title', 'Untitled')
            source = article.get('source', 'Unknown')
            summary = article.get('summary', '')
            
            section = f"{'='*60}\n"
            section += f"ARTICLE {idx}: {title}\n"
            section += f"Source: {source}\n"
            section += f"{'='*60}\n\n"
            
            # Clean the RSS summary (remove HTML tags if any)
            if summary:
                from bs4 import BeautifulSoup
                clean_summary = BeautifulSoup(summary, 'html.parser').get_text(separator=' ', strip=True)
                section += clean_summary
            else:
                section += "[No excerpt available]"
            
            section += "\n\n"
            clean_combined.append(section)
        
        all_content = "\n".join(clean_combined)
        
        # Display in a large text area
        st.text_area(
            "Combined RSS Excerpts",
            all_content,
            height=500,
            label_visibility="collapsed"
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Summarize button
        if st.button("🤖 Summarize with GPT-4o-mini", use_container_width=True, type="primary"):
            with st.spinner("Generating summary with GPT-4o-mini..."):
                try:
                    response = requests.post(f"{API_URL}/summarize-combined", json={"text": all_content})
                    if response.status_code == 200:
                        st.session_state['gpt_summary'] = response.json().get('summary', 'No summary generated')
                    else:
                        st.error(f"Error: {response.json().get('detail', 'Failed to generate summary')}")
                except Exception as e:
                    st.error(f"Error connecting to backend: {e}")
        
        # Display summary if available
        if 'gpt_summary' in st.session_state:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1.5rem; border-radius: 12px; margin: 1rem 0;">
                <h4 style="color: white; margin: 0 0 1rem 0;">🤖 GPT-4o-mini Summary</h4>
                <div style="background: white; padding: 1rem; border-radius: 8px; line-height: 1.6;">
            """, unsafe_allow_html=True)
            st.write(st.session_state['gpt_summary'])
            st.markdown("</div></div>", unsafe_allow_html=True)
            
            # Export buttons for summary
            st.markdown("#### Export Summary")
            col_pdf, col_audio = st.columns(2)
            
            with col_pdf:
                if st.button("📄 Download as PDF", use_container_width=True):
                    with st.spinner("Generating PDF..."):
                        try:
                            response = requests.post(
                                f"{API_URL}/summary/pdf", 
                                json={"text": st.session_state['gpt_summary']}
                            )
                            if response.status_code == 200:
                                st.session_state['summary_pdf'] = response.content
                            else:
                                st.error("Failed to generate PDF")
                        except Exception as e:
                            st.error(f"Error: {e}")
                
                if 'summary_pdf' in st.session_state:
                    st.download_button(
                        label="⬇️ Save PDF",
                        data=st.session_state['summary_pdf'],
                        file_name="news_summary.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
            
            with col_audio:
                if st.button("🔊 Generate Audio (OpenAI TTS)", use_container_width=True):
                    with st.spinner("Generating audio with OpenAI TTS..."):
                        try:
                            response = requests.post(
                                f"{API_URL}/summary/audio", 
                                json={"text": st.session_state['gpt_summary']},
                                timeout=60
                            )
                            if response.status_code == 200:
                                audio_content = response.content
                                # Validate audio content
                                if audio_content and len(audio_content) > 1000:
                                    st.session_state['summary_audio'] = audio_content
                                    st.success(f"✅ Audio generated ({len(audio_content):,} bytes)")
                                else:
                                    st.error(f"Audio content too small ({len(audio_content)} bytes)")
                            else:
                                error_detail = response.text[:200] if response.text else "Unknown error"
                                st.error(f"Failed to generate audio: {error_detail}")
                        except requests.exceptions.Timeout:
                            st.error("Request timed out. Try a shorter summary.")
                        except Exception as e:
                            st.error(f"Error: {e}")
                
                if 'summary_audio' in st.session_state and st.session_state['summary_audio']:
                    st.audio(st.session_state['summary_audio'], format='audio/mpeg')
                    st.download_button(
                        label="⬇️ Save Audio",
                        data=st.session_state['summary_audio'],
                        file_name="news_summary.mp3",
                        mime="audio/mpeg",
                        use_container_width=True
                    )
            
            # Email delivery section
            st.markdown("---")
            st.markdown("#### 📧 Send to Email")
            
            col_email, col_send = st.columns([3, 1])
            
            with col_email:
                email_input = st.text_input(
                    "Recipient email",
                    placeholder="Enter your email address",
                    label_visibility="collapsed",
                    key="email_input"
                )
            
            with col_send:
                if st.button("📧 Send", use_container_width=True):
                    if not email_input or "@" not in email_input:
                        st.error("Please enter a valid email address")
                    else:
                        with st.spinner("Generating PDF & audio, sending email..."):
                            try:
                                response = requests.post(
                                    f"{API_URL}/send-summary-email",
                                    json={
                                        "email": email_input,
                                        "summary": st.session_state['gpt_summary']
                                    },
                                    timeout=120
                                )
                                if response.status_code == 200:
                                    result = response.json()
                                    st.success(f"✅ {result.get('message', 'Email sent!')}")
                                else:
                                    error = response.json().get('detail', 'Failed to send email')
                                    st.error(f"❌ {error}")
                            except requests.exceptions.Timeout:
                                st.error("Request timed out. Please try again.")
                            except Exception as e:
                                st.error(f"Error: {e}")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Action buttons row
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="⬇️ Download All Raw Content",
                data=all_content,
                file_name="combined_raw_news.txt",
                mime="text/plain",
                use_container_width=True
            )
        with col2:
            if st.button("❌ Close Raw News View", use_container_width=True):
                st.session_state['show_raw_news'] = False
                # Clean up all session state
                for key in ['gpt_summary', 'summary_pdf', 'summary_audio']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
    else:
        st.info("No news data available. Please wait for news to load.")
    
    st.markdown("---")

# --- Main Header ---
st.markdown("""
<div style="margin-bottom: 2rem;">
    <h1 style="margin: 0; font-size: 2rem;">👋 Welcome back!</h1>
    <p style="color: #666; margin: 0.5rem 0 0 0; font-size: 1.1rem;">Here's what's happening in the news today</p>
</div>
""", unsafe_allow_html=True)

if 'news_data' not in st.session_state:
    # Get selected categories from session state or use defaults
    categories = st.session_state.get('selected_categories', ["top_stories", "technology", "business"])
    with st.spinner("🔍 Scanning news sources..."):
        st.session_state.news_data = fetch_news(categories)

if not st.session_state.news_data:
    st.markdown("""
    <div class="ai-message">
        <p style="margin: 0;">I couldn't find any news articles. Please make sure the backend server is running on port 8000.</p>
    </div>
    """, unsafe_allow_html=True)

# News count indicator
if st.session_state.news_data:
    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1.5rem;">
        <span style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 0.35rem 0.75rem; border-radius: 20px; font-size: 0.8rem; font-weight: 600;">
            {len(st.session_state.news_data)} articles
        </span>
        <span style="color: #888; font-size: 0.85rem;">from your subscribed sources</span>
    </div>
    """, unsafe_allow_html=True)

for idx, article in enumerate(st.session_state.news_data):
    # Card Container
    with st.container():
        # Clean HTML from summary
        from bs4 import BeautifulSoup
        raw_summary = article.get('summary', 'No summary')
        clean_summary = BeautifulSoup(raw_summary, 'html.parser').get_text(separator=' ', strip=True)
        display_summary = clean_summary[:200] + '...' if len(clean_summary) > 200 else clean_summary
        
        st.markdown(f"""
        <div class="news-card">
            <span class="source-tag">{html_module.escape(article['source'])}</span>
            <h3 class="news-title">{html_module.escape(article['title'])}</h3>
            <p class="news-summary">{html_module.escape(display_summary)}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Expandable section to view raw news data
        with st.expander("📋 View Raw News Data"):
            st.markdown("**Source:**")
            st.code(article.get('source', 'N/A'), language=None)
            
            st.markdown("**Published:**")
            st.code(article.get('published', 'N/A'), language=None)
            
            st.markdown("**Link:**")
            st.code(article.get('link', 'N/A'), language=None)
            
            st.markdown("**RSS Summary:**")
            st.code(article.get('summary', 'N/A'), language=None)
            
            st.markdown("**Full Scraped Content:**")
            content = article.get('content')
            if content:
                st.code(content, language=None)
            else:
                st.info("No full content available (scraping may have failed for this article)")
        
        st.markdown("---")
