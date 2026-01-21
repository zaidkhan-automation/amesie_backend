from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from routers.embeddings import router as embeddings_router
import time
from ws.seller_agent_ws import router as seller_agent_ws_router
from routers.seller_product_image import router as seller_product_image_router
from core.logging_config import setup_logging, get_logger
from core.database import engine
from db import models
from ws.seller_metrics_ws import router as seller_metrics_ws_router
from routers.agent_docs import router as agent_docs_router
# ─────────────────────────────────────────────
# GEO ROUTING IMPORTS AND ROUTER INCLUSION
# ─────────────────────────────────────────────

from geo_routing.routers import routing, poi


from routers import (
    auth,
    products,
    cart,
    orders,
    users,
    sellers,
    orders_history,
    health,   # 👈 router module only
)

# ─────────────────────────────────────────────
# APP SETUP
# ─────────────────────────────────────────────
setup_logging()
logger = get_logger("main")

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Shopease E-commerce Platform",
    version="1.0.0"
)

# ─────────────────────────────────────────────
# MIDDLEWARES
# ─────────────────────────────────────────────
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

# ─────────────────────────────────────────────
# ROUTERS (ONLY ROUTERS, NO INLINE ROUTES)
# ─────────────────────────────────────────────
app.include_router(health.router)  # /health
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(products.router, prefix="/api/products", tags=["products"])
app.include_router(cart.router, prefix="/api/cart", tags=["cart"])
app.include_router(orders.router, prefix="/api/orders", tags=["orders"])
app.include_router(orders_history.router, prefix="/api/orders", tags=["orders-history"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(sellers.router, prefix="/api/sellers", tags=["sellers"])
app.include_router(seller_product_image_router)
app.include_router(seller_metrics_ws_router)
app.include_router(seller_agent_ws_router)
app.include_router(agent_docs_router)
app.include_router(embeddings_router)
# ─────────────────────────────────────────────
# GEO ROUTING ROUTER INCLUSION
# ─────────────────────────────────────────────
app.include_router(routing.router)
app.include_router(poi.router)