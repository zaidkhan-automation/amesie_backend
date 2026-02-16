# Redis & Caching

Redis is used for speed.

Cached things:
- Product lists
- Product detail
- Nearby products

Cache rules:
- Cache on GET
- Invalidate on CREATE/UPDATE/DELETE

If Redis fails:
- Backend should still work
- Cache is optional, DB is source of truth

