# Backend Architecture

Think backend like a factory.

Frontend → API → Services → Database

Flow:
1. Request comes to FastAPI
2. Router decides what to do
3. Service does business logic
4. DB stores data
5. Redis caches fast stuff

Folders:
- routers/ → API endpoints
- services/ → logic
- db/models → database tables
- schemas/ → request/response shapes
- core/ → auth, db, redis, logging

Rule:
Router should be thin.
Service should think.
DB should store.

