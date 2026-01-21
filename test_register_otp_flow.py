import requests
import time

BASE_URL = "http://127.0.0.1:8001/api/auth"

EMAIL = "silvercity320@gmail.com"
PASSWORD = "ana01011"
FULL_NAME = "ahmed"
PHONE = "1249999999"

def step(title):
    print(f"\n{'='*10} {title} {'='*10}")

# --------------------------------------------------
# STEP 1: REGISTER (AUTO OTP SHOULD SEND)
# --------------------------------------------------
step("STEP 1: Register (Expect OTP Auto Send)")

register_payload = {
    "email": EMAIL,
    "password": PASSWORD,
    "full_name": FULL_NAME,
    "phone_number": PHONE,
}

res = requests.post(f"{BASE_URL}/register", json=register_payload)

print("Status:", res.status_code)
print("Response:", res.json())

if res.status_code != 202:
    raise Exception("❌ Expected 202 OTP sent response")

print("✅ OTP triggered successfully")

# --------------------------------------------------
# MANUAL STEP: USER ENTERS OTP FROM EMAIL
# --------------------------------------------------
step("WAIT FOR OTP (CHECK EMAIL)")
otp = input("👉 Enter OTP received on email: ").strip()

# --------------------------------------------------
# STEP 2: VERIFY OTP
# --------------------------------------------------
step("STEP 2: Verify OTP")

verify_payload = {
    "email": EMAIL,
    "otp": otp,
    "purpose": "auth"
}

res = requests.post(f"{BASE_URL}/verify-otp", json=verify_payload)

print("Status:", res.status_code)
print("Response:", res.json())

if res.status_code != 200:
    raise Exception("❌ OTP verification failed")

print("✅ OTP verified successfully")

# --------------------------------------------------
# STEP 3: REGISTER AGAIN (USER SHOULD BE CREATED)
# --------------------------------------------------
step("STEP 3: Register Again (Create User)")

res = requests.post(f"{BASE_URL}/register", json=register_payload)

print("Status:", res.status_code)
print("Response:", res.json())

if res.status_code != 200:
    raise Exception("❌ User creation failed")

print("✅ User registered successfully")

# --------------------------------------------------
# STEP 4: LOGIN TEST
# --------------------------------------------------
step("STEP 4: Login")

login_payload = {
    "email": EMAIL,
    "password": PASSWORD
}

res = requests.post(f"{BASE_URL}/login", json=login_payload)

print("Status:", res.status_code)
print("Response:", res.json())

if res.status_code != 200:
    raise Exception("❌ Login failed")

print("✅ Login successful")

print("\n🎉 ALL TESTS PASSED. FLOW WORKS END-TO-END.")
