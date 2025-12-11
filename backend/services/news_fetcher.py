import feedparser
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional

RSS_FEEDS = [
    # Google News - Top Stories
    "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
    # Google News - World
    "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx1YlY4U0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en",
    # Google News - Technology
    "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en",
    # Google News - Business
    "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en",
]

# Maximum content length per article (in characters) to avoid token limits
MAX_CONTENT_LENGTH = 1500


def fetch_article_content(url: str) -> Optional[str]:
    """
    Fetch and extract the main article content from a news URL.
    Returns the extracted text content, or None if extraction fails.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
        # Follow redirects to get the actual article URL (important for Google News links)
        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        response.raise_for_status()
        
        # Log the final URL after redirects
        final_url = response.url
        if final_url != url:
            print(f"[DEBUG] Redirected: {url[:50]}... -> {final_url[:80]}...")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe']):
            element.decompose()
        
        # Try to find the main article content using common selectors
        article_content = None
        
        # Try common article containers
        selectors = [
            'article',
            '[role="article"]',
            '.article-body',
            '.article-content',
            '.story-body',
            '.post-content',
            '.entry-content',
            'main',
            '.content'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                article_content = element
                break
        
        # Fallback to body if no article container found
        if not article_content:
            article_content = soup.body
        
        if article_content:
            # Extract text from paragraphs
            paragraphs = article_content.find_all('p')
            text_parts = []
            for p in paragraphs:
                text = p.get_text(strip=True)
                if len(text) > 50:  # Only include substantial paragraphs
                    text_parts.append(text)
            
            full_text = ' '.join(text_parts)
            
            # Limit content length
            if len(full_text) > MAX_CONTENT_LENGTH:
                full_text = full_text[:MAX_CONTENT_LENGTH] + "..."
            
            return full_text if len(full_text) > 100 else None
            
    except Exception as e:
        print(f"[DEBUG] Error fetching article content from {url}: {e}")
        return None
    
    return None


def fetch_news() -> List[Dict]:
    """
    Fetches news from defined RSS feeds and returns a unified list of articles.
    Also fetches full article content from each news URL.
    """
    articles = []
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:2]:  # Limit to 2 per feed for one-page digest
                article_link = entry.get("link", "#")
                
                # Fetch full article content
                print(f"[DEBUG] Fetching content from: {article_link}")
                full_content = fetch_article_content(article_link)
                
                article = {
                    "title": entry.get("title", "No Title"),
                    "link": article_link,
                    "summary": entry.get("summary", entry.get("description", "No summary available.")),
                    "published": entry.get("published", "Unknown Date"),
                    "source": feed.feed.get("title", "Unknown Source"),
                    "content": full_content  # Add full scraped content
                }
                
                if full_content:
                    print(f"[DEBUG] Successfully fetched {len(full_content)} chars from article")
                else:
                    print(f"[DEBUG] Could not fetch content, using RSS summary only")
                
                articles.append(article)
        except Exception as e:
            print(f"Error fetching from {url}: {e}")
            continue
    
    print(f"[DEBUG] Total articles fetched: {len(articles)}")
    return articles
