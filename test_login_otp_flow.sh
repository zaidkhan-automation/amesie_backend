#!/bin/bash

BASE_URL="http://127.0.0.1:8001/api/auth"

EMAIL="zaidkhan880000@gmail.com"
PHONE="9616367598"
PASSWORD="StrongPass@123"

echo "=============================="
echo "STEP 1: REGISTER (SEND OTP)"
echo "=============================="

curl -i -X POST "$BASE_URL/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$EMAIL\",
    \"password\": \"$PASSWORD\",
    \"full_name\": \"Zaid Khan Test\",
    \"phone_number\": \"$PHONE\"
  }"

echo
echo "➡️ Check email inbox and note the OTP"
echo "Press ENTER after you have the OTP"
read

echo "Enter OTP:"
read OTP

echo
echo "=============================="
echo "STEP 2: VERIFY OTP"
echo "=============================="

curl -i -X POST "$BASE_URL/verify-otp" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$EMAIL\",
    \"otp\": \"$OTP\",
    \"purpose\": \"auth\"
  }"

echo
echo "=============================="
echo "STEP 3: LOGIN (AFTER OTP VERIFY)"
echo "=============================="

curl -i -X POST "$BASE_URL/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$EMAIL\",
    \"password\": \"$PASSWORD\"
  }"

echo
echo "=============================="
echo "EXPECTED RESULTS"
echo "=============================="
echo "1) Register → 202 OTP sent"
echo "2) Verify OTP → 200 success"
echo "3) Login → 200 + access_token"
