-- =====================================================================
-- Tailoring Web Application - SQLite schema (development / demo)
-- Production target is MS SQL Server -> see database/schema_mssql.sql
-- for the equivalent DDL (BRS Section 28).
-- =====================================================================

CREATE TABLE IF NOT EXISTS admin_users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    full_name       TEXT,
    is_active       INTEGER NOT NULL DEFAULT 1,
    failed_attempts INTEGER NOT NULL DEFAULT 0,
    locked_until    TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS customers (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    mobile          TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    name            TEXT,
    email           TEXT,
    address         TEXT,
    is_active       INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- BRS Section 11 / 29: versioned measurements, never overwritten.
CREATE TABLE IF NOT EXISTS measurements (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id     INTEGER NOT NULL REFERENCES customers(id),
    version         INTEGER NOT NULL,
    blouse_length   REAL,
    shoulder        REAL,
    bust            REAL,
    waist           REAL,
    armhole         REAL,
    sleeve_length   REAL,
    sleeve_round    REAL,
    neck_front      REAL,
    neck_back       REAL,
    neck_width      REAL,
    neck_depth      REAL,
    other_notes     TEXT,
    is_current      INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(customer_id, version)
);

CREATE TABLE IF NOT EXISTS designs (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    name                    TEXT NOT NULL,
    description             TEXT,
    category                TEXT,
    neck_style              TEXT,
    sleeve_style            TEXT,
    blouse_length           TEXT,
    customisation_details   TEXT,
    base_price              REAL NOT NULL DEFAULT 0,
    additional_charges      REAL NOT NULL DEFAULT 0,
    image_path              TEXT,
    status                  TEXT NOT NULL DEFAULT 'ACTIVE',   -- ACTIVE / INACTIVE
    created_at              TEXT NOT NULL DEFAULT (datetime('now')),
    modified_at             TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS gallery (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    image_path      TEXT NOT NULL,
    category        TEXT,
    description     TEXT,
    display_order   INTEGER NOT NULL DEFAULT 0,
    is_active       INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- BRS Section 14 / 15 / 17: order header. Order number is generated
-- server-side and is never reused (BR-005).
CREATE TABLE IF NOT EXISTS orders (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number        TEXT NOT NULL UNIQUE,
    customer_id         INTEGER NOT NULL REFERENCES customers(id),
    design_id           INTEGER NOT NULL REFERENCES designs(id),
    measurement_id      INTEGER NOT NULL REFERENCES measurements(id),  -- snapshot, BR-006
    customisation_notes TEXT,
    total_amount        REAL NOT NULL DEFAULT 0,
    amount_received     REAL NOT NULL DEFAULT 0,
    amount_pending      REAL NOT NULL DEFAULT 0,
    payment_mode        TEXT,          -- ONLINE / AT_SHOP / AFTER_DELIVERY
    payment_status      TEXT NOT NULL DEFAULT 'PENDING', -- PENDING/SUCCESS/FAILED/VERIFIED/REFUNDED
    delivery_date       TEXT,
    status              TEXT NOT NULL DEFAULT 'ORDER_RECEIVED',
    cancellation_reason TEXT,
    created_at          TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at          TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS order_status_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id        INTEGER NOT NULL REFERENCES orders(id),
    previous_status TEXT,
    new_status      TEXT NOT NULL,
    remarks         TEXT,
    updated_by      TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS payments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id        INTEGER NOT NULL REFERENCES orders(id),
    amount          REAL NOT NULL,
    mode            TEXT,                 -- ONLINE / CASH / UPI / CARD
    reference_no    TEXT,
    status          TEXT NOT NULL DEFAULT 'PENDING', -- PENDING/SUCCESS/FAILED/VERIFIED/REFUNDED
    verified_by     TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- BRS Section 3 / 20: image metadata. image_type: CustomerReference/Trial/Order
CREATE TABLE IF NOT EXISTS order_images (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id        INTEGER REFERENCES orders(id),
    customer_id     INTEGER REFERENCES customers(id),
    image_type      TEXT NOT NULL,
    file_name       TEXT NOT NULL,
    file_path       TEXT NOT NULL,
    uploaded_by     TEXT,
    uploaded_at     TEXT NOT NULL DEFAULT (datetime('now')),
    is_active       INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS email_logs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id        INTEGER REFERENCES orders(id),
    customer_id     INTEGER REFERENCES customers(id),
    email_to        TEXT,
    email_type      TEXT,          -- TRIAL_INVITE / ORDER_CONFIRMATION / etc
    sent_at         TEXT NOT NULL DEFAULT (datetime('now')),
    status          TEXT NOT NULL,  -- SUCCESS / FAILED
    error_message   TEXT,
    retry_count     INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS website_settings (
    setting_key     TEXT PRIMARY KEY,
    setting_value   TEXT
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    admin_user      TEXT,
    action          TEXT,
    module          TEXT,
    record_id       TEXT,
    old_value       TEXT,
    new_value       TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    ip_address      TEXT
);

CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_measurements_customer ON measurements(customer_id);
CREATE INDEX IF NOT EXISTS idx_order_images_order ON order_images(order_id);
