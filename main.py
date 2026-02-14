from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import time
from routers.agent_session import router as agent_session_router
from core.logging_config import setup_logging, get_logger
from core.database import engine
from db import models

from routers import (
    auth,
    products,
    cart,
    orders,
    users,
    sellers,
    orders_history,
    health,
    product_images,
    categories,
    search,
)

from routers.embeddings import router as embeddings_router
from ws.seller_agent_ws import router as seller_agent_ws_router
from ws.seller_metrics_ws import router as seller_metrics_ws_router
from routers.agent_docs import router as agent_docs_router
from geo_routing.routers import routing, poi


# ─────────────────────────────────────────────
# SETUP
# ─────────────────────────────────────────────
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
    logger.info(
        f"{request.method} {request.url.path} "
        f"{response.status_code} "
        f"{time.time() - start:.3f}s"
    )
    return response


# ─────────────────────────────────────────────
# ROUTERS
# ─────────────────────────────────────────────
app.include_router(health.router)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(products.router, prefix="/api/products", tags=["products"])
app.include_router(cart.router, prefix="/api/cart", tags=["cart"])
app.include_router(orders.router, prefix="/api/orders", tags=["orders"])
app.include_router(orders_history.router, prefix="/api/orders", tags=["orders-history"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(sellers.router, prefix="/api/sellers", tags=["sellers"])

app.include_router(product_images.router)
app.include_router(categories.router, prefix="/api/categories", tags=["categories"])
app.include_router(agent_session_router)
app.include_router(seller_metrics_ws_router)
app.include_router(seller_agent_ws_router)
app.include_router(agent_docs_router)

app.include_router(embeddings_router)

# IMPORTANT: search is mounted WITHOUT prefix
# So endpoint is:
# GET /search?q=shoe
app.include_router(search.router)

app.include_router(routing.router)
app.include_router(poi.router)
