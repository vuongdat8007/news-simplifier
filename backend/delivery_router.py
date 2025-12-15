"""
Delivery history router for viewing past email deliveries.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc
from database import get_db
from models import User, EmailDeliveryLog
from auth import get_current_user

router = APIRouter(prefix="/deliveries", tags=["Deliveries"])


class DeliveryResponse(BaseModel):
    id: int
    delivered_at: datetime
    categories_used: Optional[List[str]]
    items_per_category: Optional[int]
    word_count_target: Optional[int]
    actual_word_count: Optional[int]
    email_sent_to: Optional[str]
    pdf_included: bool
    audio_included: bool
    feedback_received: Optional[str]
    feedback_received_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class DeliveryListResponse(BaseModel):
    deliveries: List[DeliveryResponse]
    total: int


@router.get("/", response_model=DeliveryListResponse)
def get_delivery_history(
    limit: int = 10,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's delivery history."""
    
    # Get total count
    total = db.query(EmailDeliveryLog).filter(
        EmailDeliveryLog.user_id == current_user.id
    ).count()
    
    # Get deliveries with pagination
    deliveries = db.query(EmailDeliveryLog).filter(
        EmailDeliveryLog.user_id == current_user.id
    ).order_by(desc(EmailDeliveryLog.delivered_at)).offset(offset).limit(limit).all()
    
    return DeliveryListResponse(
        deliveries=[
            DeliveryResponse(
                id=d.id,
                delivered_at=d.delivered_at,
                categories_used=d.categories_used,
                items_per_category=d.items_per_category,
                word_count_target=d.word_count_target,
                actual_word_count=d.actual_word_count,
                email_sent_to=d.email_sent_to,
                pdf_included=d.pdf_included or False,
                audio_included=d.audio_included or False,
                feedback_received=d.feedback_received,
                feedback_received_at=d.feedback_received_at
            )
            for d in deliveries
        ],
        total=total
    )


@router.get("/{delivery_id}", response_model=DeliveryResponse)
def get_delivery_detail(
    delivery_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get details of a specific delivery."""
    
    delivery = db.query(EmailDeliveryLog).filter(
        EmailDeliveryLog.id == delivery_id,
        EmailDeliveryLog.user_id == current_user.id
    ).first()
    
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    
    return DeliveryResponse(
        id=delivery.id,
        delivered_at=delivery.delivered_at,
        categories_used=delivery.categories_used,
        items_per_category=delivery.items_per_category,
        word_count_target=delivery.word_count_target,
        actual_word_count=delivery.actual_word_count,
        email_sent_to=delivery.email_sent_to,
        pdf_included=delivery.pdf_included or False,
        audio_included=delivery.audio_included or False,
        feedback_received=delivery.feedback_received,
        feedback_received_at=delivery.feedback_received_at
    )
