import feedparser
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse, urljoin

# Categorized RSS Feeds from Google News
RSS_FEEDS_BY_CATEGORY = {
    "top_stories": {
        "name": "Top Stories",
        "emoji": "📰",
        "url": "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"
    },
    "world": {
        "name": "World",
        "emoji": "🌍",
        "url": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx1YlY4U0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en"
    },
    "nation": {
        "name": "U.S.",
        "emoji": "🇺🇸",
        "url": "https://news.google.com/rss/topics/CAAqIggKIhxDQkFTRHdvSkwyMHZNRGxqTjNjd0VnSmxiaWdBUAE?hl=en-US&gl=US&ceid=US:en"
    },
    "business": {
        "name": "Business",
        "emoji": "💼",
        "url": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en"
    },
    "technology": {
        "name": "Technology",
        "emoji": "💻",
        "url": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en"
    },
    "entertainment": {
        "name": "Entertainment",
        "emoji": "🎬",
        "url": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNREpxYW5RU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en"
    },
    "sports": {
        "name": "Sports",
        "emoji": "⚽",
        "url": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp1ZEdvU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en"
    },
    "science": {
        "name": "Science",
        "emoji": "🔬",
        "url": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp0Y1RjU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en"
    },
    "health": {
        "name": "Health",
        "emoji": "🏥",
        "url": "https://news.google.com/rss/topics/CAAqIQgKIhtDQkFTRGdvSUwyMHZNR3QwTlRFU0FtVnVLQUFQAQ?hl=en-US&gl=US&ceid=US:en"
    }
}

# Default feeds (backward compatibility)
RSS_FEEDS = [
    RSS_FEEDS_BY_CATEGORY["top_stories"]["url"],
    RSS_FEEDS_BY_CATEGORY["world"]["url"],
    RSS_FEEDS_BY_CATEGORY["technology"]["url"],
    RSS_FEEDS_BY_CATEGORY["business"]["url"],
]

# Maximum content length per article (in characters) to avoid token limits
MAX_CONTENT_LENGTH = 1500

# Common RSS feed paths to try
COMMON_RSS_PATHS = [
    '/feed',
    '/rss',
    '/feed/',
    '/rss/',
    '/feeds/posts/default',
    '/rss.xml',
    '/feed.xml',
    '/atom.xml',
    '/index.xml',
    '/rss/news',
    '/feeds/all.atom.xml',
]

# Cache for discovered RSS feeds to avoid repeated lookups
_rss_cache: Dict[str, Optional[str]] = {}


def get_headers() -> Dict[str, str]:
    """Return common headers for HTTP requests."""
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }


def get_base_url(url: str) -> str:
    """Extract the base URL (scheme + domain) from a URL."""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def resolve_redirect(url: str) -> Optional[str]:
    """Follow redirects to get the final URL (important for Google News links)."""
    try:
        response = requests.head(url, headers=get_headers(), timeout=10, allow_redirects=True)
        return response.url
    except Exception:
        try:
            # Fallback to GET if HEAD fails
            response = requests.get(url, headers=get_headers(), timeout=10, allow_redirects=True)
            return response.url
        except Exception as e:
            print(f"[DEBUG] Failed to resolve redirect for {url}: {e}")
            return None


