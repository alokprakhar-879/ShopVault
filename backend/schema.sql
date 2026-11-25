-- E-commerce & Inventory Management System
-- PostgreSQL DDL — 9 tables with PK/FK/CHECK constraints

CREATE TABLE IF NOT EXISTS categories (
    category_id   SERIAL PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE,
    description   TEXT
);

CREATE TABLE IF NOT EXISTS products (
    product_id  SERIAL PRIMARY KEY,
    category_id INTEGER NOT NULL REFERENCES categories(category_id),
    name        VARCHAR(200) NOT NULL,
    price       NUMERIC(12, 2) NOT NULL CHECK (price >= 0),
    description TEXT,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS inventory (
    inventory_id   SERIAL PRIMARY KEY,
    product_id     INTEGER NOT NULL UNIQUE REFERENCES products(product_id),
    stock_quantity INTEGER NOT NULL DEFAULT 0 CHECK (stock_quantity >= 0),
    reorder_level  INTEGER NOT NULL DEFAULT 5,
    last_updated   TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id   SERIAL PRIMARY KEY,
    full_name     VARCHAR(150) NOT NULL,
    email         VARCHAR(150) NOT NULL UNIQUE,
    phone         VARCHAR(30),
    address       TEXT,
    registered_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS orders (
    order_id     SERIAL PRIMARY KEY,
    customer_id  INTEGER NOT NULL REFERENCES customers(customer_id),
    order_status VARCHAR(20) NOT NULL DEFAULT 'Pending'
                 CHECK (order_status IN ('Pending', 'Shipped', 'Delivered', 'Cancelled')),
    total_amount NUMERIC(12, 2) NOT NULL DEFAULT 0 CHECK (total_amount >= 0),
    order_date   TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id      INTEGER NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    product_id    INTEGER NOT NULL REFERENCES products(product_id),
    quantity      INTEGER NOT NULL CHECK (quantity > 0),
    unit_price    NUMERIC(12, 2) NOT NULL  -- historical price snapshot
);

CREATE TABLE IF NOT EXISTS payments (
    payment_id       SERIAL PRIMARY KEY,
    order_id         INTEGER NOT NULL UNIQUE REFERENCES orders(order_id),
    amount           NUMERIC(12, 2) NOT NULL CHECK (amount >= 0),
    payment_status   VARCHAR(20) NOT NULL DEFAULT 'Pending'
                     CHECK (payment_status IN ('Pending', 'Success', 'Failed')),
    payment_method   VARCHAR(30) NOT NULL
                     CHECK (payment_method IN ('Credit Card', 'UPI', 'PayPal')),
    transaction_date TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS wishlists (
    wishlist_id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    product_id  INTEGER NOT NULL REFERENCES products(product_id),
    added_at    TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (customer_id, product_id)
);

CREATE TABLE IF NOT EXISTS reviews (
    review_id   SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    product_id  INTEGER NOT NULL REFERENCES products(product_id),
    rating      INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment     TEXT,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Useful indexes for reporting / lookups
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_reviews_product ON reviews(product_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(payment_status);

-- Example: average rating via SQL aggregate
-- SELECT product_id, AVG(rating) AS avg_rating, COUNT(*) AS review_count
-- FROM reviews GROUP BY product_id;
