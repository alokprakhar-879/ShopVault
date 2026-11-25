from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas, services
from ..database import get_db

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("", response_model=List[schemas.OrderOut])
def list_orders(
    customer_id: int = Query(...),
    db: Session = Depends(get_db),
):
    orders = (
        db.query(models.Order)
        .options(
            joinedload(models.Order.items).joinedload(models.OrderItem.product),
            joinedload(models.Order.payment),
        )
        .filter(models.Order.customer_id == customer_id)
        .order_by(models.Order.order_date.desc())
        .all()
    )
    return [services.serialize_order(o) for o in orders]


@router.get("/{order_id}", response_model=schemas.OrderOut)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = (
        db.query(models.Order)
        .options(
            joinedload(models.Order.items).joinedload(models.OrderItem.product),
            joinedload(models.Order.payment),
        )
        .filter(models.Order.order_id == order_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return services.serialize_order(order)


@router.post("/validate-cart", response_model=schemas.CartValidateResponse)
def validate_cart(payload: schemas.CartValidateRequest, db: Session = Depends(get_db)):
    return services.validate_cart_stock(db, payload.items)


@router.post("/checkout", response_model=schemas.CheckoutResponse)
def checkout(payload: schemas.CheckoutRequest, db: Session = Depends(get_db)):
    return services.checkout(db, payload)


@router.post("/{order_id}/cancel", response_model=schemas.CheckoutResponse)
def cancel_order(order_id: int, db: Session = Depends(get_db)):
    return services.cancel_order(db, order_id)


@router.patch("/{order_id}/status", response_model=schemas.OrderOut)
def update_order_status(
    order_id: int,
    status: str = Query(..., pattern="^(Pending|Shipped|Delivered|Cancelled)$"),
    db: Session = Depends(get_db),
):
    """Admin helper to advance order status for demos."""
    order = db.get(models.Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.order_status == "Cancelled":
        raise HTTPException(status_code=400, detail="Cannot change a cancelled order")
    if status == "Cancelled":
        result = services.cancel_order(db, order_id)
        if not result.success:
            raise HTTPException(status_code=400, detail=result.message)
        return result.order
    order.order_status = status
    db.commit()
    db.refresh(order)
    order = (
        db.query(models.Order)
        .options(
            joinedload(models.Order.items).joinedload(models.OrderItem.product),
            joinedload(models.Order.payment),
        )
        .filter(models.Order.order_id == order_id)
        .first()
    )
    return services.serialize_order(order)
