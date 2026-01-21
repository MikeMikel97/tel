"""
SIP Trunk model
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class SIPTrunk(Base):
    __tablename__ = "sip_trunks"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name = Column(String(100), nullable=False)
    provider = Column(String(50))  # 'mango', 'beeline', 'custom'
    
    # SIP settings
    server_uri = Column(String(255))
    client_uri = Column(String(255))
    username = Column(String(255))
    password = Column(String(255))
    realm = Column(String(255))
    
    # Additional settings
    enabled = Column(Boolean, default=True)
    config = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    company = relationship("Company", back_populates="sip_trunks")
    phone_numbers = relationship("PhoneNumber", back_populates="trunk")
    call_sessions = relationship("CallSession", back_populates="trunk")

    def __repr__(self):
        return f"<SIPTrunk(id={self.id}, name='{self.name}', provider='{self.provider}')>"
