"""Business logic: stock badges, checkout with FOR UPDATE, cancel/restock."""

import os
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from . import models, schemas

LOW_STOCK_THRESHOLD = int(os.getenv("LOW_STOCK_THRESHOLD", "4"))

STATUS_EMOJI = {
    "Pending": "🟡",
    "Shipped": "🔵",
    "Delivered": "🟢",
    "Cancelled": "🔴",
}


def stock_badge(stock_quantity: int, reorder_level: int = 4) -> Tuple[str, str]:
    """Return (status_key, badge_text) computed dynamically from stock_quantity."""
    if stock_quantity <= LOW_STOCK_THRESHOLD:
        if stock_quantity == 0:
            return "out_of_stock", "Out of Stock"
        return "low_stock", f"Low Stock - {stock_quantity} left"
    return "in_stock", f"In Stock - {stock_quantity} left"


def product_avg_rating(db: Session, product_id: int) -> Tuple[Optional[float], int]:
    row = (
        db.query(
            func.avg(models.Review.rating).label("avg_rating"),
            func.count(models.Review.review_id).label("cnt"),
        )
        .filter(models.Review.product_id == product_id)
        .one()
    )
    avg = float(row.avg_rating) if row.avg_rating is not None else None
    return avg, int(row.cnt or 0)


def enrich_product(db: Session, product: models.Product) -> schemas.ProductOut:
    inv = product.inventory
    qty = inv.stock_quantity if inv else 0
    reorder = inv.reorder_level if inv else LOW_STOCK_THRESHOLD
    status, badge = stock_badge(qty, reorder)
    avg, count = product_avg_rating(db, product.product_id)
    return schemas.ProductOut(
        product_id=product.product_id,
        category_id=product.category_id,
        name=product.name,
        price=product.price,
        description=product.description,
        created_at=product.created_at,
        stock_quantity=qty,
        reorder_level=reorder,
        stock_status=status,
        stock_badge=badge,
        average_rating=round(avg, 2) if avg is not None else None,
        review_count=count,
        category_name=product.category.category_name if product.category else None,
    )


def validate_cart_stock(
    db: Session, items: List[schemas.CartItem]
) -> schemas.CartValidateResponse:
    issues: List[schemas.CartValidateIssue] = []
    refreshed: List[schemas.CartItem] = []

    for item in items:
        product = db.get(models.Product, item.product_id)
        if not product or not product.inventory:
            issues.append(
                schemas.CartValidateIssue(
                    product_id=item.product_id,
                    product_name=product.name if product else f"#{item.product_id}",
                    requested=item.quantity,
                    available=0,
                )
            )
            continue

        available = product.inventory.stock_quantity
        if available <= 0:
            issues.append(
                schemas.CartValidateIssue(
                    product_id=item.product_id,
                    product_name=product.name,
                    requested=item.quantity,
                    available=0,
                )
            )
        elif item.quantity > available:
            issues.append(
                schemas.CartValidateIssue(
                    product_id=item.product_id,
                    product_name=product.name,
                    requested=item.quantity,
                    available=available,
                )
            )
            refreshed.append(
                schemas.CartItem(product_id=item.product_id, quantity=available)
            )
        else:
            refreshed.append(item)

    if issues:
        return schemas.CartValidateResponse(
            valid=False,
            message=(
                "Sorry! Someone else just bought these items. "
                "We've updated your cart"
            ),
            issues=issues,
            refreshed_items=refreshed,
        )

    return schemas.CartValidateResponse(
        valid=True, message="Cart stock OK", refreshed_items=refreshed or items
    )


