from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from database import get_db
from models import User, UserSettings
from auth import (
    hash_password, 
    authenticate_user, 
    create_access_token, 
    get_current_user
)

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
    user_id: int
    email: str
    is_admin: bool = False
    is_premium: bool = False


class UserResponse(BaseModel):
    id: int
    email: str
    is_active: bool
    is_admin: bool
    is_premium: bool
    
    class Config:
        from_attributes = True


# --- Endpoints ---

@router.post("/register", response_model=TokenResponse)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user account."""
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate password
    if len(request.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters"
        )
    
    # Check if this is the first user (make them admin)
    user_count = db.query(User).count()
    is_first_user = user_count == 0
    
    # Create user
    hashed_password = hash_password(request.password)
    new_user = User(
        email=request.email,
        password_hash=hashed_password,
        is_admin=is_first_user,  # First user becomes admin
        is_premium=is_first_user  # First user also gets premium
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create default settings for user
    default_settings = UserSettings(
        user_id=new_user.id,
        categories=["top_stories", "technology", "business"]
    )
    db.add(default_settings)
    db.commit()
    
    # Generate token
    access_token = create_access_token(data={"sub": new_user.email})
    
    admin_msg = " (ADMIN)" if is_first_user else ""
    print(f"[AUTH] New user registered: {new_user.email}{admin_msg}")
    
    return TokenResponse(
        access_token=access_token,
        user_id=new_user.id,
        email=new_user.email,
        is_admin=new_user.is_admin,
        is_premium=new_user.is_premium
    )


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login with email and password."""
    # Find user
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    from auth import verify_password
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )
    
    # Generate token
    access_token = create_access_token(data={"sub": user.email})
    
    print(f"[AUTH] User logged in: {user.email}")
    
    return TokenResponse(
        access_token=access_token,
        user_id=user.id,
        email=user.email,
        is_admin=user.is_admin or False,
        is_premium=user.is_premium or False
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user info."""
    return current_user
