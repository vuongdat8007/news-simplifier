"""
Authentication router - Firebase version.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from auth import (
    hash_password, 
    verify_password,
    create_access_token, 
    get_current_user
)
import firebase_models as fm

router = APIRouter(prefix="/auth", tags=["Authentication"])


# --- Request/Response Models ---

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    is_admin: bool = False
    is_premium: bool = False


class UserResponse(BaseModel):
    id: str
    email: str
    is_active: bool
    is_admin: bool
    is_premium: bool


# --- Endpoints ---

@router.post("/register", response_model=TokenResponse)
def register(request: RegisterRequest):
    """Register a new user account."""
    # Validate password
    if len(request.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters"
        )
    
    # Check if this is the first user (make them admin)
    all_users = fm.get_all_users()
    is_first_user = len(all_users) == 0
    
    # Create user
    hashed_password = hash_password(request.password)
    
    try:
        new_user = fm.create_user(
            email=request.email,
            password_hash=hashed_password
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Update admin/premium status for first user
    if is_first_user:
        fm.update_user(new_user["id"], {
            "is_admin": True,
            "is_premium": True
        })
        new_user["is_admin"] = True
        new_user["is_premium"] = True
    
    # Generate token
    access_token = create_access_token(data={"sub": new_user["email"]})
    
    admin_msg = " (ADMIN)" if is_first_user else ""
    print(f"[AUTH] New user registered: {new_user['email']}{admin_msg}")
    
    return TokenResponse(
        access_token=access_token,
        user_id=new_user["id"],
        email=new_user["email"],
        is_admin=new_user.get("is_admin", False),
        is_premium=new_user.get("is_premium", False)
    )


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest):
    """Login with email and password."""
    # Find user
    user = fm.get_user_by_email(request.email)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_password(request.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )
    
    # Generate token
    access_token = create_access_token(data={"sub": user["email"]})
    
    print(f"[AUTH] User logged in: {user['email']}")
    
    return TokenResponse(
        access_token=access_token,
        user_id=user["id"],
        email=user["email"],
        is_admin=user.get("is_admin", False),
        is_premium=user.get("is_premium", False)
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user info."""
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        is_active=current_user.get("is_active", True),
        is_admin=current_user.get("is_admin", False),
        is_premium=current_user.get("is_premium", False)
    )
