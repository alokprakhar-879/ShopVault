from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas, services
from ..database import get_db

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("", response_model=List[schemas.ProductOut])
def list_products(
    category_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    q = (
        db.query(models.Product)
        .options(
            joinedload(models.Product.inventory),
            joinedload(models.Product.category),
        )
    )
    if category_id is not None:
        q = q.filter(models.Product.category_id == category_id)
    if search:
        q = q.filter(models.Product.name.ilike(f"%{search}%"))
    products = q.order_by(models.Product.product_id).all()
    return [services.enrich_product(db, p) for p in products]


@router.get("/{product_id}", response_model=schemas.ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = (
        db.query(models.Product)
        .options(
            joinedload(models.Product.inventory),
            joinedload(models.Product.category),
        )
        .filter(models.Product.product_id == product_id)
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return services.enrich_product(db, product)


@router.post("", response_model=schemas.ProductOut, status_code=201)
def create_product(payload: schemas.ProductCreate, db: Session = Depends(get_db)):
    category = db.get(models.Category, payload.category_id)
    if not category:
        raise HTTPException(status_code=400, detail="Invalid category_id")

    product = models.Product(
        category_id=payload.category_id,
        name=payload.name,
        price=payload.price,
        description=payload.description,
    )
    db.add(product)
    db.flush()
    db.add(
        models.Inventory(
            product_id=product.product_id,
            stock_quantity=payload.stock_quantity,
            reorder_level=payload.reorder_level,
        )
    )
    db.commit()
    db.refresh(product)
    product = (
        db.query(models.Product)
        .options(
            joinedload(models.Product.inventory),
            joinedload(models.Product.category),
        )
        .filter(models.Product.product_id == product.product_id)
        .first()
    )
    return services.enrich_product(db, product)
