from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class MessageResponse(BaseModel):
    message: str


# Budgets (BUD-1..BUD-11): typed request/response schemas. Unlike the receipts
# list endpoint (raw dicts, response_model=None), the budget summary is a
# structured payload with a duplication flag (BUD-10), so it gets a real
# response model.
class BudgetCreate(BaseModel):
    period: str
    target_amount: float


class BudgetSummaryResponse(BaseModel):
    period: str
    target_amount: float
    spent: float
    remaining: float
    over: bool
    duplicate_rows: bool = False
