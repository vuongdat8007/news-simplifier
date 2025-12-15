"""
Delivery history router - Firebase version.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from auth import get_current_user
import firebase_models as fm

router = APIRouter(prefix="/deliveries", tags=["Deliveries"])


class DeliveryResponse(BaseModel):
    id: str
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


class DeliveryListResponse(BaseModel):
    deliveries: List[DeliveryResponse]
    total: int


@router.get("/", response_model=DeliveryListResponse)
def get_delivery_history(
    limit: int = 10,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """Get user's delivery history."""
    deliveries, total = fm.get_user_delivery_logs(current_user["id"], limit, offset)
    
    return DeliveryListResponse(
        deliveries=[
            DeliveryResponse(
                id=d["id"],
                delivered_at=d.get("delivered_at"),
                categories_used=d.get("categories_used"),
                items_per_category=d.get("items_per_category"),
                word_count_target=d.get("word_count_target"),
                actual_word_count=d.get("actual_word_count"),
                email_sent_to=d.get("email_sent_to"),
                pdf_included=d.get("pdf_included", False),
                audio_included=d.get("audio_included", False),
                feedback_received=d.get("feedback_received"),
                feedback_received_at=d.get("feedback_received_at")
            )
            for d in deliveries
        ],
        total=total
    )


@router.get("/{delivery_id}", response_model=DeliveryResponse)
def get_delivery_detail(
    delivery_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get details of a specific delivery."""
    from firebase_db import get_db
    
    db = get_db()
    doc = db.collection("delivery_logs").document(delivery_id).get()
    
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Delivery not found")
    
    delivery = doc.to_dict()
    
    if delivery.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=404, detail="Delivery not found")
    
    return DeliveryResponse(
        id=doc.id,
        delivered_at=delivery.get("delivered_at"),
        categories_used=delivery.get("categories_used"),
        items_per_category=delivery.get("items_per_category"),
        word_count_target=delivery.get("word_count_target"),
        actual_word_count=delivery.get("actual_word_count"),
        email_sent_to=delivery.get("email_sent_to"),
        pdf_included=delivery.get("pdf_included", False),
        audio_included=delivery.get("audio_included", False),
        feedback_received=delivery.get("feedback_received"),
        feedback_received_at=delivery.get("feedback_received_at")
    )
