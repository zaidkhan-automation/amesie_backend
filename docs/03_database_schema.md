# Database Schema (Simple)

Main tables you must remember:

users
- basic identity
- role = CUSTOMER or SELLER

sellers
- linked to users
- store info
- location
- verification status

products
- belongs to seller
- price, stock, meta
- active / deleted flags

orders
- belongs to user
- total, status, payment info

order_items
- products inside an order

cart_items
- temporary holding before order

otp_verifications
- handles registration security

Rule:
Never delete blindly.
Relations matter.