def serialize_order(order: models.Order) -> schemas.OrderOut:
    items = [
        schemas.OrderItemOut(
            order_item_id=i.order_item_id,
            product_id=i.product_id,
            product_name=i.product.name if i.product else None,
            quantity=i.quantity,
            unit_price=i.unit_price,
        )
        for i in order.items
    ]
    payment = None
    if order.payment:
        payment = schemas.PaymentOut.model_validate(order.payment)

    # Order cannot be cancelled if already Cancelled, Shipped, Delivered, or if payment failed
    payment_failed = order.payment and order.payment.payment_status == "Failed"
    can_cancel = (order.order_status == "Pending") and not payment_failed

    return schemas.OrderOut(
        order_id=order.order_id,
        customer_id=order.customer_id,
        order_status=order.order_status,
        total_amount=order.total_amount,
        order_date=order.order_date,
        status_emoji=STATUS_EMOJI.get(order.order_status, ""),
        can_cancel=can_cancel,
        items=items,
        payment=payment,
    )


def checkout(
    db: Session, payload: schemas.CheckoutRequest
) -> schemas.CheckoutResponse:
    """
    ACID checkout with row-level locking:
    1. Lock inventory rows (SELECT ... FOR UPDATE)
    2. Validate stock
    3. Create order + items
    4. If payment fails:
       - Keep failed payment record in Payments table with status='Failed'
       - Link order (status='Cancelled') to customer and payment
       - DO NOT deduct stock
       - Commit transaction so record is preserved for audit
    5. If payment succeeds:
       - Deduct stock
       - Record payment as 'Success'
       - Commit transaction
    """
    customer = db.get(models.Customer, payload.customer_id)
    if not customer:
        return schemas.CheckoutResponse(
            success=False, message="Customer not found"
        )

    if not payload.items:
        return schemas.CheckoutResponse(
            success=False, message="Cart is empty"
        )

    try:
        product_ids = [i.product_id for i in payload.items]
        # Row-level locks to prevent double-booking the last unit
        locked_rows = (
            db.execute(
                select(models.Inventory)
                .where(models.Inventory.product_id.in_(product_ids))
                .with_for_update()
            )
            .scalars()
            .all()
        )
        inv_by_pid = {row.product_id: row for row in locked_rows}

        issues: List[schemas.CartValidateIssue] = []
        refreshed: List[schemas.CartItem] = []
        line_total = Decimal("0.00")
        prepared_lines = []

        for item in payload.items:
            inv = inv_by_pid.get(item.product_id)
            product = db.get(models.Product, item.product_id)
            if not inv or not product:
                issues.append(
                    schemas.CartValidateIssue(
                        product_id=item.product_id,
                        product_name=product.name if product else f"#{item.product_id}",
                        requested=item.quantity,
                        available=0,
                    )
                )
                continue

            if inv.stock_quantity < item.quantity:
                issues.append(
                    schemas.CartValidateIssue(
                        product_id=item.product_id,
                        product_name=product.name,
                        requested=item.quantity,
                        available=inv.stock_quantity,
                    )
                )
                if inv.stock_quantity > 0:
                    refreshed.append(
                        schemas.CartItem(
                            product_id=item.product_id, quantity=inv.stock_quantity
                        )
                    )
                continue

            unit_price = Decimal(product.price)
            prepared_lines.append((product, inv, item.quantity, unit_price))
            line_total += unit_price * item.quantity
            refreshed.append(item)

        if issues:
            db.rollback()
            return schemas.CheckoutResponse(
                success=False,
                message=(
                    "Sorry! Someone else just bought these items. "
                    "We've updated your cart"
                ),
                cart_issues=issues,
            )

        # Handle simulated payment failure:
        # Preserve Order (Cancelled) and Payment (Failed) in DB; do NOT mutate inventory.
        if payload.simulate_payment_failure:
            order = models.Order(
                customer_id=payload.customer_id,
                order_status="Cancelled",
                total_amount=line_total,
                order_date=datetime.utcnow(),
            )
            db.add(order)
            db.flush()

            for product, inv, qty, unit_price in prepared_lines:
                db.add(
                    models.OrderItem(
                        order_id=order.order_id,
                        product_id=product.product_id,
                        quantity=qty,
                        unit_price=unit_price,
                    )
                )
                # Stock is NOT deducted for failed payments!

            payment = models.Payment(
                order_id=order.order_id,
                amount=line_total,
                payment_status="Failed",
                payment_method=payload.payment_method,
                transaction_date=datetime.utcnow(),
            )
            db.add(payment)
            db.commit()
            db.refresh(order)

            order = (
                db.query(models.Order)
                .filter(models.Order.order_id == order.order_id)
                .first()
            )
            return schemas.CheckoutResponse(
                success=False,
                message=(
                    "Payment failed. Order recorded as Cancelled with Payment 'Failed'; "
                    "inventory was not deducted and remains safe."
                ),
                order=serialize_order(order),
            )

        # Normal successful checkout path:
        order = models.Order(
            customer_id=payload.customer_id,
            order_status="Pending",
            total_amount=line_total,
            order_date=datetime.utcnow(),
        )
        db.add(order)
        db.flush()

        for product, inv, qty, unit_price in prepared_lines:
            db.add(
                models.OrderItem(
                    order_id=order.order_id,
                    product_id=product.product_id,
                    quantity=qty,
                    unit_price=unit_price,
                )
            )
            inv.stock_quantity -= qty
            inv.last_updated = datetime.utcnow()

        payment = models.Payment(
            order_id=order.order_id,
            amount=line_total,
            payment_status="Success",
            payment_method=payload.payment_method,
            transaction_date=datetime.utcnow(),
        )
        db.add(payment)
        db.commit()
        db.refresh(order)

        order = (
            db.query(models.Order)
            .filter(models.Order.order_id == order.order_id)
            .first()
        )
        return schemas.CheckoutResponse(
            success=True,
            message="Order placed successfully!",
            order=serialize_order(order),
        )

    except Exception as exc:
        db.rollback()
        return schemas.CheckoutResponse(
            success=False, message=f"Checkout failed: {exc}"
        )


