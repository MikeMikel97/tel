"""
Phone Number model
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class PhoneNumber(Base):
    __tablename__ = "phone_numbers"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    trunk_id = Column(Integer, ForeignKey("sip_trunks.id", ondelete="SET NULL"), nullable=True)
    
    number = Column(String(20), unique=True, nullable=False, index=True)
    display_name = Column(String(100))
    is_available = Column(Boolean, default=True)
    assigned_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    company = relationship("Company", back_populates="phone_numbers")
    trunk = relationship("SIPTrunk", back_populates="phone_numbers")
    # Relationship for User.current_number_id (one phone can be current for multiple users)
    users = relationship("User", back_populates="current_number", foreign_keys="User.current_number_id")
    # Relationship for assigned_user_id (one phone assigned to one user)
    assigned_user = relationship("User", foreign_keys=[assigned_user_id], post_update=True, overlaps="users,current_number")

    def __repr__(self):
        return f"<PhoneNumber(id={self.id}, number='{self.number}')>"
