import streamlit as st
import requests
import dateutil.parser
import html as html_module
import os

# API URL - uses environment variable in Docker, localhost for local dev
API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="AI News Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# --- AI Assistant UI Theme ---
st.markdown("""
<style>
    /* Hide Streamlit hamburger menu, deploy button, header toolbar, and footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none !important;}
    header[data-testid="stHeader"] {display: none !important;}
    [data-testid="stToolbar"] {display: none !important;}
    
    /* Make sure sidebar collapse button is always visible */
    [data-testid="stSidebarCollapsedControl"] {
        visibility: visible !important;
        display: flex !important;
    }
    
    /* Style the collapse button to be more visible */
    [data-testid="stSidebarCollapsedControl"] button {
        background-color: #1a1a2e !important;
        border: none !important;
        padding: 0.5rem !important;
        border-radius: 0 8px 8px 0 !important;
    }
    
    [data-testid="stSidebarCollapsedControl"] button svg {
        fill: white !important;
    }
    
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Global Styles */
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Sidebar base styles - light by default */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }
    
    [data-testid="stSidebar"] * {
        color: #1a1a1a !important;
    }
    
    /* Sidebar selectbox styling */
    [data-testid="stSidebar"] .stSelectbox [data-baseweb="select"],
    [data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] > div,
    [data-testid="stSidebar"] .stSelectbox [role="combobox"] {
        background-color: #ffffff !important;
        background: #ffffff !important;
        border: 1px solid #dee2e6 !important;
    }
    
    [data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] span,
    [data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] div,
    [data-testid="stSidebar"] .stSelectbox [role="combobox"],
    [data-testid="stSidebar"] .stSelectbox [role="combobox"] * {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
    }
    
    [data-testid="stSidebar"] .stSelectbox label {
        color: #1a1a1a !important;
        -webkit-text-fill-color: #1a1a1a !important;
    }
    
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3 {
        color: #1a1a1a !important;
    }
    
    [data-testid="stSidebar"] .stMarkdown p {
        color: #495057 !important;
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
    
    /* Sidebar buttons - light theme by default */
    [data-testid="stSidebar"] div.stButton > button {
        background: #ffffff !important;
        color: #1a1a1a !important;
        border: 1px solid #dee2e6 !important;
        border-radius: 12px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
    }
    
    [data-testid="stSidebar"] div.stButton > button:hover {
        background: #f8f9fa !important;
        color: #1a1a1a !important;
        border-color: #667eea !important;
    }
    
    /* Secondary buttons */
    div.stButton > button[kind="secondary"] {
        background: #f0f2f5;
        color: #1a1a1a;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
    }
    
    /* Multiselect pills - subtle styling */
    [data-baseweb="tag"] {
        background-color: #e8e4f0 !important;
        border-color: #d0c8e0 !important;
        border-radius: 16px !important;
    }
    
    [data-baseweb="tag"] span {
        color: #4a4a6a !important;
    }
    
    [data-baseweb="tag"] svg {
        fill: #6a6a8a !important;
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
    
    /* Login card */
    .login-card {
        background: white;
        padding: 2.5rem;
        border-radius: 16px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        max-width: 400px;
        margin: 2rem auto;
    }
    
    .login-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .login-header h1 {
        font-size: 2rem;
        margin: 0;
    }
</style>
""", unsafe_allow_html=True)


# --- Authentication Functions ---

def auth_login(email: str, password: str):
    """Login user and store token in session and cookies."""
    try:
        response = requests.post(
            f"{API_URL}/auth/login",
            json={"email": email, "password": password}
        )
        if response.status_code == 200:
            data = response.json()
            st.session_state['auth_token'] = data['access_token']
            st.session_state['user_email'] = data['email']
            st.session_state['user_id'] = data['user_id']
            return True, "Login successful!"
        else:
            error = response.json().get('detail', 'Login failed')
            return False, error
    except Exception as e:
        return False, str(e)


def auth_register(email: str, password: str):
    """Register new user and store token in session."""
    try:
        response = requests.post(
            f"{API_URL}/auth/register",
            json={"email": email, "password": password}
        )
        if response.status_code == 200:
            data = response.json()
            st.session_state['auth_token'] = data['access_token']
            st.session_state['user_email'] = data['email']
            st.session_state['user_id'] = data['user_id']
            return True, "Account created successfully!"
        else:
            error = response.json().get('detail', 'Registration failed')
            return False, error
    except Exception as e:
        return False, str(e)


