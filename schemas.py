"""Pydantic request/response models -> FastAPI uses these to validate input or output."""
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


# ---------- Auth ----------

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str
    created_at: str


# ---------- Tickets ----------

class TicketCreateRequest(BaseModel):
    message: str = Field(min_length=1)
    order_value_inr: Optional[float] = None
    days_since_delivery: Optional[int] = None
    days_since_dispatch: Optional[int] = None
    product_type: Optional[str] = None      
    opened_status: Optional[str] = None     
    order_status: Optional[str] = None      


class DecisionResponse(BaseModel):
    action: str
    reason: str
    confidence: float
    sources: list[str]


class TicketResponse(BaseModel):
    id: int
    user_id: int
    message: str
    created_at: str
    decision: Optional[DecisionResponse] = None
