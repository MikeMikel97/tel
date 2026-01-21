"""
User model
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    email = Column(String(255))
    role = Column(String(50), default='operator')  # 'admin', 'operator'
    
    # WebRTC settings
    sip_username = Column(String(100), unique=True, index=True)
    sip_password = Column(String(100))
    
    # Phone numbers access
    assigned_number_ids = Column(JSON, default=[])
    current_number_id = Column(Integer, ForeignKey("phone_numbers.id"), nullable=True)
    
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    company = relationship("Company", back_populates="users")
    current_number = relationship("PhoneNumber", back_populates="users", foreign_keys=[current_number_id])
    call_sessions = relationship("CallSession", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"