def auth_logout():
    """Clear authentication from session."""
    for key in ['auth_token', 'user_email', 'user_id', 'news_data', 'digest', 'is_premium', 'is_admin', 'user_theme']:
        if key in st.session_state:
            del st.session_state[key]


def is_authenticated():
    """Check if user is authenticated."""
    return 'auth_token' in st.session_state and st.session_state['auth_token']


def get_auth_header():
    """Get authorization header for API requests."""
    if 'auth_token' in st.session_state:
        return {"Authorization": f"Bearer {st.session_state['auth_token']}"}
    return {}


def fetch_user_settings():
    """Fetch user settings from API."""
    try:
        response = requests.get(
            f"{API_URL}/settings/",
            headers=get_auth_header()
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error fetching settings: {e}")
    return None


def save_user_settings(settings: dict):
    """Save user settings to API."""
    try:
        response = requests.put(
            f"{API_URL}/settings/",
            headers=get_auth_header(),
            json=settings
        )
        return response.status_code == 200
    except Exception as e:
        print(f"Error saving settings: {e}")
    return False


def check_premium_status():
    """Check if current user has premium access."""
    try:
        response = requests.get(
            f"{API_URL}/check-premium",
            headers=get_auth_header()
        )
        if response.status_code == 200:
            data = response.json()
            st.session_state['is_premium'] = data.get('is_premium', False)
            st.session_state['is_admin'] = data.get('is_admin', False)
            return data
    except Exception as e:
        print(f"Error checking premium: {e}")
    return {"is_premium": False, "is_admin": False}


# --- Login/Register UI ---

if not is_authenticated():
    # Show login/register page - centered narrow card
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 2rem 0 1.5rem 0;">
            <div style="font-size: 4rem; margin-bottom: 0.5rem;">🤖</div>
            <h1 style="margin: 0; font-size: 1.8rem; font-weight: 700; color: #1a1a2e;">AI News Assistant</h1>
            <p style="color: #666; margin-top: 0.5rem; font-size: 0.95rem;">Sign in to access your personalized news digest</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Tabs for login/register
        tab_login, tab_register = st.tabs(["🔐 Login", "📝 Register"])
        
        with tab_login:
            with st.form("login_form"):
                st.markdown("<p style='font-weight: 600; margin-bottom: 0.5rem;'>Email</p>", unsafe_allow_html=True)
                login_email = st.text_input("Email", key="login_email", placeholder="your@email.com", label_visibility="collapsed")
                st.markdown("<p style='font-weight: 600; margin-bottom: 0.5rem; margin-top: 1rem;'>Password</p>", unsafe_allow_html=True)
                login_password = st.text_input("Password", type="password", key="login_password", label_visibility="collapsed")
                st.markdown("<br>", unsafe_allow_html=True)
                login_submit = st.form_submit_button("Sign In", use_container_width=True)
                
                if login_submit:
                    if login_email and login_password:
                        success, message = auth_login(login_email, login_password)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    else:
                        st.warning("Please enter email and password")
        
        with tab_register:
            with st.form("register_form"):
                st.markdown("<p style='font-weight: 600; margin-bottom: 0.5rem;'>Email</p>", unsafe_allow_html=True)
                reg_email = st.text_input("Email", key="reg_email", placeholder="your@email.com", label_visibility="collapsed")
                st.markdown("<p style='font-weight: 600; margin-bottom: 0.5rem; margin-top: 1rem;'>Password</p>", unsafe_allow_html=True)
                reg_password = st.text_input("Password", type="password", key="reg_password", label_visibility="collapsed")
                st.markdown("<p style='font-weight: 600; margin-bottom: 0.5rem; margin-top: 1rem;'>Confirm Password</p>", unsafe_allow_html=True)
                reg_confirm = st.text_input("Confirm Password", type="password", key="reg_confirm", label_visibility="collapsed")
                st.markdown("<br>", unsafe_allow_html=True)
                reg_submit = st.form_submit_button("Create Account", use_container_width=True)
                
                if reg_submit:
                    if not reg_email or not reg_password:
                        st.warning("Please fill in all fields")
                    elif reg_password != reg_confirm:
                        st.error("Passwords do not match")
                    elif len(reg_password) < 6:
                        st.error("Password must be at least 6 characters")
                    else:
                        success, message = auth_register(reg_email, reg_password)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
    
    # Stop execution here - don't show main app
    st.stop()


# --- Main App (only shown when authenticated) ---

# Check premium status on every page load (to pick up manual Firebase changes)
check_premium_status()

# Load theme from user settings
if 'user_theme' not in st.session_state:
    user_settings = fetch_user_settings()
    if user_settings and 'theme' in user_settings:
        st.session_state['user_theme'] = user_settings['theme']
    else:
        st.session_state['user_theme'] = 'light'

# Apply dark theme CSS if selected
if st.session_state.get('user_theme') == 'dark':
    st.markdown("""
    <style>
        /* Dark theme overrides */
        .stApp {
            background-color: #0e1117 !important;
            color: #fafafa !important;
        }
        
        .main .block-container {
            background-color: #0e1117 !important;
        }
        
        h1, h2, h3, h4, h5, h6 {
            color: #fafafa !important;
        }
        
        p, span, label, .stMarkdown {
            color: #c8c8c8 !important;
        }
        
        /* Dark cards */
        .news-card {
            background: #1a1a2e !important;
            border-color: #2a2a4e !important;
        }
        
        .news-card:hover {
            border-color: #667eea !important;
        }
        
        .news-title {
            color: #fafafa !important;
        }
        
        .news-summary {
            color: #b8b8b8 !important;
        }
        
        /* Dark inputs */
        .stTextInput input, .stTextArea textarea, .stSelectbox > div > div {
            background-color: #1a1a2e !important;
            color: #fafafa !important;
            border-color: #2a2a4e !important;
        }
        
        /* Dark expander */
        .streamlit-expanderHeader {
            background: #1a1a2e !important;
            color: #fafafa !important;
        }
        
        /* Dark metrics */
        [data-testid="stMetricLabel"] {
            color: #b8b8b8 !important;
        }
        
        /* Dark sidebar */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%) !important;
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
        
        [data-testid="stSidebar"] .stSelectbox label {
            color: #e8e8e8 !important;
            -webkit-text-fill-color: #e8e8e8 !important;
        }
        
        /* Dark sidebar buttons */
        [data-testid="stSidebar"] div.stButton > button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            color: white !important;
            border: none !important;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }
        
        [data-testid="stSidebar"] div.stButton > button:hover {
            background: linear-gradient(135deg, #7b8eee 0%, #8a5fb8 100%) !important;
            color: white !important;
        }
        
        /* Dark sidebar multiselect */
        [data-testid="stSidebar"] [data-baseweb="tag"] {
            background-color: #3a3a5e !important;
            border-color: #4a4a7e !important;
        }
        
        [data-testid="stSidebar"] [data-baseweb="tag"] span {
            color: #e0e0e0 !important;
        }
        
        [data-testid="stSidebar"] [data-baseweb="tag"] svg {
            fill: #c0c0c0 !important;
        }
        
        /* Dark sidebar multiselect input */
        [data-testid="stSidebar"] [data-baseweb="select"] {
            background-color: #2a2a4e !important;
            border-color: #3a3a6e !important;
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
    
    # User info and logout
    st.markdown(f"""
    <div style="background: rgba(255,255,255,0.1); padding: 0.75rem 1rem; border-radius: 8px; margin-bottom: 1rem;">
        <p style="margin: 0; font-size: 0.85rem;">👤 Logged in as:</p>
        <p style="margin: 0.25rem 0 0 0; font-weight: 600; font-size: 0.9rem;">{st.session_state.get('user_email', 'Unknown')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚪 Logout", key="logout_btn", use_container_width=True):
        auth_logout()
        st.rerun()
    
    # Theme toggle
    current_theme = st.session_state.get('user_theme', 'light')
    theme_options = {"🌞 Light": "light", "🌙 Dark": "dark"}
    theme_labels = {"light": "🌞 Light", "dark": "🌙 Dark"}
    
    selected_theme_label = st.selectbox(
        "Theme",
        options=list(theme_options.keys()),
        index=0 if current_theme == "light" else 1,
        key="theme_selector"
    )
    
    selected_theme = theme_options[selected_theme_label]
    if selected_theme != st.session_state.get('user_theme', 'light'):
        st.session_state['user_theme'] = selected_theme
        save_user_settings({"theme": selected_theme})
        st.rerun()
    
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
    
    st.markdown("---")
    
    # --- Admin Panel (only for admins) ---
    if st.session_state.get('is_admin', False):
        st.markdown("### 🛠️ Admin Panel")
        
        # Fetch users list
        try:
            response = requests.get(
                f"{API_URL}/admin/users",
                headers=get_auth_header()
            )
            if response.status_code == 200:
                users_data = response.json()
                users = users_data.get('users', [])
                
                if users:
                    st.caption(f"{len(users)} registered users")
                    
                    for user in users:
                        user_id = user['id']
                        email = user['email']
                        is_me = email == st.session_state.get('user_email')
                        
                        # Build badges
                        badges = ""
                        if user['is_admin']:
                            badges += "👑"
                        if user['is_premium']:
                            badges += "⭐"
                        
                        # Display user row with custom HTML
                        email_display = email if len(email) <= 25 else email[:22] + "..."
                        st.markdown(f"""
                        <div style="display: flex; align-items: center; padding: 0.5rem 0; border-bottom: 1px solid rgba(255,255,255,0.1);">
                            <span style="font-size: 0.9rem;">{badges}</span>
                            <span style="flex: 1; margin-left: 0.5rem; font-size: 0.85rem; overflow: hidden; text-overflow: ellipsis;" title="{email}">{email_display}</span>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Action buttons in a row
                        if not is_me:
                            col1, col2 = st.columns(2)
                            with col1:
                                premium_label = "⭐ Remove" if user['is_premium'] else "☆ Premium"
                                if st.button(premium_label, key=f"premium_{user_id}", use_container_width=True):
                                    resp = requests.put(
                                        f"{API_URL}/admin/users/{user_id}/toggle-premium",
                                        headers=get_auth_header()
                                    )
                                    if resp.status_code == 200:
                                        st.rerun()
                            with col2:
                                active_label = "✅ Active" if user['is_active'] else "❌ Disabled"
                                if st.button(active_label, key=f"active_{user_id}", use_container_width=True):
                                    resp = requests.put(
                                        f"{API_URL}/admin/users/{user_id}/toggle-active",
                                        headers=get_auth_header()
                                    )
                                    if resp.status_code == 200:
                                        st.rerun()
        except Exception as e:
            st.error(f"Error loading users: {e}")


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

# --- Define Categories and Sources ---
CATEGORIES = {
    "top_stories": "📰 Top Stories",
    "world": "🌍 World",
    "nation": "🇺🇸 U.S.",
    "business": "💼 Business",
    "technology": "💻 Technology",
    "healthcare_finance": "🏥💰 Healthcare Finance",
    "ai_blockchain": "🤖⛓️ AI & Blockchain",
    "entertainment": "🎬 Entertainment",
    "sports": "⚽ Sports",
    "science": "🔬 Science",
    "health": "🏥 Health"
}

NEWS_SOURCES = {
    "reuters": "📡 Reuters",
    "ap_news": "📰 Associated Press",
    "npr": "🎙️ NPR",
    "bbc": "🇬🇧 BBC News",
    "fierce_healthcare": "🏥 Fierce Healthcare",
    "beckers_hospital": "🏨 Becker's Hospital",
    "healthcare_finance_news": "💵 Healthcare Finance",
    "techcrunch": "💻 TechCrunch",
    "wired": "🔌 Wired",
    "coindesk": "₿ CoinDesk",
    "cointelegraph": "⛓️ Cointelegraph"
}

# Initialize selected categories from user settings
if 'selected_categories' not in st.session_state:
    user_settings = fetch_user_settings()
    if user_settings and 'categories' in user_settings:
        st.session_state.selected_categories = user_settings['categories']
    else:
        st.session_state.selected_categories = ["top_stories", "technology", "business"]

if 'selected_sources' not in st.session_state:
    st.session_state.selected_sources = []

# --- Main Header ---
st.markdown("""
<div style="margin-bottom: 1.5rem;">
    <h1 style="margin: 0; font-size: 2rem;">👋 Welcome back!</h1>
    <p style="color: #666; margin: 0.5rem 0 0 0; font-size: 1.1rem;">Here's what's happening in the news today</p>
</div>
""", unsafe_allow_html=True)

# --- Filter Bar: Categories & Sources ---
st.markdown("""
<style>
    .filter-bar {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.08) 0%, rgba(118, 75, 162, 0.08) 100%);
        border: 1px solid rgba(102, 126, 234, 0.2);
        border-radius: 16px;
        padding: 1.25rem;
        margin-bottom: 1.5rem;
    }
    .filter-label {
        font-size: 0.85rem;
        font-weight: 600;
        color: #4a5568;
        margin-bottom: 0.5rem;
    }
</style>
<div class="filter-bar">
</div>
""", unsafe_allow_html=True)

# Filter controls in columns
filter_col1, filter_col2, filter_col3 = st.columns([3, 3, 1])

with filter_col1:
    st.markdown("<p class='filter-label'>🏷️ Categories</p>", unsafe_allow_html=True)
    selected = st.multiselect(
        "Select categories",
        options=list(CATEGORIES.keys()),
        default=st.session_state.selected_categories,
        format_func=lambda x: CATEGORIES[x],
        label_visibility="collapsed",
        key="main_categories"
    )
    if selected != st.session_state.selected_categories:
        st.session_state.selected_categories = selected
        save_user_settings({"categories": selected})
        if 'news_data' in st.session_state:
            del st.session_state['news_data']

with filter_col2:
    st.markdown("<p class='filter-label'>📡 Sources</p>", unsafe_allow_html=True)
    selected_sources = st.multiselect(
        "Select sources",
        options=list(NEWS_SOURCES.keys()),
        default=st.session_state.selected_sources,
        format_func=lambda x: NEWS_SOURCES[x],
        label_visibility="collapsed",
        key="main_sources"
    )
    if selected_sources != st.session_state.selected_sources:
        st.session_state.selected_sources = selected_sources
        if 'news_data' in st.session_state:
            del st.session_state['news_data']

with filter_col3:
    st.markdown("<p class='filter-label'>&nbsp;</p>", unsafe_allow_html=True)
    if st.button("🔄 Refresh", key="refresh_main", use_container_width=True):
        if 'news_data' in st.session_state:
            del st.session_state['news_data']
        st.rerun()

# --- Main Content Tabs ---
tab1, tab2, tab3, tab4 = st.tabs(["📰 News Feed", "📧 Email & Scheduler", "🔗 Integrations", "🤖 AI Tools"])

with tab1:
    if 'news_data' not in st.session_state:
        # Get selected categories and sources from session state
        categories = st.session_state.get('selected_categories', ["top_stories", "technology", "business"])
        sources = st.session_state.get('selected_sources', [])
        
        with st.spinner("🔍 Scanning news sources..."):
            # Fetch from categories
            category_news = fetch_news(categories)
            
            # Fetch from selected sources if any
            source_news = []
            if sources:
                try:
                    sources_param = ",".join(sources)
                    response = requests.get(f"{API_URL}/news/sources?sources={sources_param}", timeout=30)
                    if response.status_code == 200:
                        source_news = response.json().get('news', [])
                except Exception as e:
                    print(f"Error fetching from sources: {e}")
            
            # Fetch from Feedly if enabled
            feedly_news = []
            if st.session_state.get('include_feedly', False):
                try:
                    response = requests.get(f"{API_URL}/feedly/articles", timeout=30)
                    if response.status_code == 200:
                        feedly_news = response.json().get('news', [])
                except Exception as e:
                    print(f"Error fetching from Feedly: {e}")
            
            # Combine results
            st.session_state.news_data = category_news + source_news + feedly_news

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

    # --- Raw Source Data (Collapsible with AI Features) ---
    if 'news_data' in st.session_state and st.session_state.news_data:
        st.markdown("---")
        with st.expander("📰 Combined Raw Source Data", expanded=False):
            st.caption("All RSS excerpts combined with AI summarization options")
            
            # Stats
            articles_count = len(st.session_state.news_data)
            articles_with_content = sum(1 for a in st.session_state.news_data if a.get('content') or a.get('summary'))
            
            # Display stats
            stat_col1, stat_col2 = st.columns(2)
            with stat_col1:
                st.metric("📰 Total Articles", articles_count)
            with stat_col2:
                st.metric("📄 With Content", articles_with_content)
            
            st.markdown("---")
            
            # Combine all content for display
            from bs4 import BeautifulSoup
            
            combined_text = []
            for idx, article in enumerate(st.session_state.news_data):
                title = article.get('title', 'Untitled')
                source = article.get('source', 'Unknown')
                raw_summary = article.get('summary', '')
                raw_content = article.get('content', '')
                link = article.get('link', '')
                
                # Clean HTML tags
                clean_summary = BeautifulSoup(raw_summary, 'html.parser').get_text(separator=' ', strip=True) if raw_summary else ''
                clean_content = BeautifulSoup(raw_content, 'html.parser').get_text(separator=' ', strip=True) if raw_content else ''
                
                # Use content if available, otherwise summary
                text = clean_content if clean_content else clean_summary
                
                if text:
                    combined_text.append(f"**{idx+1}. {title}** ({source})\n{text[:500]}{'...' if len(text) > 500 else ''}\n")
            
            # Display combined content
            if combined_text:
                # Create copyable text area
                all_text = "\n---\n".join(combined_text)
                st.text_area(
                    "Combined Content (Copy All)",
                    value=all_text,
                    height=400,
                    key="combined_raw_text"
                )
                
                st.markdown("---")
                
                # Individual article display
                st.markdown("#### 📋 Individual Articles")
                for idx, article in enumerate(st.session_state.news_data[:20]):  # Limit to 20
                    title = article.get('title', 'Untitled')
                    source = article.get('source', 'Unknown')
                    raw_summary = article.get('summary', '')
                    link = article.get('link', '')
                    raw_content = article.get('content', '')
                    
                    clean_summary = BeautifulSoup(raw_summary, 'html.parser').get_text(separator=' ', strip=True) if raw_summary else ''
                    clean_content = BeautifulSoup(raw_content, 'html.parser').get_text(separator=' ', strip=True) if raw_content else ''
                    
                    st.markdown(f"**{idx+1}. {title}**")
                    st.caption(f"Source: {source}")
                    
                    if clean_summary:
                        display_summary = clean_summary[:500] + "..." if len(clean_summary) > 500 else clean_summary
                        st.markdown(display_summary)
                    
                    if clean_content:
                        with st.expander("📄 Full Content"):
                            st.text(clean_content[:2000])
                    
                    if link:
                        st.markdown(f"[🔗 Read original]({link})")
                    
                    st.markdown("---")
            else:
                st.info("No content available to display.")

with tab2:
    st.markdown("### 📧 Email & Scheduler")
    st.caption("Configure your email notifications and automatic digest delivery.")
    
    # --- Email Subscription Section ---
    st.markdown("#### ✉️ Notification Email")
    
    # Get current email from settings or use logged-in email
    default_email = st.session_state.get('notification_email', st.session_state.get('user_email', ''))
    
    col_email1, col_email2 = st.columns([3, 1])
    with col_email1:
        notification_email = st.text_input(
            "Email address",
            value=default_email,
            placeholder="your@email.com",
            key="notification_email_input_tab",
            label_visibility="collapsed"
        )
    with col_email2:
        if st.button("💾 Save", key="save_email_tab", use_container_width=True):
            if notification_email:
                try:
                    response = requests.put(
                        f"{API_URL}/settings/",
                        headers=get_auth_header(),
                        json={"notification_email": notification_email}
                    )
                    if response.status_code == 200:
                        st.session_state['notification_email'] = notification_email
                        st.success("✅ Saved!")
                    else:
                        st.error("Failed")
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("Enter email")
    
    st.markdown("---")
    
    # --- Scheduled Email Settings ---
    st.markdown("#### ⏰ Scheduled Digest")
    st.caption("Automatic news summary delivery to your inbox.")
    
    # Load scheduler settings from user settings
    if 'scheduler_settings' not in st.session_state:
        user_settings = fetch_user_settings()
        if user_settings:
            st.session_state['scheduler_settings'] = {
                'enabled': user_settings.get('scheduler_enabled', False),
                'interval': user_settings.get('scheduler_interval_hours', 12),
                'max_items': user_settings.get('max_items_per_category', 5),
                'word_count': user_settings.get('target_word_count', 500)
            }
        else:
            st.session_state['scheduler_settings'] = {
                'enabled': False,
                'interval': 12,
                'max_items': 5,
                'word_count': 500
            }
    
    sched = st.session_state['scheduler_settings']
    
    # Enable/Disable scheduler
    scheduler_enabled = st.checkbox(
        "Enable scheduled emails",
        value=sched['enabled'],
        key="scheduler_enabled_toggle_tab"
    )
    
    if scheduler_enabled:
        # Interval selection
        interval_options = {6: "Every 6 hours", 12: "Every 12 hours", 24: "Daily", 48: "Every 2 days"}
        current_interval_label = interval_options.get(sched['interval'], "Every 12 hours")
        
        selected_interval_label = st.selectbox(
            "Delivery frequency",
            options=list(interval_options.values()),
            index=list(interval_options.values()).index(current_interval_label),
            key="scheduler_interval_select_tab"
        )
        selected_interval = [k for k, v in interval_options.items() if v == selected_interval_label][0]
        
        # Max items per category
        max_items = st.slider(
            "Max articles per category",
            min_value=1,
            max_value=10,
            value=sched['max_items'],
            key="scheduler_max_items_tab"
        )
        
        # Display current adaptive word count (read-only)
        st.markdown(f"""
        <div style="background: rgba(102, 126, 234, 0.1); padding: 0.75rem; border-radius: 8px; margin: 0.5rem 0;">
            <p style="margin: 0; font-size: 0.85rem; opacity: 0.8;">📊 Current summary length</p>
            <p style="margin: 0.25rem 0 0 0; font-weight: 600; font-size: 1.1rem;">{sched['word_count']} words</p>
            <p style="margin: 0.25rem 0 0 0; font-size: 0.75rem; opacity: 0.6;">Adjusts based on your feedback</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Save scheduler settings button
        if st.button("💾 Save Schedule", key="save_scheduler_tab", use_container_width=True):
            try:
                response = requests.put(
                    f"{API_URL}/settings/",
                    headers=get_auth_header(),
                    json={
                        "scheduler_enabled": True,
                        "scheduler_interval_hours": selected_interval,
                        "max_items_per_category": max_items
                    }
                )
                if response.status_code == 200:
                    st.session_state['scheduler_settings'] = {
                        'enabled': True,
                        'interval': selected_interval,
                        'max_items': max_items,
                        'word_count': sched['word_count']
                    }
                    st.success("✅ Schedule saved!")
                else:
                    st.error(f"Failed to save: {response.text}")
            except Exception as e:
                st.error(f"Error: {e}")
    
    # Update enabled state if toggled off
    if scheduler_enabled != sched['enabled']:
        try:
            requests.put(
                f"{API_URL}/settings/",
                headers=get_auth_header(),
                json={"scheduler_enabled": scheduler_enabled}
            )
            st.session_state['scheduler_settings']['enabled'] = scheduler_enabled
            st.rerun()
        except:
            pass
    
    # Premium badge for audio
    if st.session_state.get('is_premium', False):
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 0.5rem 0.75rem; border-radius: 8px; margin-top: 0.5rem;">
            <p style="margin: 0; font-size: 0.8rem;">🎧 Premium: Audio included in emails</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.caption("💎 Upgrade to Premium for audio summaries")
    
    st.markdown("---")
    
    # --- Delivery History Section ---
    st.markdown("#### 📧 Delivery History")
    
    with st.expander("View past deliveries", expanded=False):
        try:
            response = requests.get(
                f"{API_URL}/deliveries/",
                headers=get_auth_header(),
                params={"limit": 5}
            )
            if response.status_code == 200:
                data = response.json()
                deliveries = data.get('deliveries', [])
                total = data.get('total', 0)
                
                if deliveries:
                    st.caption(f"Showing {len(deliveries)} of {total} deliveries")
                    
                    for delivery in deliveries:
                        # Format date
                        delivered_at = delivery.get('delivered_at', '')
                        if delivered_at:
                            try:
                                dt = dateutil.parser.parse(delivered_at)
                                date_str = dt.strftime("%b %d, %Y %I:%M %p")
                            except:
                                date_str = "Unknown"
                        else:
                            date_str = "Unknown"
                        
                        # Feedback status
                        feedback = delivery.get('feedback_received')
                        if feedback:
                            feedback_icon = {"too_short": "📈", "just_right": "✅", "too_long": "📉"}.get(feedback, "")
                            feedback_text = f"{feedback_icon} {feedback.replace('_', ' ').title()}"
                        else:
                            feedback_text = "⏳ Awaiting"
                        
                        # Word count info
                        target = delivery.get('word_count_target', '-')
                        actual = delivery.get('actual_word_count', '-')
                        
                        # Audio badge
                        audio_badge = "🎧" if delivery.get('audio_included') else ""
                        
                        st.markdown(f"""
                        <div style="background: rgba(102, 126, 234, 0.1); padding: 0.75rem; border-radius: 8px; margin-bottom: 0.5rem;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <span style="font-size: 0.8rem; font-weight: 600;">{date_str}</span>
                                <span style="font-size: 0.75rem;">{audio_badge}</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; margin-top: 0.25rem;">
                                <span style="font-size: 0.75rem; opacity: 0.8;">Words: {actual}/{target}</span>
                                <span style="font-size: 0.75rem;">{feedback_text}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No deliveries yet. Enable scheduling to receive email digests!")
            elif response.status_code == 401:
                st.caption("Login required to view history")
            else:
                st.caption("Unable to load delivery history")
        except Exception as e:
            st.caption(f"Error loading history")

with tab3:
    st.markdown("### 🔗 Integrations")
    st.caption("Connect external services to enhance your news experience.")
    
    # --- Feedly Integration ---
    st.markdown("#### 🦅 Feedly")
    st.markdown("""
    <div style="background: rgba(102, 126, 234, 0.08); padding: 1rem; border-radius: 12px; margin-bottom: 1rem;">
        <p style="margin: 0; font-size: 0.9rem;">Connect your Feedly account to include personalized RSS feeds in your news digest.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check Feedly status
    feedly_configured = False
    try:
        response = requests.get(f"{API_URL}/feedly/status", timeout=5)
        if response.status_code == 200:
            feedly_configured = response.json().get('configured', False)
    except:
        pass
    
    if feedly_configured:
        st.success("✅ Feedly connected")
        
        # Toggle to include Feedly articles
        if 'include_feedly' not in st.session_state:
            st.session_state.include_feedly = False
        
        include_feedly = st.checkbox(
            "Include Feedly articles in news feed",
            value=st.session_state.include_feedly,
            key="feedly_toggle_tab"
        )
        
        if include_feedly != st.session_state.include_feedly:
            st.session_state.include_feedly = include_feedly
            if 'news_data' in st.session_state:
                del st.session_state['news_data']
    else:
        st.info("💡 Set FEEDLY_API_KEY in your .env file to connect Feedly.")
    
    st.markdown("---")
    
    # Future integrations placeholder
    st.markdown("#### 🚀 More Integrations Coming Soon")
    st.markdown("""
    - **Pocket** - Save articles for later
    - **Notion** - Export digests to your workspace
    - **Slack** - Get notifications in your channels
    """)

with tab4:
    st.markdown("### 🤖 AI Tools")
    st.caption("Powerful AI features to help you understand and process news.")
    
    # Generate Digest Feature
    st.markdown("#### 📋 Generate AI Digest")
    st.markdown("""
    <div style="background: rgba(102, 126, 234, 0.08); padding: 1rem; border-radius: 12px; margin-bottom: 1rem;">
        <p style="margin: 0; font-size: 0.9rem;">Create an AI-powered summary of today's news from your selected categories and sources.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("✨ Generate Digest Now", key="generate_digest_btn", use_container_width=True):
        with st.spinner("🤖 AI is analyzing and summarizing your news..."):
            try:
                response = requests.get(f"{API_URL}/digest", timeout=60)
                if response.status_code == 200:
                    digest_data = response.json()
                    st.session_state['digest'] = digest_data
                    st.success("✅ Digest generated!")
                    st.rerun()
                else:
                    st.error("Failed to generate digest")
            except Exception as e:
                st.error(f"Error: {e}")
    
    # Display existing digest if available
    if 'digest' in st.session_state:
        st.markdown("---")
        st.markdown("#### 📄 Your Latest Digest")
        
        digest_data = st.session_state['digest']
        
        # Metrics
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📰 Articles", digest_data.get('article_count', 0))
        with col2:
            st.metric("📍 Sources", len(digest_data.get('sources', [])))
        
        # Content
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1.5rem; border-radius: 12px; margin: 1rem 0;">
            <div style="background: white; padding: 1.25rem; border-radius: 8px;">
        """, unsafe_allow_html=True)
        
        st.markdown(digest_data.get('digest', 'No digest content available.'))
        
        st.markdown("</div></div>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Future AI features placeholder
    st.markdown("#### 🔮 Coming Soon")
    st.markdown("""
    - **Topic Deep Dive** - Get detailed analysis on specific topics
    - **Sentiment Analysis** - Understand the tone of news coverage
    - **Trend Detection** - Spot emerging stories
    """)
