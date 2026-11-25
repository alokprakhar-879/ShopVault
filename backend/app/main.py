from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routers import (
    admin,
    categories,
    customers,
    inventory,
    orders,
    products,
    reviews,
    wishlists,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="E-commerce & Inventory Management API",
    description=(
        "Production-ready MVP with ACID checkout, SELECT FOR UPDATE locking, "
        "wishlist, reviews (AVG), and admin sales analytics."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(categories.router, prefix="/api")
app.include_router(products.router, prefix="/api")
app.include_router(inventory.router, prefix="/api")
app.include_router(customers.router, prefix="/api")
app.include_router(orders.router, prefix="/api")
app.include_router(wishlists.router, prefix="/api")
app.include_router(reviews.router, prefix="/api")
app.include_router(admin.router, prefix="/api")


@app.get("/")
def root():
    return {
        "message": "E-commerce & Inventory Management API",
        "docs": "/docs",
        "health": "/api/health",
    }


@app.get("/api/health")
def health():
    return {"status": "ok"}
