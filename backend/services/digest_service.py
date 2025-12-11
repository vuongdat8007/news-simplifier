from datetime import datetime
from typing import Dict, Optional
from services.news_fetcher import fetch_news
from services.openai_service import create_digest as openai_create_digest


def combine_articles_text(articles: list) -> str:
    """
    Combine all article summaries into a single text block.
    """
    if not articles:
        return ""
    
    combined = []
    for article in articles:
        title = article.get('title', 'Untitled')
        source = article.get('source', 'Unknown')
        summary = article.get('summary', '')
        combined.append(f"**{title}** ({source}): {summary}")
    
    return "\n\n".join(combined)


def generate_digest() -> Dict:
    """
    Fetch all news and generate a one-page digest.
    Returns a dictionary with digest content and metadata.
    """
    # Fetch all news articles
    articles = fetch_news()
    
    if not articles:
        return {
            "digest": "No news articles available at this time. Please try again later.",
            "generated_at": datetime.now().isoformat(),
            "article_count": 0,
            "sources": []
        }
    
    # Get unique sources
    sources = list(set(article.get('source', 'Unknown') for article in articles))
    
    # Try OpenAI digest first
    digest_text = openai_create_digest(articles)
    
    # Fallback to simple concatenation if OpenAI is not available
    if not digest_text:
        digest_text = _create_mock_digest(articles)
    
    return {
        "digest": digest_text,
        "generated_at": datetime.now().isoformat(),
        "article_count": len(articles),
        "sources": sources
    }


def _create_mock_digest(articles: list) -> str:
    """
    Create a concise one-page digest when OpenAI is not available.
    """
    today = datetime.now().strftime("%B %d, %Y")
    
    # Limit to top 8 articles total for one-page fit
    top_articles = articles[:8]
    
    header = f"**Daily News Digest - {today}**\n\n"
    
    content = ""
    for i, article in enumerate(top_articles, 1):
        title = article.get('title', 'Untitled')
        # Keep only headline, no summary
        content += f"{i}. {title}\n\n"
    
    return header + content
