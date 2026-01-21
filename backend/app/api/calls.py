"""
Calls API endpoints
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.deps import get_db, get_current_user
from app.models.call_session import CallSession
from app.models.user import User
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/calls", tags=["calls"])


class CallSessionResponse(BaseModel):
    """Call session response"""
    id: int
    direction: str
    caller_number: str
    called_number: str
    status: str
    started_at: datetime
    answered_at: datetime | None
    ended_at: datetime | None
    duration: int | None
    
    class Config:
        from_attributes = True


@router.get("/history", response_model=List[CallSessionResponse])
def get_call_history(
    limit: int = 50,
    skip: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get call history for current user
    """
    # Получаем звонки пользователя или всей компании (если админ)
    query = db.query(CallSession)
    
    if current_user.role == "operator":
        # Операторы видят только свои звонки
        query = query.filter(CallSession.user_id == current_user.id)
    else:
        # Админы видят все звонки компании
        query = query.filter(CallSession.company_id == current_user.company_id)
    
    calls = query.order_by(desc(CallSession.started_at)).offset(skip).limit(limit).all()
    return calls


@router.get("/stats")
def get_call_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get call statistics for current user
    """
    query = db.query(CallSession)
    
    if current_user.role == "operator":
        query = query.filter(CallSession.user_id == current_user.id)
    else:
        query = query.filter(CallSession.company_id == current_user.company_id)
    
    total_calls = query.count()
    inbound_calls = query.filter(CallSession.direction == "inbound").count()
    outbound_calls = query.filter(CallSession.direction == "outbound").count()
    answered_calls = query.filter(CallSession.answered_at.isnot(None)).count()
    
    return {
        "total": total_calls,
        "inbound": inbound_calls,
        "outbound": outbound_calls,
        "answered": answered_calls,
        "missed": total_calls - answered_calls
    }
