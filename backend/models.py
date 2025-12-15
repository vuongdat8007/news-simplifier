from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, Text
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
    # Relationship to delivery logs
    delivery_logs = relationship("EmailDeliveryLog", back_populates="user")
    
    def __repr__(self):
        return f"<User {self.email}>"


class UserSettings(Base):
    """Per-user settings model."""
    __tablename__ = "user_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # News preferences
    categories = Column(JSON, default=["top_stories", "technology", "business"])
    sources = Column(JSON, default=[])  # Optional specific sources
    
    # Email settings
    notification_email = Column(String(255), nullable=True)
    email_enabled = Column(Boolean, default=False)
    
    # Scheduler settings
    scheduler_enabled = Column(Boolean, default=False)
    scheduler_interval_hours = Column(Integer, default=12)  # 6, 12, 24, 48
    max_items_per_category = Column(Integer, default=5)  # 1-10
    target_word_count = Column(Integer, default=500)  # Adaptive based on feedback
    
    # UI preferences
    theme = Column(String(20), default="light")  # 'light' or 'dark'
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship back to user
    user = relationship("User", back_populates="settings")
    
    def __repr__(self):
        return f"<UserSettings for user_id={self.user_id}>"


class EmailDeliveryLog(Base):
    """Log of email deliveries for tracking and feedback."""
    __tablename__ = "email_delivery_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    delivered_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Settings snapshot at delivery time
    categories_used = Column(JSON)
    sources_used = Column(JSON)
    items_per_category = Column(Integer)
    word_count_target = Column(Integer)
    actual_word_count = Column(Integer)
    
    # Delivery status
    email_sent_to = Column(String(255))
    pdf_included = Column(Boolean, default=True)
    audio_included = Column(Boolean, default=False)
    
    # Feedback mechanism
    feedback_token = Column(String(64), unique=True, index=True)
    feedback_expires_at = Column(DateTime(timezone=True))
    feedback_received = Column(String(20), nullable=True)  # 'too_long', 'just_right', 'too_short'
    feedback_received_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationship back to user
    user = relationship("User", back_populates="delivery_logs")
    
    def __repr__(self):
        return f"<EmailDeliveryLog id={self.id} user_id={self.user_id}>"
