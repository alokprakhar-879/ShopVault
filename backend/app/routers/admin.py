import os
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import cast, Date, func
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/admin", tags=["Admin"])

# ---- configurable admin credentials from .env ----
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@shopvault.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
ADMIN_ACCESS_KEY = os.getenv("ADMIN_ACCESS_KEY", "shopvault-secret-key")
LOW_STOCK_THRESHOLD = int(os.getenv("LOW_STOCK_THRESHOLD", "4"))


def verify_admin(x_admin_key: str = Header(...)):
    """Lightweight header-based access gate for the admin dashboard."""
    if x_admin_key != ADMIN_ACCESS_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin access key")


@router.post("/login")
def admin_login(payload: schemas.AdminLoginRequest):
    if (
        payload.email == ADMIN_EMAIL
        and payload.password == ADMIN_PASSWORD
        and payload.access_key == ADMIN_ACCESS_KEY
    ):
        return {"success": True, "access_key": ADMIN_ACCESS_KEY}
    raise HTTPException(status_code=401, detail="Invalid admin credentials")


@router.get("/dashboard", response_model=schemas.AdminDashboard)
def dashboard(db: Session = Depends(get_db), _=Depends(verify_admin)):
    # Revenue only from successful payments
    total_revenue = (
        db.query(func.coalesce(func.sum(models.Payment.amount), 0))
        .filter(models.Payment.payment_status == "Success")
        .scalar()
    )
    total_orders = db.query(func.count(models.Order.order_id)).scalar() or 0
    pending_orders = (
        db.query(func.count(models.Order.order_id))
        .filter(models.Order.order_status == "Pending")
        .scalar()
        or 0
    )

    # Low-stock items (threshold-based)
    low_rows = (
        db.query(models.Inventory)
        .options(joinedload(models.Inventory.product))
        .filter(models.Inventory.stock_quantity <= LOW_STOCK_THRESHOLD)
        .order_by(models.Inventory.stock_quantity.asc())
        .all()
    )
    low_stock_items = [
        schemas.InventoryOut(
            inventory_id=r.inventory_id,
            product_id=r.product_id,
            product_name=r.product.name if r.product else None,
            stock_quantity=r.stock_quantity,
            reorder_level=r.reorder_level,
            last_updated=r.last_updated,
            is_low_stock=True,
        )
        for r in low_rows
    ]

    # ALL inventory items for full view
    all_rows = (
        db.query(models.Inventory)
        .options(joinedload(models.Inventory.product))
        .order_by(models.Inventory.stock_quantity.asc())
        .all()
    )
    all_inventory = [
        schemas.InventoryOut(
            inventory_id=r.inventory_id,
            product_id=r.product_id,
            product_name=r.product.name if r.product else None,
            stock_quantity=r.stock_quantity,
            reorder_level=r.reorder_level,
            last_updated=r.last_updated,
            is_low_stock=r.stock_quantity <= LOW_STOCK_THRESHOLD,
        )
        for r in all_rows
    ]

    # Failed payments audit log (kept in existing payments table)
    failed_rows = (
        db.query(models.Payment)
        .join(models.Order, models.Payment.order_id == models.Order.order_id)
        .join(models.Customer, models.Order.customer_id == models.Customer.customer_id)
        .filter(models.Payment.payment_status == "Failed")
        .order_by(models.Payment.transaction_date.desc())
        .all()
    )
    failed_payments = [
        schemas.AdminPaymentOut(
            payment_id=p.payment_id,
            order_id=p.order_id,
            customer_id=p.order.customer_id if p.order else 0,
            customer_name=p.order.customer.full_name if p.order and p.order.customer else None,
            customer_email=p.order.customer.email if p.order and p.order.customer else None,
            amount=p.amount,
            payment_status=p.payment_status,
            payment_method=p.payment_method,
            transaction_date=p.transaction_date,
        )
        for p in failed_rows
    ]

    # Last 14 days sales trend (successful payments only)
    start = datetime.utcnow().date() - timedelta(days=13)
    daily = (
        db.query(
            cast(models.Payment.transaction_date, Date).label("day"),
            func.coalesce(func.sum(models.Payment.amount), 0).label("revenue"),
            func.count(models.Payment.payment_id).label("order_count"),
        )
        .filter(
            models.Payment.payment_status == "Success",
            cast(models.Payment.transaction_date, Date) >= start,
        )
        .group_by(cast(models.Payment.transaction_date, Date))
        .order_by(cast(models.Payment.transaction_date, Date))
        .all()
    )
    by_day = {str(row.day): row for row in daily}
    sales_trend = []
    for i in range(14):
        d = start + timedelta(days=i)
        key = str(d)
        row = by_day.get(key)
        sales_trend.append(
            schemas.SalesPoint(
                date=key,
                revenue=float(row.revenue) if row else 0.0,
                order_count=int(row.order_count) if row else 0,
            )
        )

    return schemas.AdminDashboard(
        total_revenue=float(total_revenue or 0),
        total_orders=int(total_orders),
        pending_orders=int(pending_orders),
        low_stock_count=len(low_stock_items),
        sales_trend=sales_trend,
        low_stock_items=low_stock_items,
        all_inventory=all_inventory,
        low_stock_threshold=LOW_STOCK_THRESHOLD,
        failed_payments_count=len(failed_payments),
        failed_payments=failed_payments,
    )
