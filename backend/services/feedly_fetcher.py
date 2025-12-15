"""
Feedly API Integration Service

This module provides integration with the Feedly API for fetching news from user's Feedly feeds.
Requires FEEDLY_API_KEY environment variable to be set.

Feedly API Documentation: https://developer.feedly.com/
"""

import os
import requests
from typing import List, Dict, Optional

# Feedly API base URL
FEEDLY_API_BASE = "https://cloud.feedly.com/v3"


def get_feedly_token() -> Optional[str]:
    """Get Feedly API token from environment."""
    return os.environ.get("FEEDLY_API_KEY")


def is_feedly_configured() -> bool:
    """Check if Feedly API is configured."""
    return get_feedly_token() is not None


def get_feedly_headers() -> Dict[str, str]:
    """Get headers for Feedly API requests."""
    token = get_feedly_token()
    if not token:
        raise ValueError("FEEDLY_API_KEY not configured")
    return {
        "Authorization": f"OAuth {token}",
        "Content-Type": "application/json"
    }


def fetch_feedly_feeds() -> List[Dict]:
    """
    Fetch user's subscribed feeds from Feedly.
    
    Returns:
        List of feed subscription objects.
    """
    if not is_feedly_configured():
        return []
    
    try:
        response = requests.get(
            f"{FEEDLY_API_BASE}/subscriptions",
            headers=get_feedly_headers(),
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Feedly API error: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error fetching Feedly feeds: {e}")
        return []


def fetch_feedly_stream(stream_id: str, count: int = 20) -> List[Dict]:
    """
    Fetch articles from a Feedly stream (feed or category).
    
    Args:
        stream_id: The Feedly stream ID (e.g., feed/http://... or user/.../category/...)
        count: Number of articles to fetch (max 100)
    
    Returns:
        List of article objects.
    """
    if not is_feedly_configured():
        return []
    
    try:
        # URL encode the stream ID
        import urllib.parse
        encoded_stream_id = urllib.parse.quote(stream_id, safe='')
        
        response = requests.get(
            f"{FEEDLY_API_BASE}/streams/{encoded_stream_id}/contents",
            headers=get_feedly_headers(),
            params={"count": min(count, 100)},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("items", [])
        else:
            print(f"Feedly stream error: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error fetching Feedly stream: {e}")
        return []


def fetch_feedly_articles(feed_ids: List[str] = None, count_per_feed: int = 10) -> List[Dict]:
    """
    Fetch articles from multiple Feedly feeds.
    
    Args:
        feed_ids: List of Feedly feed IDs. If None, fetches from all subscribed feeds.
        count_per_feed: Number of articles to fetch per feed.
    
    Returns:
        List of normalized article dictionaries.
    """
    if not is_feedly_configured():
        print("[Feedly] Not configured - FEEDLY_API_KEY not set")
        return []
    
    articles = []
    
    # If no specific feeds, get user's subscriptions
    if feed_ids is None:
        subscriptions = fetch_feedly_feeds()
        feed_ids = [sub.get("id") for sub in subscriptions if sub.get("id")]
    
    for feed_id in feed_ids[:10]:  # Limit to 10 feeds
        items = fetch_feedly_stream(feed_id, count=count_per_feed)
        
        for item in items:
            # Normalize to our article format
            article = {
                "title": item.get("title", "Untitled"),
                "link": item.get("canonicalUrl") or item.get("originId", ""),
                "summary": item.get("summary", {}).get("content", "") if isinstance(item.get("summary"), dict) else item.get("summary", ""),
                "published": item.get("published", ""),
                "source": item.get("origin", {}).get("title", "Feedly"),
                "content": item.get("content", {}).get("content", "") if isinstance(item.get("content"), dict) else item.get("content", "")
            }
            articles.append(article)
    
    print(f"[Feedly] Fetched {len(articles)} articles from {len(feed_ids)} feeds")
    return articles
