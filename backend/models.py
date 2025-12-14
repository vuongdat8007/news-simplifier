from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class User(Base):
    """User account model."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    is_premium = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship to settings
    settings = relationship("UserSettings", back_populates="user", uselist=False)
    
    def __repr__(self):
        return f"<User {self.email}>"


class UserSettings(Base):
    """Per-user settings model."""
    __tablename__ = "user_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # News preferences
    categories = Column(JSON, default=["top_stories", "technology", "business"])
    
    # Email settings
    notification_email = Column(String(255), nullable=True)
    email_enabled = Column(Boolean, default=False)
    
    # Scheduler settings
    scheduler_enabled = Column(Boolean, default=False)
    scheduler_interval_hours = Column(Integer, default=12)
    
    # UI preferences
    theme = Column(String(20), default="light")  # 'light' or 'dark'
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship back to user
    user = relationship("User", back_populates="settings")
    
    def __repr__(self):
        return f"<UserSettings for user_id={self.user_id}>"
