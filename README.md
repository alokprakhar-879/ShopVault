# ShopVault — E-commerce & Inventory Management System

Production-ready DBMS MVP with **React + Chart.js**, **FastAPI**, **PostgreSQL**, and **SQLAlchemy**.

## Features

- **9 normalized tables** with PK/FK/CHECK constraints (`backend/schema.sql`)
- Dynamic stock badges (In Stock / Hurry / Out of Stock)
- Wishlist, order history with live status emojis, reviews with SQL `AVG()`
- Pre-checkout stock validation + cart refresh message
- Cancel lock for Shipped/Delivered; Pending cancel restocks inventory
- Checkout race protection via `SELECT … FOR UPDATE`
- Payment-failure ACID rollback (no stock mutation if payment fails)
- Admin sales dashboard (Chart.js) + low-stock monitoring panel

## Folder structure

```
DBMS Project/
├── docker-compose.yml          # PostgreSQL 16
├── README.md
├── backend/
│   ├── .env / .env.example
│   ├── requirements.txt
│   ├── schema.sql
│   └── app/
│       ├── main.py             # FastAPI entry
│       ├── database.py
│       ├── models.py           # SQLAlchemy ORM (9 tables)
│       ├── schemas.py          # Pydantic DTOs
│       ├── services.py         # Checkout locking, cancel/restock
│       ├── seed.py
│       └── routers/            # REST endpoints
└── frontend/
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── App.jsx
        ├── api.js
        ├── context/
        ├── components/
        └── styles/
```

## Quick start

### 1. Database

**PostgreSQL (recommended for the DBMS project):**

```bash
docker compose up -d
```

Then set in `backend/.env`:

```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ecommerce_db
```

Or create a local PostgreSQL database named `ecommerce_db` and point `DATABASE_URL` at it.

**SQLite fallback (no Docker needed):** the repo `.env` can use `sqlite:///./ecommerce.db` so you can demo the full stack immediately. Switch to PostgreSQL for the formal schema / locking demonstration.

### 2. Backend

```bash
cd backend
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
python -m app.seed
uvicorn app.main:app --reload --port 8000
```

API docs: http://127.0.0.1:8000/docs

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

App: http://127.0.0.1:5173

### Demo logins

| Email | Role |
|-------|------|
| `aisha@example.com` | Customer (wishlist + reviews seeded) |
| `rohan@example.com` | Customer |
| `admin@example.com` | Demo admin user |

## Key API endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/products` | Catalog + stock badges + AVG rating |
| POST | `/api/orders/validate-cart` | Edge case 1 — stock mismatch check |
| POST | `/api/orders/checkout` | Locked checkout + payment |
| POST | `/api/orders/{id}/cancel` | Edge case 2 — cancel/restock rules |
| GET/POST | `/api/wishlists` | Save for later |
| GET | `/api/reviews/product/{id}` | Comments + `AVG(rating)` |
| GET | `/api/admin/dashboard` | Revenue trend + low stock |
| GET | `/api/inventory/low-stock` | Monitoring panel data |

## Edge-case demos

1. **Cart vs stock**: Add a low-stock item, reduce stock in Admin (“Add stock” can also be used in reverse via API), then checkout — UI shows *“Sorry! Someone else just bought these items…”* and refreshes quantities.
2. **Cancel lock**: Place an order, use Admin → **Ship all pending**, then try Cancel on My Orders — button disabled + return message.
3. **Payment rollback**: Cart → enable **Simulate payment failure** → checkout — inventory unchanged.
4. **Race safety**: Checkout path locks inventory rows with `with_for_update()` inside a single transaction.

## Tech notes

- Historical prices are stored on `order_items.unit_price` so later product price edits do not rewrite receipts.
- One inventory row per product (`product_id UNIQUE`).
- CORS is open for local MVP development.
