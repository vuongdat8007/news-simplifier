from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from database import get_db
from models import User, UserSettings
from auth import get_current_user

router = APIRouter(prefix="/admin", tags=["Admin"])


# --- Request/Response Models ---

class UserListItem(BaseModel):
    id: int
    email: str
    is_active: bool
    is_admin: bool
    is_premium: bool
    created_at: Optional[str]
    
    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    users: List[UserListItem]
    total: int


class ToggleResponse(BaseModel):
    success: bool
    message: str
    new_value: bool


# --- Admin Dependency ---

def get_admin_user(current_user: User = Depends(get_current_user)):
    """Require current user to be an admin."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


# --- Endpoints ---

@router.get("/users", response_model=UserListResponse)
def list_users(
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """List all users (admin only)."""
    users = db.query(User).order_by(User.id).all()
    
    user_list = []
    for user in users:
        user_list.append(UserListItem(
            id=user.id,
            email=user.email,
            is_active=user.is_active or False,
            is_admin=user.is_admin or False,
            is_premium=user.is_premium or False,
            created_at=str(user.created_at) if user.created_at else None
        ))
    
    return UserListResponse(users=user_list, total=len(user_list))


@router.put("/users/{user_id}/toggle-premium", response_model=ToggleResponse)
def toggle_premium(
    user_id: int,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Toggle premium status for a user (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Can't modify own premium status
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot modify own premium status")
    
    user.is_premium = not (user.is_premium or False)
    db.commit()
    
    status_text = "granted" if user.is_premium else "revoked"
    print(f"[ADMIN] Premium {status_text} for {user.email} by {admin.email}")
    
    return ToggleResponse(
        success=True,
        message=f"Premium status {status_text} for {user.email}",
        new_value=user.is_premium
    )


@router.put("/users/{user_id}/toggle-active", response_model=ToggleResponse)
def toggle_active(
    user_id: int,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Toggle active status for a user (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Can't deactivate self
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")
    
    user.is_active = not (user.is_active if user.is_active is not None else True)
    db.commit()
    
    status_text = "enabled" if user.is_active else "disabled"
    print(f"[ADMIN] Account {status_text} for {user.email} by {admin.email}")
    
    return ToggleResponse(
        success=True,
        message=f"Account {status_text} for {user.email}",
        new_value=user.is_active
    )


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Delete a user (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Can't delete self
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    # Delete user settings first
    settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
    if settings:
        db.delete(settings)
    
    email = user.email
    db.delete(user)
    db.commit()
    
    print(f"[ADMIN] User {email} deleted by {admin.email}")
    
    return {"success": True, "message": f"User {email} deleted"}
