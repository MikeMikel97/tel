"""Модели данных"""
from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime
from enum import Enum


class CallStatus(str, Enum):
    RINGING = "ringing"
    ANSWERED = "answered"
    ENDED = "ended"


class CallDirection(str, Enum):
    INCOMING = "incoming"
    OUTGOING = "outgoing"


class Call(BaseModel):
    """Информация о звонке"""
    id: str
    caller_number: str
    called_number: str
    direction: CallDirection
    status: CallStatus
    started_at: datetime
    answered_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    operator_extension: str = "1001"


class TranscriptSegment(BaseModel):
    """Сегмент транскрипции"""
    call_id: str
    timestamp: float
    speaker: Literal["operator", "client"]
    text: str
    confidence: float = 1.0


class Suggestion(BaseModel):
    """AI подсказка для оператора"""
    call_id: str
    type: Literal["objection", "upsell", "info", "warning", "script"]
    title: str
    content: str
    priority: Literal["low", "medium", "high"] = "medium"
    created_at: datetime = datetime.now()


class CallEvent(BaseModel):
    """Событие звонка для WebSocket"""
    event_type: Literal["call_start", "call_answer", "call_end", "transcript", "suggestion"]
    call_id: str
    data: dict