def cancel_order(db: Session, order_id: int) -> schemas.CheckoutResponse:
    """
    Pending -> cancel + restock (with FOR UPDATE).
    Shipped/Delivered -> reject with return message.
    """
    try:
        order = (
            db.execute(
                select(models.Order)
                .where(models.Order.order_id == order_id)
                .with_for_update()
            )
            .scalars()
            .first()
        )
        if not order:
            return schemas.CheckoutResponse(
                success=False, message="Order not found"
            )

        if order.order_status in ("Shipped", "Delivered"):
            return schemas.CheckoutResponse(
                success=False,
                message=(
                    "This order has already shipped. "
                    "Please request a return instead"
                ),
                order=serialize_order(order),
            )

        if order.order_status == "Cancelled":
            return schemas.CheckoutResponse(
                success=False,
                message="Order is already cancelled",
                order=serialize_order(order),
            )

        # Do not restock if payment had failed (stock was never deducted)
        if order.payment and order.payment.payment_status == "Failed":
            order.order_status = "Cancelled"
            db.commit()
            db.refresh(order)
            return schemas.CheckoutResponse(
                success=True,
                message="Order cancelled (no restock needed as payment had failed)",
                order=serialize_order(order),
            )

        # Restock loop under row locks
        product_ids = [item.product_id for item in order.items]
        if product_ids:
            locked = (
                db.execute(
                    select(models.Inventory)
                    .where(models.Inventory.product_id.in_(product_ids))
                    .with_for_update()
                )
                .scalars()
                .all()
            )
            inv_map = {row.product_id: row for row in locked}
            for item in order.items:
                inv = inv_map.get(item.product_id)
                if inv:
                    inv.stock_quantity += item.quantity
                    inv.last_updated = datetime.utcnow()

        order.order_status = "Cancelled"
        db.commit()
        db.refresh(order)
        return schemas.CheckoutResponse(
            success=True,
            message="Order cancelled and inventory restocked",
            order=serialize_order(order),
        )
    except Exception as exc:
        db.rollback()
        return schemas.CheckoutResponse(
            success=False, message=f"Cancel failed: {exc}"
        )