def discover_rss_feed(base_url: str) -> Optional[str]:
    """
    Discover the RSS feed URL for a given website.
    
    Strategy:
    1. Check cached results
    2. Try common RSS paths
    3. Parse HTML for RSS link tags
    """
    # Check cache first
    if base_url in _rss_cache:
        print(f"[DEBUG] RSS cache hit for {base_url}")
        return _rss_cache[base_url]
    
    print(f"[DEBUG] Discovering RSS feed for: {base_url}")
    
    # Strategy 1: Try common RSS paths
    for path in COMMON_RSS_PATHS:
        feed_url = urljoin(base_url, path)
        try:
            response = requests.get(feed_url, headers=get_headers(), timeout=5)
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '').lower()
                # Check if it's an RSS/Atom feed
                if any(ct in content_type for ct in ['xml', 'rss', 'atom']):
                    # Verify it's actually a valid feed
                    feed = feedparser.parse(response.content)
                    if feed.entries:
                        print(f"[DEBUG] Found RSS feed at: {feed_url}")
                        _rss_cache[base_url] = feed_url
                        return feed_url
        except Exception:
            continue
    
    # Strategy 2: Parse HTML for RSS link tags
    try:
        response = requests.get(base_url, headers=get_headers(), timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for RSS/Atom link tags
            rss_links = soup.find_all('link', type=lambda x: x and ('rss' in x.lower() or 'atom' in x.lower()))
            
            # Also check for alternate links
            alternate_links = soup.find_all('link', rel='alternate')
            for link in alternate_links:
                link_type = link.get('type', '').lower()
                if 'rss' in link_type or 'atom' in link_type or 'xml' in link_type:
                    rss_links.append(link)
            
            for link in rss_links:
                href = link.get('href')
                if href:
                    feed_url = urljoin(base_url, href)
                    # Verify the feed works
                    try:
                        feed = feedparser.parse(feed_url)
                        if feed.entries:
                            print(f"[DEBUG] Found RSS feed via HTML: {feed_url}")
                            _rss_cache[base_url] = feed_url
                            return feed_url
                    except Exception:
                        continue
    except Exception as e:
        print(f"[DEBUG] Error parsing HTML for RSS: {e}")
    
    print(f"[DEBUG] No RSS feed found for: {base_url}")
    _rss_cache[base_url] = None
    return None


def find_article_in_feed(feed_url: str, article_title: str, article_link: str) -> Optional[str]:
    """
    Search for matching article content in an RSS feed.
    Matches by title similarity or link.
    """
    try:
        feed = feedparser.parse(feed_url)
        
        # Normalize the article link for comparison
        parsed_article = urlparse(article_link)
        article_path = parsed_article.path.lower()
        
        for entry in feed.entries:
            # Check if link matches
            entry_link = entry.get('link', '')
            parsed_entry = urlparse(entry_link)
            entry_path = parsed_entry.path.lower()
            
            # Match by path similarity
            if article_path and entry_path and article_path in entry_path:
                content = extract_content_from_entry(entry)
                if content:
                    return content
            
            # Match by title similarity (simple substring check)
            entry_title = entry.get('title', '').lower()
            if article_title.lower() in entry_title or entry_title in article_title.lower():
                content = extract_content_from_entry(entry)
                if content:
                    return content
        
    except Exception as e:
        print(f"[DEBUG] Error searching feed {feed_url}: {e}")
    
    return None


def extract_content_from_entry(entry) -> Optional[str]:
    """Extract the best available content from an RSS feed entry."""
    content = None
    
    # Try content:encoded first (usually has full article)
    if hasattr(entry, 'content') and entry.content:
        for c in entry.content:
            if c.get('value'):
                content = c['value']
                break
    
    # Try description/summary
    if not content:
        content = entry.get('summary') or entry.get('description', '')
    
    if content:
        # Clean HTML from content
        soup = BeautifulSoup(content, 'html.parser')
        text = soup.get_text(separator=' ', strip=True)
        
        # Limit content length
        if len(text) > MAX_CONTENT_LENGTH:
            text = text[:MAX_CONTENT_LENGTH] + "..."
        
        return text if len(text) > 100 else None
    
    return None


def fetch_content_via_rss(article_link: str, article_title: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Fetch article content by discovering and parsing the source's RSS feed.
    Returns (content, rss_feed_url) tuple.
    """
    # Resolve redirects to get actual article URL
    resolved_url = resolve_redirect(article_link)
    if not resolved_url:
        return None, None
    
    print(f"[DEBUG] Resolved URL: {resolved_url}")
    
    # Get base URL of the source
    base_url = get_base_url(resolved_url)
    
    # Discover the RSS feed
    rss_feed_url = discover_rss_feed(base_url)
    if not rss_feed_url:
        return None, None
    
    # Search for the article in the feed
    content = find_article_in_feed(rss_feed_url, article_title, resolved_url)
    
    return content, rss_feed_url


def fetch_article_content_fallback(url: str) -> Optional[str]:
    """
    Fallback: Fetch and extract the main article content from a news URL via direct scraping.
    Returns the extracted text content, or None if extraction fails.
    """
    try:
        response = requests.get(url, headers=get_headers(), timeout=15, allow_redirects=True)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe']):
            element.decompose()
        
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
        
        article_content = None
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                article_content = element
                break
        
        if not article_content:
            article_content = soup.body
        
        if article_content:
            paragraphs = article_content.find_all('p')
            text_parts = []
            for p in paragraphs:
                text = p.get_text(strip=True)
                if len(text) > 50:
                    text_parts.append(text)
            
            full_text = ' '.join(text_parts)
            
            if len(full_text) > MAX_CONTENT_LENGTH:
                full_text = full_text[:MAX_CONTENT_LENGTH] + "..."
            
            return full_text if len(full_text) > 100 else None
            
    except Exception as e:
        print(f"[DEBUG] Fallback scraping failed for {url}: {e}")
        return None
    
    return None


def fetch_news_by_categories(categories: List[str] = None) -> List[Dict]:
    """
    Fetches news from specified categories.
    
    Args:
        categories: List of category keys (e.g., ['technology', 'business'])
                   If None, uses default categories.
    
    Returns:
        List of article dictionaries with category info.
    """
    if not categories:
        categories = ["top_stories", "technology", "business"]
    
    articles = []
    
    for category in categories:
        if category not in RSS_FEEDS_BY_CATEGORY:
            print(f"[DEBUG] Unknown category: {category}")
            continue
        
        cat_info = RSS_FEEDS_BY_CATEGORY[category]
        url = cat_info["url"]
        cat_name = cat_info["name"]
        cat_emoji = cat_info["emoji"]
        
        try:
            print(f"[DEBUG] Fetching category: {cat_emoji} {cat_name}")
            feed = feedparser.parse(url)
            
            for entry in feed.entries[:3]:  # Limit to 3 per category
                article_link = entry.get("link", "#")
                article_title = entry.get("title", "No Title")
                
                # Try to fetch content via RSS discovery
                print(f"[DEBUG] Processing: {article_title[:50]}...")
                content, rss_source = fetch_content_via_rss(article_link, article_title)
                
                # Fallback to direct scraping if RSS discovery failed
                if not content:
                    print(f"[DEBUG] RSS discovery failed, trying direct scraping...")
                    content = fetch_article_content_fallback(article_link)
                    rss_source = None
                
                article = {
                    "title": article_title,
                    "link": article_link,
                    "summary": entry.get("summary", entry.get("description", "No summary available.")),
                    "published": entry.get("published", "Unknown Date"),
                    "source": f"{cat_emoji} {cat_name}",
                    "category": category,
                    "category_name": cat_name,
                    "content": content,
                    "rss_source": rss_source
                }
                
                if content:
                    source_info = f"via RSS: {rss_source}" if rss_source else "via direct scraping"
                    print(f"[DEBUG] Got {len(content)} chars {source_info}")
                else:
                    print(f"[DEBUG] Could not fetch content from any source")
                
                articles.append(article)
                
        except Exception as e:
            print(f"Error fetching from {cat_name}: {e}")
            continue
    
    print(f"[DEBUG] Total articles fetched: {len(articles)}")
    return articles


def fetch_news() -> List[Dict]:
    """
    Fetches news from default RSS feeds.
    Backward compatible wrapper for fetch_news_by_categories.
    """
    return fetch_news_by_categories(["top_stories", "world", "technology", "business"])
