import os
from datetime import datetime
from typing import Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from dotenv import load_dotenv

load_dotenv()

# Global scheduler instance
_scheduler: Optional[BackgroundScheduler] = None
_job_id = "news_summary_job"


def get_scheduler() -> Optional[BackgroundScheduler]:
    """Get the scheduler instance."""
    return _scheduler


def scheduled_news_job():
    """
    Job that runs every 12 hours to:
    1. Fetch latest news
    2. Generate AI summary
    3. Create PDF and audio
    4. Send email to recipients
    """
    print("\n" + "=" * 70)
    print(f"   SCHEDULED NEWS JOB STARTING - {datetime.now()}")
    print("=" * 70)
    
    try:
        # Import services
        from services.news_fetcher import fetch_news
        from services.openai_service import summarize_combined_excerpts
        from services.pdf_service import create_pdf
        from services.tts_service import text_to_speech_openai
        from services.email_service import send_news_summary_email
        from bs4 import BeautifulSoup
        
        # Step 1: Fetch news
        print("[SCHEDULER] Fetching news...")
        articles = fetch_news()
        print(f"[SCHEDULER] Fetched {len(articles)} articles")
        
        if not articles:
            print("[SCHEDULER] No articles found, skipping email")
            return
        
        # Step 2: Build combined excerpts
        print("[SCHEDULER] Building combined excerpts...")
        excerpts = []
        for idx, article in enumerate(articles, 1):
            title = article.get('title', 'Untitled')
            source = article.get('source', 'Unknown')
            summary = article.get('summary', '')
            
            section = f"ARTICLE {idx}: {title}\n"
            section += f"Source: {source}\n"
            
            if summary:
                clean_summary = BeautifulSoup(summary, 'html.parser').get_text(separator=' ', strip=True)
                section += clean_summary
            
            excerpts.append(section)
        
        combined_text = "\n\n".join(excerpts)
        print(f"[SCHEDULER] Combined text: {len(combined_text)} characters")
        
        # Step 3: Generate AI summary
        print("[SCHEDULER] Generating AI summary with GPT-4o-mini...")
        summary = summarize_combined_excerpts(combined_text)
        
        if not summary:
            print("[SCHEDULER] Failed to generate summary, skipping email")
            return
        
        print(f"[SCHEDULER] Summary generated: {len(summary)} characters")
        
        # Step 4: Generate PDF
        print("[SCHEDULER] Generating PDF...")
        pdf_bytes = create_pdf(summary, "AI News Summary")
        print(f"[SCHEDULER] PDF generated: {len(pdf_bytes)} bytes")
        
        # Step 5: Generate audio
        print("[SCHEDULER] Generating audio with OpenAI TTS...")
        audio_bytes = text_to_speech_openai(summary, voice="nova")
        print(f"[SCHEDULER] Audio generated: {len(audio_bytes)} bytes")
        
        # Step 6: Send email
        print("[SCHEDULER] Sending email...")
        success = send_news_summary_email(
            summary=summary,
            pdf_bytes=pdf_bytes,
            audio_bytes=audio_bytes
        )
        
        if success:
            print("[SCHEDULER] ✅ Email sent successfully!")
        else:
            print("[SCHEDULER] ❌ Failed to send email")
        
    except Exception as e:
        print(f"[SCHEDULER] Error in scheduled job: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 70)
    print(f"   SCHEDULED NEWS JOB COMPLETED - {datetime.now()}")
    print("=" * 70 + "\n")


def start_scheduler(interval_hours: int = 12) -> bool:
    """
    Start the background scheduler.
    
    Args:
        interval_hours: Hours between each job run (default: 12)
    
    Returns:
        True if scheduler started successfully
    """
    global _scheduler
    
    if _scheduler is not None and _scheduler.running:
        print("[SCHEDULER] Scheduler already running")
        return True
    
    try:
        _scheduler = BackgroundScheduler()
        
        # Add job with interval trigger
        _scheduler.add_job(
            scheduled_news_job,
            trigger=IntervalTrigger(hours=interval_hours),
            id=_job_id,
            name="News Summary Email Job",
            replace_existing=True
        )
        
        _scheduler.start()
        
        next_run = _scheduler.get_job(_job_id).next_run_time
        print(f"[SCHEDULER] ✅ Scheduler started - interval: {interval_hours} hours")
        print(f"[SCHEDULER] Next run: {next_run}")
        
        return True
        
    except Exception as e:
        print(f"[SCHEDULER] Failed to start scheduler: {e}")
        return False


def stop_scheduler() -> bool:
    """Stop the background scheduler."""
    global _scheduler
    
    if _scheduler is None:
        return True
    
    try:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        print("[SCHEDULER] Scheduler stopped")
        return True
    except Exception as e:
        print(f"[SCHEDULER] Error stopping scheduler: {e}")
        return False


def get_scheduler_status() -> dict:
    """Get the current scheduler status."""
    global _scheduler
    
    if _scheduler is None or not _scheduler.running:
        return {
            "running": False,
            "next_run": None,
            "job_count": 0
        }
    
    job = _scheduler.get_job(_job_id)
    
    return {
        "running": True,
        "next_run": str(job.next_run_time) if job else None,
        "job_count": len(_scheduler.get_jobs())
    }


def trigger_job_now() -> bool:
    """Manually trigger the news job immediately."""
    global _scheduler
    
    if _scheduler is None or not _scheduler.running:
        # Run directly if scheduler not running
        print("[SCHEDULER] Running job directly (scheduler not active)")
        scheduled_news_job()
        return True
    
    try:
        _scheduler.get_job(_job_id).modify(next_run_time=datetime.now())
        print("[SCHEDULER] Job triggered manually")
        return True
    except Exception as e:
        print(f"[SCHEDULER] Error triggering job: {e}")
        # Fallback to direct execution
        scheduled_news_job()
        return True
