=============================================================
                   NEWS SIMPLIFIER APP
               Installation & Running Guide
=============================================================

OVERVIEW
--------
News Simplifier is a web application that aggregates news from 
top sources and uses AI to simplify complex articles into 
easy-to-read summaries. It also generates daily digests with
PDF and audio export options.

PREREQUISITES
-------------
- Python 3.8 or higher
- pip (Python package manager)
- OpenAI API key (for AI text simplification)

=============================================================
                    INSTALLATION STEPS
=============================================================

STEP 1: Clone/Navigate to Project Directory
--------------------------------------------
cd /path/to/news-simplifier

STEP 2: Set Up Backend
----------------------
# Navigate to backend folder
cd backend

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

STEP 3: Configure Environment Variables
----------------------------------------
Create a .env file in the backend folder with:

OPENAI_API_KEY=your_openai_api_key_here

STEP 4: Set Up Frontend
-----------------------
# Open a new terminal and navigate to frontend folder
cd frontend

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

=============================================================
                    RUNNING THE APP
=============================================================

STEP 1: Start the Backend Server
--------------------------------
# In the backend directory with venv activated:
cd backend
uvicorn main:app --reload --port 8000

The backend API will be available at: http://localhost:8000

STEP 2: Start the Frontend App
------------------------------
# In a NEW terminal, in the frontend directory with venv activated:
cd frontend
streamlit run app.py

The frontend will be available at: http://localhost:8501

=============================================================
                    API ENDPOINTS
=============================================================

GET  /           - Health check
GET  /news       - Fetch latest news articles
POST /simplify   - Simplify article text
GET  /digest     - Generate daily news digest
GET  /digest/pdf - Download digest as PDF
GET  /digest/audio - Download digest as MP3 audio

=============================================================
                    FEATURES
=============================================================

1. NEWS AGGREGATION
   - Fetches news from multiple sources
   - Displays headlines with source and publication date

2. AI TEXT SIMPLIFICATION
   - Click "Simplify" on any article
   - Uses OpenAI GPT to create easy-to-read summaries

3. DAILY DIGEST
   - Combines all news into a single digest
   - Export to PDF for reading later
   - Export to MP3 audio for listening on the go

=============================================================
                    TECH STACK
=============================================================

Backend:
- FastAPI (Python web framework)
- OpenAI GPT (AI text simplification)
- ReportLab (PDF generation)
- gTTS (Text-to-speech)
- BeautifulSoup4 & Feedparser (News scraping)

Frontend:
- Streamlit (Python web UI framework)
- Custom CSS styling

=============================================================
                    TROUBLESHOOTING
=============================================================

1. "Error connecting to backend"
   - Ensure the backend is running on port 8000
   - Check if uvicorn started without errors

2. "Failed to fetch news"
   - Check your internet connection
   - The news sources may be temporarily unavailable

3. "Error during simplification"
   - Verify your OpenAI API key is correctly set
   - Check if you have API credits available

4. Port already in use
   - Kill existing processes on port 8000 or 8501
   - Or change the port numbers in the commands

=============================================================
                    QUICK START
=============================================================

# Terminal 1 - Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Terminal 2 - Frontend
cd frontend
pip install -r requirements.txt
streamlit run app.py

Then open http://localhost:8501 in your browser!

=============================================================
