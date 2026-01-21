#!/bin/bash

URL="http://76.13.17.48:8001/api/auth/login"
EMAIL="zaidkhanx3009@gmail.com"
PASSWORD="Reset@12345"

RESPONSE=$(curl -s -X POST "$URL" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "'"$EMAIL"'",
    "password": "'"$PASSWORD"'"
  }')

ACCESS_TOKEN=$(echo "$RESPONSE" | jq -r '.access_token')

if [ "$ACCESS_TOKEN" = "null" ] || [ -z "$ACCESS_TOKEN" ]; then
  echo "Login failed"
  echo "$RESPONSE"
  exit 1
fi

echo "Login successful"
echo "Access Token:"
echo "$ACCESS_TOKEN"
