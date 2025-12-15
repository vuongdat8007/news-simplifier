"""
Firebase Firestore data models and CRUD operations.
"""
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List, Any
from firebase_db import get_db
from google.cloud.firestore_v1 import FieldFilter


# ============================================================================
# USER OPERATIONS
# ============================================================================

def create_user(email: str, password_hash: str) -> Dict[str, Any]:
    """Create a new user."""
    db = get_db()
    
    # Check if email already exists
    existing = db.collection("users").where(
        filter=FieldFilter("email", "==", email)
    ).limit(1).get()
    
    if existing:
        raise ValueError("Email already registered")
    
    user_data = {
        "email": email,
        "password_hash": password_hash,
        "is_active": True,
        "is_admin": False,
        "is_premium": False,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    
    # Create user document
    doc_ref = db.collection("users").document()
    doc_ref.set(user_data)
    
    user_data["id"] = doc_ref.id
    
    # Create default settings
    create_user_settings(doc_ref.id)
    
    return user_data


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user by email address."""
    db = get_db()
    
    docs = db.collection("users").where(
        filter=FieldFilter("email", "==", email)
    ).limit(1).get()
    
    for doc in docs:
        user = doc.to_dict()
        user["id"] = doc.id
        return user
    
    return None


def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user by ID."""
    db = get_db()
    
    doc = db.collection("users").document(user_id).get()
    if doc.exists:
        user = doc.to_dict()
        user["id"] = doc.id
        return user
    
    return None


def get_all_users() -> List[Dict[str, Any]]:
    """Get all users."""
    db = get_db()
    
    users = []
    for doc in db.collection("users").stream():
        user = doc.to_dict()
        user["id"] = doc.id
        users.append(user)
    
    return users


def update_user(user_id: str, updates: Dict[str, Any]) -> bool:
    """Update user fields."""
    db = get_db()
    
    updates["updated_at"] = datetime.now(timezone.utc)
    db.collection("users").document(user_id).update(updates)
    return True


# ============================================================================
# USER SETTINGS OPERATIONS
# ============================================================================

def create_user_settings(user_id: str) -> Dict[str, Any]:
    """Create default settings for a user."""
    db = get_db()
    
    settings_data = {
        "user_id": user_id,
        "categories": ["top_stories", "technology", "business"],
        "sources": [],
        "notification_email": None,
        "email_enabled": False,
        "scheduler_enabled": False,
        "scheduler_interval_hours": 12,
        "max_items_per_category": 5,
        "target_word_count": 500,
        "theme": "light",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    
    db.collection("user_settings").document(user_id).set(settings_data)
    settings_data["id"] = user_id
    return settings_data


def get_user_settings(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user settings."""
    db = get_db()
    
    doc = db.collection("user_settings").document(user_id).get()
    if doc.exists:
        settings = doc.to_dict()
        settings["id"] = doc.id
        return settings
    
    # Create default settings if not exists
    return create_user_settings(user_id)


def update_user_settings(user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Update user settings."""
    db = get_db()
    
    updates["updated_at"] = datetime.now(timezone.utc)
    
    doc_ref = db.collection("user_settings").document(user_id)
    doc = doc_ref.get()
    
    if not doc.exists:
        # Create with defaults + updates
        settings = create_user_settings(user_id)
        settings.update(updates)
        doc_ref.set(settings)
    else:
        doc_ref.update(updates)
    
    return get_user_settings(user_id)


def get_users_with_scheduler_enabled() -> List[Dict[str, Any]]:
    """Get all users who have scheduler enabled."""
    db = get_db()
    
    results = []
    docs = db.collection("user_settings").where(
        filter=FieldFilter("scheduler_enabled", "==", True)
    ).stream()
    
    for doc in docs:
        settings = doc.to_dict()
        user = get_user_by_id(settings["user_id"])
        if user and user.get("is_active", True):
            user["settings"] = settings
            results.append(user)
    
    return results


# ============================================================================
# EMAIL DELIVERY LOG OPERATIONS
# ============================================================================

def create_delivery_log(
    user_id: str,
    email_sent_to: str,
    categories_used: List[str],
    sources_used: List[str] = None,
    items_per_category: int = 5,
    word_count_target: int = 500,
    actual_word_count: int = 0,
    pdf_included: bool = True,
    audio_included: bool = False
) -> Dict[str, Any]:
    """Create an email delivery log entry."""
    db = get_db()
    
    # Generate unique feedback token
    feedback_token = secrets.token_urlsafe(32)
    
    log_data = {
        "user_id": user_id,
        "delivered_at": datetime.now(timezone.utc),
        "categories_used": categories_used,
        "sources_used": sources_used or [],
        "items_per_category": items_per_category,
        "word_count_target": word_count_target,
        "actual_word_count": actual_word_count,
        "email_sent_to": email_sent_to,
        "pdf_included": pdf_included,
        "audio_included": audio_included,
        "feedback_token": feedback_token,
        "feedback_expires_at": datetime.now(timezone.utc) + timedelta(days=7),
        "feedback_received": None,
        "feedback_received_at": None,
    }
    
    doc_ref = db.collection("delivery_logs").document()
    doc_ref.set(log_data)
    
    log_data["id"] = doc_ref.id
    return log_data


def get_delivery_log_by_token(token: str) -> Optional[Dict[str, Any]]:
    """Get delivery log by feedback token."""
    db = get_db()
    
    docs = db.collection("delivery_logs").where(
        filter=FieldFilter("feedback_token", "==", token)
    ).limit(1).get()
    
    for doc in docs:
        log = doc.to_dict()
        log["id"] = doc.id
        return log
    
    return None


def update_delivery_log(log_id: str, updates: Dict[str, Any]) -> bool:
    """Update delivery log."""
    db = get_db()
    db.collection("delivery_logs").document(log_id).update(updates)
    return True


def get_user_delivery_logs(user_id: str, limit: int = 10, offset: int = 0) -> tuple:
    """Get delivery logs for a user with pagination."""
    db = get_db()
    
    # Get total count
    total_docs = db.collection("delivery_logs").where(
        filter=FieldFilter("user_id", "==", user_id)
    ).count().get()
    total = total_docs[0][0].value if total_docs else 0
    
    # Get paginated results
    query = db.collection("delivery_logs").where(
        filter=FieldFilter("user_id", "==", user_id)
    ).order_by("delivered_at", direction="DESCENDING").limit(limit).offset(offset)
    
    logs = []
    for doc in query.stream():
        log = doc.to_dict()
        log["id"] = doc.id
        logs.append(log)
    
    return logs, total


def get_user_last_delivery(user_id: str) -> Optional[Dict[str, Any]]:
    """Get the most recent delivery for a user."""
    db = get_db()
    
    docs = db.collection("delivery_logs").where(
        filter=FieldFilter("user_id", "==", user_id)
    ).order_by("delivered_at", direction="DESCENDING").limit(1).get()
    
    for doc in docs:
        log = doc.to_dict()
        log["id"] = doc.id
        return log
    
    return None
