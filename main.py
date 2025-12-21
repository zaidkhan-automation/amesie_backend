from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import time

from core.logging_config import setup_logging, get_logger
from core.database import engine
from db import models
from routers import auth, products, cart, orders, users, sellers, orders_history

setup_logging()
logger = get_logger("main")

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Shopease E-commerce Platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start

    logger.info(
        f"{request.method} {request.url.path} "
        f"{response.status_code} "
        f"{duration:.3f}s "
        f"{request.client.host}"
    )
    return response

@app.get("/health")
def health():
    return {"ok": True}

# ─────────────────────────────────────────────
# ROUTERS (IMPORTANT PART)
# ─────────────────────────────────────────────
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(products.router, prefix="/api/products", tags=["products"])
app.include_router(cart.router, prefix="/api/cart", tags=["cart"])
app.include_router(orders.router, prefix="/api/orders", tags=["orders"])
app.include_router(orders_history.router, prefix="/api/orders", tags=["orders-history"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(sellers.router, prefix="/api/sellers", tags=["sellers"])
