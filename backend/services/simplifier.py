import random
from services.openai_service import summarize_text as openai_summarize

def simplify_text(text: str) -> str:
    """
    Simplifies text using OpenAI API with fallback to mock.
    """
    # Try OpenAI first
    result = openai_summarize(text)
    if result:
        return result
    
    # Fallback to mock logic if OpenAI is not configured
    return _mock_simplify(text)


def _mock_simplify(text: str) -> str:
    """
    Mock simplification for when OpenAI is not available.
    """
    sentences = text.split('. ')
    if len(sentences) > 1:
        simplified = ". ".join(sentences[:2]) + "."
    else:
        simplified = text

    prefixes = [
        "Simply put: ",
        "In short: ",
        "To break it down: ",
        "The key takeaway is: "
    ]
    
    return f"{random.choice(prefixes)} {simplified}"
