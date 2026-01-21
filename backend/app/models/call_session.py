"""
Call Session model
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class CallSession(Base):
    __tablename__ = "call_sessions"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    trunk_id = Column(Integer, ForeignKey("sip_trunks.id", ondelete="SET NULL"), nullable=True)
    
    # Call details
    direction = Column(String(20))  # 'inbound', 'outbound'
    caller_number = Column(String(20))
    called_number = Column(String(20))
    
    # Timestamps
    started_at = Column(DateTime(timezone=True))
    answered_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    duration = Column(Integer, nullable=True)  # seconds
    
    # Recordings and AI
    recording_path = Column(String(500), nullable=True)
    transcript = Column(Text, nullable=True)
    ai_summary = Column(Text, nullable=True)
    ai_enabled = Column(Boolean, default=True)
    
    # Status
    status = Column(String(50))  # 'ringing', 'active', 'ended', 'failed'
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    company = relationship("Company", back_populates="call_sessions")
    user = relationship("User", back_populates="call_sessions")
    trunk = relationship("SIPTrunk", back_populates="call_sessions")

    def __repr__(self):
        return f"<CallSession(id={self.id}, direction='{self.direction}', status='{self.status}')>"
