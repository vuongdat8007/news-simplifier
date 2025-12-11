import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Dict, Optional

# Load environment variables
load_dotenv()

# Initialize OpenAI client
_client: Optional[OpenAI] = None

def _get_client() -> Optional[OpenAI]:
    """Get or create OpenAI client."""
    global _client
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key or api_key == "sk-your-api-key-here":
        return None
    
    if _client is None:
        _client = OpenAI(api_key=api_key)
    
    return _client


def summarize_text(text: str) -> Optional[str]:
    """
    Summarize a single piece of text using OpenAI GPT.
    Returns None if OpenAI is not configured.
    """
    client = _get_client()
    if not client:
        return None
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that simplifies news articles. Make the text easy to understand for a general audience. Keep it concise but informative."
                },
                {
                    "role": "user",
                    "content": f"Please simplify this news article:\n\n{text}"
                }
            ],
            max_tokens=300,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return None


def create_digest(articles: List[Dict]) -> Optional[str]:
    """
    Create a one-page digest from multiple news articles using OpenAI GPT.
    Goes through each headline and compiles raw text before sending to OpenAI.
    Returns None if OpenAI is not configured.
    """
    client = _get_client()
    if not client:
        print("[DEBUG] OpenAI client not configured - API key missing or invalid")
        return None
    
    if not articles:
        return "No news articles available to create a digest."
    
    # ========== COMPILE RAW TEXT FROM ALL HEADLINES ==========
    print("\n" + "=" * 70)
    print("   COMPILING RAW TEXT FROM EACH HEADLINE")
    print("=" * 70)
    
    articles_parts = []
    scraped_count = 0
    rss_fallback_count = 0
    
    for i, article in enumerate(articles, 1):
        title = article.get('title', 'Untitled')
        source = article.get('source', 'Unknown')
        link = article.get('link', 'No link')
        full_content = article.get('content')  # Scraped content from the headline link
        rss_summary = article.get('summary', '')  # RSS summary (fallback)
        
        # Determine content source - prefer scraped content from headline link
        if full_content:
            content = full_content
            content_type = "SCRAPED FROM LINK"
            scraped_count += 1
        else:
            content = rss_summary
            content_type = "RSS SUMMARY ONLY"
            rss_fallback_count += 1
        
        # Log each headline's content
        print(f"\n[Headline {i}] {title[:60]}{'...' if len(title) > 60 else ''}")
        print(f"  Source: {source}")
        print(f"  Link: {link[:70]}{'...' if len(link) > 70 else ''}")
        print(f"  Content Type: {content_type} ({len(content)} chars)")
        preview = content[:200] + "..." if len(content) > 200 else content
        print(f"  Preview: {preview}")
        
        # Compile the article text
        articles_parts.append(f"**{title}** ({source})\n{content}")
    
    # Join all articles into raw text
    raw_news_text = "\n\n---\n\n".join(articles_parts)
    
    print("\n" + "-" * 70)
    print("CONTENT COMPILATION SUMMARY:")
    print(f"  - Total Headlines Processed: {len(articles)}")
    print(f"  - Content Scraped from Links: {scraped_count}")
    print(f"  - Using RSS Summary Only: {rss_fallback_count}")
    print(f"  - Total Compiled Raw Text: {len(raw_news_text)} characters")
    print("-" * 70)
    
    # ========== PREPARE OPENAI REQUEST ==========
    
    system_prompt = """You are a news editor creating a VERY BRIEF daily digest.
Your task is to:
1. Summarize ALL articles into ONE short paragraph (150-200 words max)
2. Mention only the most important 4-5 headlines
3. Write in a clear, engaging style
4. Be extremely concise - this must fit on ONE page"""

    user_prompt = f"Create a brief one-paragraph news digest from these articles:\n\n{raw_news_text}"
    
    # ========== DEBUG: SHOW WHAT'S BEING SENT TO OPENAI ==========
    print("\n" + "=" * 70)
    print("   SENDING COMPILED RAW TEXT TO OPENAI")
    print("=" * 70)
    print(f"\n[SYSTEM PROMPT]\n{system_prompt}")
    print(f"\n[USER PROMPT - COMPILED RAW NEWS TEXT]")
    print("-" * 40)
    # Show full or truncated prompt
    if len(user_prompt) > 3000:
        print(user_prompt[:3000])
        print(f"\n... [TRUNCATED - Full size: {len(user_prompt)} chars]")
    else:
        print(user_prompt)
    print("-" * 40)
    print("=" * 70 + "\n")
    # =============================================================
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            max_tokens=300,
            temperature=0.7
        )
        
        result = response.choices[0].message.content
        print(f"[DEBUG] OpenAI Response received: {len(result)} characters")
        return result
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return None

