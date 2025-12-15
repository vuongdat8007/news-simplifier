"""
Per-user scheduler service - Firebase version.
Handles individual user schedules, premium audio generation, and feedback-based word count adaptation.
"""
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from dotenv import load_dotenv

load_dotenv()

# Global scheduler instance
_scheduler: Optional[BackgroundScheduler] = None


def get_scheduler() -> Optional[BackgroundScheduler]:
    """Get the scheduler instance."""
    return _scheduler


def generate_feedback_token() -> str:
    """Generate a unique token for email feedback."""
    return secrets.token_urlsafe(32)


def process_user_digest(user_id: str):
    """
    Process and send news digest for a single user.
    
    This function:
    1. Loads user settings from Firebase
    2. Fetches news by user's categories/sources
    3. Limits to max_items_per_category
    4. Generates summary with target_word_count
    5. Creates PDF
    6. If premium: generates audio
    7. Sends email with feedback buttons
    8. Logs delivery to Firebase
    """
    print(f"\n{'='*70}")
    print(f"   PROCESSING DIGEST FOR USER {user_id} - {datetime.now()}")
    print(f"{'='*70}")
    
    try:
        import firebase_models as fm
        from services.news_fetcher import fetch_news_by_categories, fetch_news_by_sources
        from services.openai_service import summarize_combined_excerpts_with_word_limit
        from services.pdf_service import create_pdf
        from services.tts_service import text_to_speech_openai
        from services.sendgrid_service import send_summary_email_with_feedback
        from bs4 import BeautifulSoup
        
        # Load user and settings
        user = fm.get_user_by_id(user_id)
        if not user:
            print(f"[SCHEDULER] User {user_id} not found")
            return
        
        settings = fm.get_user_settings(user_id)
        if not settings:
            print(f"[SCHEDULER] No settings for user {user_id}")
            return
        
        if not settings.get("scheduler_enabled", False):
            print(f"[SCHEDULER] Scheduler disabled for user {user_id}")
            return
        
        if not settings.get("notification_email"):
            print(f"[SCHEDULER] No notification email for user {user_id}")
            return
        
        print(f"[SCHEDULER] User: {user['email']}")
        print(f"[SCHEDULER] Settings: interval={settings.get('scheduler_interval_hours', 12)}h, max_items={settings.get('max_items_per_category', 5)}, word_count={settings.get('target_word_count', 500)}")
        
        # Fetch news based on categories and sources
        articles = []
        max_items = settings.get("max_items_per_category", 5)
        
        if settings.get("categories"):
            print(f"[SCHEDULER] Fetching from categories: {settings['categories']}")
            cat_articles = fetch_news_by_categories(
                settings["categories"], 
                max_per_category=max_items
            )
            articles.extend(cat_articles)
        
        if settings.get("sources"):
            print(f"[SCHEDULER] Fetching from sources: {settings['sources']}")
            src_articles = fetch_news_by_sources(
                settings["sources"],
                max_per_source=max_items
            )
            articles.extend(src_articles)
        
        if not articles:
            print(f"[SCHEDULER] No articles found for user {user_id}")
            return
        
        print(f"[SCHEDULER] Collected {len(articles)} articles")
        
        # Build combined excerpts
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
        
        # Generate AI summary with word limit
        target_word_count = settings.get("target_word_count", 500)
        print(f"[SCHEDULER] Generating AI summary (target: {target_word_count} words)...")
        summary = summarize_combined_excerpts_with_word_limit(
            combined_text, 
            target_word_count=target_word_count
        )
        
        if not summary:
            print(f"[SCHEDULER] Failed to generate summary for user {user_id}")
            return
        
        actual_word_count = len(summary.split())
        print(f"[SCHEDULER] Summary generated: {actual_word_count} words")
        
        # Create PDF
        print("[SCHEDULER] Generating PDF...")
        pdf_bytes = create_pdf(summary, "AI News Summary")
        print(f"[SCHEDULER] PDF generated: {len(pdf_bytes)} bytes")
        
        # Generate audio only for premium users
        audio_bytes = None
        if user.get("is_premium", False):
            print("[SCHEDULER] Premium user - generating audio...")
            audio_bytes = text_to_speech_openai(summary, voice="nova")
            print(f"[SCHEDULER] Audio generated: {len(audio_bytes)} bytes")
        else:
            print("[SCHEDULER] Non-premium user - skipping audio")
        
        # Generate feedback token
        feedback_token = generate_feedback_token()
        
        # Send email with feedback links
        notification_email = settings["notification_email"]
        print(f"[SCHEDULER] Sending email to {notification_email}...")
        success, message = send_summary_email_with_feedback(
            to_email=notification_email,
            summary_text=summary,
            pdf_bytes=pdf_bytes,
            audio_bytes=audio_bytes,
            feedback_token=feedback_token
        )
        
        if success:
            print(f"[SCHEDULER] ✅ Email sent to {notification_email}")
            
            # Log delivery to Firebase
            delivery_log = fm.create_delivery_log(
                user_id=user_id,
                email_sent_to=notification_email,
                categories_used=settings.get("categories", []),
                sources_used=settings.get("sources", []),
                items_per_category=max_items,
                word_count_target=target_word_count,
                actual_word_count=actual_word_count,
                pdf_included=True,
                audio_included=audio_bytes is not None
            )
            print(f"[SCHEDULER] Delivery logged (id={delivery_log['id']})")
        else:
            print(f"[SCHEDULER] ❌ Failed to send email: {message}")
    
    except Exception as e:
        print(f"[SCHEDULER] Error processing user {user_id}: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"{'='*70}")
    print(f"   COMPLETED DIGEST FOR USER {user_id}")
    print(f"{'='*70}\n")


def run_all_user_digests():
    """
    Run digests for all users with enabled schedulers.
    This is called periodically by the master scheduler.
    """
    print("\n" + "=" * 70)
    print(f"   SCHEDULED JOB: PROCESSING ALL USER DIGESTS - {datetime.now()}")
    print("=" * 70)
    
    try:
        import firebase_models as fm
        
        # Get all users with enabled schedulers
        enabled_users = fm.get_users_with_scheduler_enabled()
        
        print(f"[SCHEDULER] Found {len(enabled_users)} users with enabled schedulers")
        
        for user in enabled_users:
            try:
                process_user_digest(user["id"])
            except Exception as e:
                print(f"[SCHEDULER] Error processing user {user['id']}: {e}")
                continue
    
    except Exception as e:
        print(f"[SCHEDULER] Error in run_all_user_digests: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 70)
    print(f"   ALL USER DIGESTS COMPLETED - {datetime.now()}")
    print("=" * 70 + "\n")


def start_scheduler(interval_hours: int = 1) -> bool:
    """
    Start the background scheduler.
    
    The scheduler runs every hour and checks which users need their digest
    based on their individual interval settings and last delivery time.
    """
    global _scheduler
    
    if _scheduler is not None and _scheduler.running:
        print("[SCHEDULER] Scheduler already running")
        return True
    
    try:
        _scheduler = BackgroundScheduler()
        
        # Run every hour to check user schedules
        _scheduler.add_job(
            check_user_schedules,
            trigger=IntervalTrigger(hours=interval_hours),
            id="user_schedule_check",
            name="User Schedule Check Job",
            replace_existing=True
        )
        
        _scheduler.start()
        
        next_run = _scheduler.get_job("user_schedule_check").next_run_time
        print(f"[SCHEDULER] ✅ Scheduler started - checking every {interval_hours} hour(s)")
        print(f"[SCHEDULER] Next check: {next_run}")
        
        return True
        
    except Exception as e:
        print(f"[SCHEDULER] Failed to start scheduler: {e}")
        return False


def check_user_schedules():
    """
    Check which users are due for their digest and process them.
    """
    print(f"\n[SCHEDULER] Checking user schedules at {datetime.now()}")
    
    try:
        import firebase_models as fm
        
        # Get all users with enabled schedulers
        enabled_users = fm.get_users_with_scheduler_enabled()
        
        print(f"[SCHEDULER] {len(enabled_users)} users with enabled scheduling")
        
        for user in enabled_users:
            settings = user.get("settings", {})
            
            # Check last delivery for this user
            last_delivery = fm.get_user_last_delivery(user["id"])
            
            needs_digest = False
            interval_hours = settings.get("scheduler_interval_hours", 12)
            
            if last_delivery is None:
                # Never delivered, send now
                needs_digest = True
                print(f"[SCHEDULER] User {user['id']}: No previous delivery, needs digest")
            else:
                # Check if interval has passed
                delivered_at = last_delivery.get("delivered_at")
                if delivered_at:
                    # Handle timezone-aware datetime
                    now = datetime.now(timezone.utc)
                    if hasattr(delivered_at, 'tzinfo') and delivered_at.tzinfo is None:
                        delivered_at = delivered_at.replace(tzinfo=timezone.utc)
                    hours_since = (now - delivered_at).total_seconds() / 3600
                    
                    if hours_since >= interval_hours:
                        needs_digest = True
                        print(f"[SCHEDULER] User {user['id']}: {hours_since:.1f}h since last delivery, needs digest")
                    else:
                        print(f"[SCHEDULER] User {user['id']}: {hours_since:.1f}h since last delivery, waiting")
            
            if needs_digest:
                process_user_digest(user["id"])
    
    except Exception as e:
        print(f"[SCHEDULER] Error checking schedules: {e}")
        import traceback
        traceback.print_exc()


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
    
    job = _scheduler.get_job("user_schedule_check")
    
    return {
        "running": True,
        "next_run": str(job.next_run_time) if job else None,
        "job_count": len(_scheduler.get_jobs())
    }


def trigger_user_job(user_id: str) -> bool:
    """Manually trigger the news job for a specific user."""
    try:
        print(f"[SCHEDULER] Manually triggering job for user {user_id}")
        process_user_digest(user_id)
        return True
    except Exception as e:
        print(f"[SCHEDULER] Error triggering job for user {user_id}: {e}")
        return False


# Legacy function for backwards compatibility
def trigger_job_now() -> bool:
    """Manually trigger the scheduled news email job for all users."""
    print("[SCHEDULER] Running job for all users (legacy trigger)")
    run_all_user_digests()
    return True
