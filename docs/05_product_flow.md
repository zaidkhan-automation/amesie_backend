# Product Flow

Product lifecycle:

1. Seller creates product
2. SKU generated server-side
3. Product stored in DB
4. Images uploaded separately
5. Product listed via GET APIs

Why images separate?
- Images are heavy
- Products are data
- Clean separation

Product GET APIs:
- /api/products
- /api/products/{id}
- cached using Redis

