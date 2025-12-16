from io import BytesIO
from gtts import gTTS
import re


def text_to_speech(text: str, lang: str = 'en') -> bytes:
    """
    Convert text to speech using Google Text-to-Speech.
    Returns MP3 audio as bytes.
    """
    # Clean the text for better speech output
    clean_text = _clean_text_for_speech(text)
    
    if not clean_text.strip():
        clean_text = "No content available for audio."
    
    try:
        # Create TTS object
        tts = gTTS(text=clean_text, lang=lang, slow=False)
        
        # Save to bytes buffer
        buffer = BytesIO()
        tts.write_to_fp(buffer)
        buffer.seek(0)
        
        audio_bytes = buffer.getvalue()
        buffer.close()
        
        return audio_bytes
    except Exception as e:
        print(f"TTS Error: {e}")
        # Return a simple error message as audio
        error_tts = gTTS(text="Sorry, there was an error generating the audio.", lang='en')
        buffer = BytesIO()
        error_tts.write_to_fp(buffer)
        buffer.seek(0)
        return buffer.getvalue()


def _clean_text_for_speech(text: str) -> str:
    """
    Clean markdown and special characters for better speech output.
    """
    # Remove markdown headers
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    
    # Remove markdown bold/italic
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)
    text = re.sub(r'_([^_]+)_', r'\1', text)
    
    # Remove markdown links, keep text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    
    # Remove horizontal rules
    text = re.sub(r'^---+\s*$', '', text, flags=re.MULTILINE)
    
    # Remove bullet points
    text = re.sub(r'^\s*[-*]\s+', '', text, flags=re.MULTILINE)
    
    # Remove extra whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' +', ' ', text)
    
    # Note: Removed artificial pauses - OpenAI TTS handles natural pauses automatically
    
    return text.strip()


def text_to_speech_openai(text: str, voice: str = 'alloy') -> bytes:
    """
    Convert text to speech using OpenAI TTS.
    Uses high-quality neural voice.
    
    Available voices: alloy, echo, fable, onyx, nova, shimmer
    Returns MP3 audio as bytes.
    """
    import os
    from openai import OpenAI
    from dotenv import load_dotenv
    
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "sk-your-api-key-here":
        print("[DEBUG] OpenAI API key not configured, falling back to gTTS")
        return text_to_speech(text)
    
    # Clean the text
    clean_text = _clean_text_for_speech(text)
    
    if not clean_text.strip():
        clean_text = "No content available for audio."
    
    try:
        client = OpenAI(api_key=api_key)
        
        print(f"[DEBUG] Generating OpenAI TTS with voice: {voice}")
        print(f"[DEBUG] Text length: {len(clean_text)} characters")
        
        # Using tts-1 standard model
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=clean_text
        )
        
        # Get audio bytes
        audio_bytes = response.content
        
        print(f"[DEBUG] OpenAI TTS generated: {len(audio_bytes)} bytes")
        return audio_bytes
        
    except Exception as e:
        print(f"OpenAI TTS Error: {e}")
        print("[DEBUG] Falling back to gTTS")
        return text_to_speech(text)
