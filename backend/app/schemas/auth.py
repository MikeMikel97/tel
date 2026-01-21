"""
Authentication schemas
"""
from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserInfo(BaseModel):
    id: int
    username: str
    full_name: str | None
    email: str | None
    role: str
    company_id: int
    
    class Config:
        from_attributes = True
