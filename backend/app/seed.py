"""Seed sample data for demos and DBMS project walkthroughs."""

import os
import random
import sys
from datetime import datetime, timedelta
from decimal import Decimal

from dotenv import load_dotenv
from sqlalchemy.orm import Session

from . import models
from .database import Base, SessionLocal, engine

load_dotenv()

SEED_HISTORICAL_DAYS = int(os.getenv("SEED_HISTORICAL_DAYS", "30"))
SEED_RECORD_COUNT = int(os.getenv("SEED_RECORD_COUNT", "25"))


def reset_database(db: Session) -> None:
    """Safely wipe existing records in FK dependency order."""
    print("Resetting database records...")
    db.query(models.Payment).delete()
    db.query(models.OrderItem).delete()
    db.query(models.Order).delete()
    db.query(models.Review).delete()
    db.query(models.Wishlist).delete()
    db.query(models.Inventory).delete()
    db.query(models.Product).delete()
    db.query(models.Customer).delete()
    db.query(models.Category).delete()
    db.commit()


def seed(db: Session, reset: bool = False) -> None:
    if reset:
        reset_database(db)
    elif db.query(models.Order).count() > 0:
        print(
            "Database already seeded with historical records. "
            "To re-seed, run: python -m app.seed --reset"
        )
        return

    # Deterministic pseudo-random seed for repeatable demo data
    rng = random.Random(42)
    now = datetime.utcnow()

    # 1. Categories
    categories_data = [
        ("Electronics", "Gadgets, accessories, and smart devices"),
        ("Apparel", "Clothing, footwear, and everyday wear"),
        ("Home & Kitchen", "Cookware, appliances, and decor"),
        ("Books", "Fiction, textbooks, and technical reference"),
        ("Fitness & Outdoor", "Sporting goods, trackers, and outdoor gear"),
    ]
    categories = [
        models.Category(category_name=name, description=desc)
        for name, desc in categories_data
    ]
    db.add_all(categories)
    db.flush()

    # 2. Products & Inventory
    catalog = [
        # name, cat_idx, price, stock, reorder, description
        ("Wireless Earbuds Pro", 0, "2499.00", 35, 5, "Noise-cancelling Bluetooth earbuds"),
        ("USB-C Hub 7-in-1", 0, "1899.00", 3, 5, "Multi-port aluminum adapter (Low Stock)"),
        ("Mechanical Keyboard", 0, "4599.00", 0, 5, "RGB mechanical board (Out of Stock)"),
        ("4K Action Camera", 0, "9999.00", 18, 5, "Waterproof sports action cam"),
        ("Classic Cotton Tee", 1, "599.00", 95, 10, "Soft unisex crew-neck cotton tee"),
        ("Denim Jacket", 1, "2499.00", 2, 5, "Vintage wash rugged denim jacket (Low Stock)"),
        ("Running Sneakers", 1, "3499.00", 24, 8, "Lightweight breathable runners"),
        ("Ceramic Mug Set", 2, "799.00", 50, 10, "Set of 4 matte ceramic mugs"),
        ("Non-stick Pan 28cm", 2, "1299.00", 4, 5, "Scratch-resistant frying pan (Low Stock)"),
        ("LED Desk Lamp", 2, "1599.00", 14, 5, "Dimmable touch-control lamp"),
        ("Intro to Databases", 3, "899.00", 30, 8, "SQL, normalization & ACID transactions"),
        ("System Design Primer", 3, "699.00", 1, 5, "Distributed architecture notes (Low Stock)"),
        ("Adjustable Dumbbells", 4, "4999.00", 12, 5, "Quick-lock selector dumbbell set"),
        ("Yoga Mat Extra Thick", 4, "1199.00", 28, 6, "Eco-friendly high-density mat"),
    ]

    products = []
    for name, cat_idx, price, stock, reorder, desc in catalog:
        p = models.Product(
            category_id=categories[cat_idx].category_id,
            name=name,
            price=Decimal(price),
            description=desc,
            created_at=now - timedelta(days=SEED_HISTORICAL_DAYS + 10),
        )
        db.add(p)
        db.flush()
        db.add(
            models.Inventory(
                product_id=p.product_id,
                stock_quantity=stock,
                reorder_level=reorder,
                last_updated=now - timedelta(days=rng.randint(0, 5)),
            )
        )
        products.append(p)

    # 3. Customers
    customers_data = [
        ("Aisha Khan", "aisha@example.com", "+91-90000-11111", "12 MG Road, Bengaluru"),
        ("Rohan Mehta", "rohan@example.com", "+91-90000-22222", "88 Park Street, Mumbai"),
        ("Priya Sharma", "priya@example.com", "+91-90000-33333", "45 Connaught Place, New Delhi"),
        ("Vikram Patel", "vikram@example.com", "+91-90000-44444", "19 SV Road, Ahmedabad"),
        ("Admin Demo", "admin@example.com", "+91-90000-00000", "ShopVault HQ"),
    ]
    customers = [
        models.Customer(
            full_name=fn,
            email=em,
            phone=ph,
            address=addr,
            registered_at=now - timedelta(days=SEED_HISTORICAL_DAYS + 5),
        )
        for fn, em, ph, addr in customers_data
    ]
    db.add_all(customers)
    db.flush()

    # 4. Reviews
    reviews_data = [
        (0, 0, 5, "Crystal clear sound and phenomenal battery life!"),
        (1, 0, 4, "Comfortable fit. Charging case is slightly bulky."),
        (2, 0, 5, "Best earbuds in this price range by far."),
        (0, 4, 5, "Soft high-grade fabric, fits true to size."),
        (1, 10, 5, "Clear SQL explanations, helped immensely in DBMS exams."),
        (2, 10, 5, "A must-read for database locking and normalization concepts."),
        (3, 7, 4, "Nice ceramic finish, good heat retention."),
        (0, 9, 4, "Sleek desk lamp with excellent color temperatures."),
        (1, 12, 5, "Sturdy dumbbells, seamless weight switching."),
    ]
    for c_idx, p_idx, rating, comment in reviews_data:
        db.add(
            models.Review(
                customer_id=customers[c_idx].customer_id,
                product_id=products[p_idx].product_id,
                rating=rating,
                comment=comment,
                created_at=now - timedelta(days=rng.randint(2, SEED_HISTORICAL_DAYS)),
            )
        )

    # 5. Wishlists
    wishlists_data = [(0, 3), (0, 6), (1, 1), (1, 12), (2, 0), (2, 10)]
    for c_idx, p_idx in wishlists_data:
        db.add(
            models.Wishlist(
                customer_id=customers[c_idx].customer_id,
                product_id=products[p_idx].product_id,
                added_at=now - timedelta(days=rng.randint(1, SEED_HISTORICAL_DAYS)),
            )
        )

    # 6. Historical Orders, Items & Payments
    # Configured by SEED_HISTORICAL_DAYS and SEED_RECORD_COUNT
    payment_methods = ["UPI", "Credit Card", "PayPal"]
    regular_customers = customers[:4]  # non-admin customers

    # Reserve specific indices for realistic status variety and failed payment demonstrations:
    # E.g. ~60% Delivered, ~15% Shipped, ~15% Pending, ~10% Cancelled / Failed Payments
    for i in range(SEED_RECORD_COUNT):
        customer = regular_customers[i % len(regular_customers)]

        # Time distribution: distribute records evenly across SEED_HISTORICAL_DAYS
        days_ago = (
            (i * SEED_HISTORICAL_DAYS) // max(1, SEED_RECORD_COUNT - 1)
            if SEED_RECORD_COUNT > 1
            else 1
        )
        # Add slight jitter within the day
        order_time = now - timedelta(
            days=days_ago,
            hours=rng.randint(1, 18),
            minutes=rng.randint(0, 59),
        )

        # Assign status based on age and pattern
        is_failed_payment = i in (2, 7)  # 2 explicit failed payment demo orders
        if is_failed_payment:
            order_status = "Cancelled"
            payment_status = "Failed"
        elif days_ago > 7:
            order_status = "Delivered" if (i % 7 != 0) else "Cancelled"
            payment_status = "Success"
        elif days_ago > 2:
            order_status = "Shipped"
            payment_status = "Success"
        else:
            order_status = "Pending"
            payment_status = "Success"

        # Pick 1 to 3 distinct products for this order
        num_items = rng.randint(1, 3)
        chosen_products = rng.sample(products, num_items)

        order_lines = []
        total_amount = Decimal("0.00")
        for prod in chosen_products:
            qty = rng.randint(1, 2)
            unit_price = Decimal(prod.price)
            order_lines.append((prod, qty, unit_price))
            total_amount += unit_price * qty

        order = models.Order(
            customer_id=customer.customer_id,
            order_status=order_status,
            total_amount=total_amount,
            order_date=order_time,
        )
        db.add(order)
        db.flush()

        for prod, qty, unit_price in order_lines:
            db.add(
                models.OrderItem(
                    order_id=order.order_id,
                    product_id=prod.product_id,
                    quantity=qty,
                    unit_price=unit_price,
                )
            )

        # Payment record linked to Order
        db.add(
            models.Payment(
                order_id=order.order_id,
                amount=total_amount,
                payment_status=payment_status,
                payment_method=payment_methods[i % len(payment_methods)],
                transaction_date=order_time,
            )
        )

    db.commit()
    print("Seed complete successfully!")
    print(
        f"Seeded {len(categories)} categories, {len(products)} products, "
        f"{len(customers)} customers, {SEED_RECORD_COUNT} historical orders "
        f"across past {SEED_HISTORICAL_DAYS} days."
    )
    print("Demo logins:")
    print("  - Customer 1: aisha@example.com")
    print("  - Customer 2: rohan@example.com")
    print("  - Customer 3: priya@example.com")
    print("  - Admin Gate: admin@shopvault.com / admin123 / shopvault-secret-key")


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    reset = "--reset" in sys.argv or "-r" in sys.argv
    try:
        seed(db, reset=reset)
    finally:
        db.close()


if __name__ == "__main__":
    main()
