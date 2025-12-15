"""
Settings router - Firebase version.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from auth import get_current_user
import firebase_models as fm

router = APIRouter(prefix="/settings", tags=["Settings"])


# --- Request/Response Models ---

class SettingsResponse(BaseModel):
    categories: List[str]
    sources: List[str]
    notification_email: Optional[str]
    email_enabled: bool
    scheduler_enabled: bool
    scheduler_interval_hours: int
    max_items_per_category: int
    target_word_count: int
    theme: str


class UpdateSettingsRequest(BaseModel):
    categories: Optional[List[str]] = None
    sources: Optional[List[str]] = None
    notification_email: Optional[str] = None
    email_enabled: Optional[bool] = None
    scheduler_enabled: Optional[bool] = None
    scheduler_interval_hours: Optional[int] = None
    max_items_per_category: Optional[int] = None
    theme: Optional[str] = None


# --- Endpoints ---

@router.get("/", response_model=SettingsResponse)
def get_settings(current_user: dict = Depends(get_current_user)):
    """Get current user's settings."""
    settings = fm.get_user_settings(current_user["id"])
    
    return SettingsResponse(
        categories=settings.get("categories", ["top_stories", "technology", "business"]),
        sources=settings.get("sources", []),
        notification_email=settings.get("notification_email"),
        email_enabled=settings.get("email_enabled", False),
        scheduler_enabled=settings.get("scheduler_enabled", False),
        scheduler_interval_hours=settings.get("scheduler_interval_hours", 12),
        max_items_per_category=settings.get("max_items_per_category", 5),
        target_word_count=settings.get("target_word_count", 500),
        theme=settings.get("theme", "light")
    )


@router.put("/", response_model=SettingsResponse)
def update_settings(
    request: UpdateSettingsRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update current user's settings."""
    updates = {}
    
    if request.categories is not None:
        updates["categories"] = request.categories
    if request.sources is not None:
        updates["sources"] = request.sources
    if request.notification_email is not None:
        updates["notification_email"] = request.notification_email
    if request.email_enabled is not None:
        updates["email_enabled"] = request.email_enabled
    if request.scheduler_enabled is not None:
        updates["scheduler_enabled"] = request.scheduler_enabled
    if request.scheduler_interval_hours is not None:
        if request.scheduler_interval_hours not in [6, 12, 24, 48]:
            raise HTTPException(status_code=400, detail="Invalid interval. Must be 6, 12, 24, or 48 hours.")
        updates["scheduler_interval_hours"] = request.scheduler_interval_hours
    if request.max_items_per_category is not None:
        if not 1 <= request.max_items_per_category <= 10:
            raise HTTPException(status_code=400, detail="Max items must be between 1 and 10.")
        updates["max_items_per_category"] = request.max_items_per_category
    if request.theme is not None:
        updates["theme"] = request.theme
    
    settings = fm.update_user_settings(current_user["id"], updates)
    
    return SettingsResponse(
        categories=settings.get("categories", ["top_stories", "technology", "business"]),
        sources=settings.get("sources", []),
        notification_email=settings.get("notification_email"),
        email_enabled=settings.get("email_enabled", False),
        scheduler_enabled=settings.get("scheduler_enabled", False),
        scheduler_interval_hours=settings.get("scheduler_interval_hours", 12),
        max_items_per_category=settings.get("max_items_per_category", 5),
        target_word_count=settings.get("target_word_count", 500),
        theme=settings.get("theme", "light")
    )
