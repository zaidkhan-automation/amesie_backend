from pydantic import BaseModel, EmailStr, Field

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    new_password: str = Field(min_length=8)
class OTPVerifyRequest(BaseModel):
    email: str
    otp: str
    purpose: str
class OTPRequest(BaseModel):
    email: EmailStr
    purpose: str = "auth"


class OTPResendRequest(BaseModel):
    email: EmailStr
    purpose: str = "auth"
