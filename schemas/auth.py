# schemas/auth.py
from typing import Optional
from pydantic import BaseModel, EmailStr


class SellerRegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str

    phone_number: Optional[str] = None

    store_name: str  # REQUIRED
    store_description: Optional[str] = None
    store_address: Optional[str] = None
    business_license: Optional[str] = None
    gst_number: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_ifsc_code: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
