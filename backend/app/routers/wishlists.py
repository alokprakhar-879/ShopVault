from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas, services
from ..database import get_db

router = APIRouter(prefix="/wishlists", tags=["Wishlists"])


@router.get("", response_model=List[schemas.WishlistOut])
def list_wishlist(
    customer_id: int = Query(...),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(models.Wishlist)
        .options(
            joinedload(models.Wishlist.product).joinedload(models.Product.inventory)
        )
        .filter(models.Wishlist.customer_id == customer_id)
        .order_by(models.Wishlist.added_at.desc())
        .all()
    )
    result = []
    for row in rows:
        qty = row.product.inventory.stock_quantity if row.product.inventory else 0
        reorder = row.product.inventory.reorder_level if row.product.inventory else 5
        _, badge = services.stock_badge(qty, reorder)
        result.append(
            schemas.WishlistOut(
                wishlist_id=row.wishlist_id,
                customer_id=row.customer_id,
                product_id=row.product_id,
                product_name=row.product.name if row.product else None,
                price=row.product.price if row.product else None,
                stock_quantity=qty,
                stock_badge=badge,
                added_at=row.added_at,
            )
        )
    return result


@router.post("", response_model=schemas.WishlistOut, status_code=201)
def add_to_wishlist(payload: schemas.WishlistCreate, db: Session = Depends(get_db)):
    if not db.get(models.Customer, payload.customer_id):
        raise HTTPException(status_code=404, detail="Customer not found")
    product = (
        db.query(models.Product)
        .options(joinedload(models.Product.inventory))
        .filter(models.Product.product_id == payload.product_id)
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    row = models.Wishlist(
        customer_id=payload.customer_id, product_id=payload.product_id
    )
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Already in wishlist")
    db.refresh(row)

    qty = product.inventory.stock_quantity if product.inventory else 0
    reorder = product.inventory.reorder_level if product.inventory else 5
    _, badge = services.stock_badge(qty, reorder)
    return schemas.WishlistOut(
        wishlist_id=row.wishlist_id,
        customer_id=row.customer_id,
        product_id=row.product_id,
        product_name=product.name,
        price=product.price,
        stock_quantity=qty,
        stock_badge=badge,
        added_at=row.added_at,
    )


@router.delete("/{wishlist_id}", status_code=204)
def remove_from_wishlist(wishlist_id: int, db: Session = Depends(get_db)):
    row = db.get(models.Wishlist, wishlist_id)
    if not row:
        raise HTTPException(status_code=404, detail="Wishlist item not found")
    db.delete(row)
    db.commit()
    return None
