from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional
import re

class UserBase(BaseModel):
    email: str = Field(..., pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    active_balance: float
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class DepositBase(BaseModel):
    amount: float
    date: datetime

class DepositCreate(DepositBase):
    pass

class Deposit(DepositBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class WithdrawalBase(BaseModel):
    amount: float
    date: datetime

class WithdrawalCreate(WithdrawalBase):
    pass

class Withdrawal(WithdrawalBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class DailyEntryBase(BaseModel):
    date: datetime
    profit: float = 0.0
    loss: float = 0.0
    reason_profit: Optional[str] = None
    reason_loss: Optional[str] = None

class DailyEntryCreate(DailyEntryBase):
    pass

class DailyEntry(DailyEntryBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DashboardStats(BaseModel):
    active_balance: float
    total_deposited: float
    total_withdrawn: float
    total_profit: float
    total_loss: float
    total_pnl: float 