# Auth & OTP Flow

Simple flow (very important):

1. User/Seller enters email + data
2. Backend sends OTP
3. OTP stored in otp_verifications table
4. User verifies OTP
5. Account is created
6. Login gives JWT token

Why OTP first?
- No fake emails
- No half users
- Clean database

OTP table stores:
- email
- otp_hash
- expiry
- payload (user/seller data)

OTP verify = final step.

