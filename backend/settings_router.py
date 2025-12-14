from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from database import get_db
from models import User, UserSettings
from auth import get_current_user

router = APIRouter(prefix="/settings", tags=["Settings"])


# --- Request/Response Models ---

class SettingsResponse(BaseModel):
    categories: List[str]
    notification_email: Optional[str]
    email_enabled: bool
    scheduler_enabled: bool
    scheduler_interval_hours: int
    theme: str
    
    class Config:
        from_attributes = True


class UpdateSettingsRequest(BaseModel):
    categories: Optional[List[str]] = None
    notification_email: Optional[str] = None
    email_enabled: Optional[bool] = None
    scheduler_enabled: Optional[bool] = None
    scheduler_interval_hours: Optional[int] = None
    theme: Optional[str] = None


# --- Endpoints ---

@router.get("/", response_model=SettingsResponse)
def get_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's settings."""
    settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    
    if not settings:
        settings = UserSettings(
            user_id=current_user.id,
            categories=["top_stories", "technology", "business"]
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    
    return SettingsResponse(
        categories=settings.categories or ["top_stories", "technology", "business"],
        notification_email=settings.notification_email,
        email_enabled=settings.email_enabled or False,
        scheduler_enabled=settings.scheduler_enabled or False,
        scheduler_interval_hours=settings.scheduler_interval_hours or 12,
        theme=settings.theme or "light"
    )


@router.put("/", response_model=SettingsResponse)
def update_settings(
    request: UpdateSettingsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's settings."""
    settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    
    if not settings:
        settings = UserSettings(user_id=current_user.id)
        db.add(settings)
    
    if request.categories is not None:
        settings.categories = request.categories
    if request.notification_email is not None:
        settings.notification_email = request.notification_email
    if request.email_enabled is not None:
        settings.email_enabled = request.email_enabled
    if request.scheduler_enabled is not None:
        settings.scheduler_enabled = request.scheduler_enabled
    if request.scheduler_interval_hours is not None:
        settings.scheduler_interval_hours = request.scheduler_interval_hours
    if request.theme is not None:
        settings.theme = request.theme
    
    db.commit()
    db.refresh(settings)
    
    return SettingsResponse(
        categories=settings.categories or ["top_stories", "technology", "business"],
        notification_email=settings.notification_email,
        email_enabled=settings.email_enabled or False,
        scheduler_enabled=settings.scheduler_enabled or False,
        scheduler_interval_hours=settings.scheduler_interval_hours or 12,
        theme=settings.theme or "light"
    )
