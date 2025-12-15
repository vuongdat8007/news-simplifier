"""
Admin router - Firebase version.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional

from auth import get_current_user
import firebase_models as fm

router = APIRouter(prefix="/admin", tags=["Admin"])


# --- Request/Response Models ---

class UserListItem(BaseModel):
    id: str
    email: str
    is_active: bool
    is_admin: bool
    is_premium: bool
    created_at: Optional[str]


class UserListResponse(BaseModel):
    users: List[UserListItem]
    total: int


class ToggleResponse(BaseModel):
    success: bool
    message: str
    new_value: bool


# --- Admin Dependency ---

def get_admin_user(current_user: dict = Depends(get_current_user)):
    """Require current user to be an admin."""
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


# --- Endpoints ---

@router.get("/users", response_model=UserListResponse)
def list_users(admin: dict = Depends(get_admin_user)):
    """List all users (admin only)."""
    users = fm.get_all_users()
    
    user_list = [
        UserListItem(
            id=user["id"],
            email=user["email"],
            is_active=user.get("is_active", True),
            is_admin=user.get("is_admin", False),
            is_premium=user.get("is_premium", False),
            created_at=str(user.get("created_at")) if user.get("created_at") else None
        )
        for user in users
    ]
    
    return UserListResponse(users=user_list, total=len(user_list))


@router.put("/users/{user_id}/toggle-premium", response_model=ToggleResponse)
def toggle_premium(user_id: str, admin: dict = Depends(get_admin_user)):
    """Toggle premium status for a user (admin only)."""
    user = fm.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user["id"] == admin["id"]:
        raise HTTPException(status_code=400, detail="Cannot modify own premium status")
    
    new_value = not user.get("is_premium", False)
    fm.update_user(user_id, {"is_premium": new_value})
    
    status_text = "granted" if new_value else "revoked"
    print(f"[ADMIN] Premium {status_text} for {user['email']} by {admin['email']}")
    
    return ToggleResponse(
        success=True,
        message=f"Premium status {status_text} for {user['email']}",
        new_value=new_value
    )


@router.put("/users/{user_id}/toggle-active", response_model=ToggleResponse)
def toggle_active(user_id: str, admin: dict = Depends(get_admin_user)):
    """Toggle active status for a user (admin only)."""
    user = fm.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user["id"] == admin["id"]:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")
    
    new_value = not user.get("is_active", True)
    fm.update_user(user_id, {"is_active": new_value})
    
    status_text = "enabled" if new_value else "disabled"
    print(f"[ADMIN] Account {status_text} for {user['email']} by {admin['email']}")
    
    return ToggleResponse(
        success=True,
        message=f"Account {status_text} for {user['email']}",
        new_value=new_value
    )


@router.delete("/users/{user_id}")
def delete_user(user_id: str, admin: dict = Depends(get_admin_user)):
    """Delete a user (admin only)."""
    from firebase_db import get_db
    
    user = fm.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user["id"] == admin["id"]:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    db = get_db()
    
    # Delete user settings
    db.collection("user_settings").document(user_id).delete()
    
    # Delete user
    email = user["email"]
    db.collection("users").document(user_id).delete()
    
    print(f"[ADMIN] User {email} deleted by {admin['email']}")
    
    return {"success": True, "message": f"User {email} deleted"}
