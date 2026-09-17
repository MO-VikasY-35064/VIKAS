-- =====================================================================
-- Tailoring Web Application - MS SQL Server schema (PRODUCTION)
-- Per BRS Section 2: "All business/transactional data must be stored
-- in MS SQL Server." This is the authoritative production schema.
-- The SQLite file (schema_sqlite.sql) is the dev/demo equivalent.
--
-- Run against your target database, e.g.:
--   sqlcmd -S <server> -d TailoringDB -i schema_mssql.sql
-- =====================================================================

IF DB_ID('TailoringDB') IS NULL
BEGIN
    --PRINT 'Create the TailoringDB database first, then run this script against it.';
    Create database TailoringDB
END
GO

CREATE TABLE admin_users (
    id              INT IDENTITY(1,1) PRIMARY KEY,
    username        NVARCHAR(100) NOT NULL UNIQUE,
    password_hash   NVARCHAR(255) NOT NULL,
    full_name       NVARCHAR(200),
    is_active       BIT NOT NULL DEFAULT 1,
    failed_attempts INT NOT NULL DEFAULT 0,
    locked_until    DATETIME2 NULL,
    created_at      DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);

CREATE TABLE customers (
    id              INT IDENTITY(1,1) PRIMARY KEY,
    mobile          NVARCHAR(20) NOT NULL UNIQUE,
    password_hash   NVARCHAR(255) NOT NULL,
    name            NVARCHAR(200),
    email           NVARCHAR(255),
    address         NVARCHAR(500),
    is_active       BIT NOT NULL DEFAULT 1,
    created_at      DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);

CREATE TABLE measurements (
    id              INT IDENTITY(1,1) PRIMARY KEY,
    customer_id     INT NOT NULL FOREIGN KEY REFERENCES customers(id),
    version         INT NOT NULL,
    blouse_length   DECIMAL(6,2),
    shoulder        DECIMAL(6,2),
    bust            DECIMAL(6,2),
    waist           DECIMAL(6,2),
    armhole         DECIMAL(6,2),
    sleeve_length   DECIMAL(6,2),
    sleeve_round    DECIMAL(6,2),
    neck_front      DECIMAL(6,2),
    neck_back       DECIMAL(6,2),
    neck_width      DECIMAL(6,2),
    neck_depth      DECIMAL(6,2),
    other_notes     NVARCHAR(1000),
    is_current      BIT NOT NULL DEFAULT 1,
    created_at      DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT UQ_customer_version UNIQUE (customer_id, version)
);

CREATE TABLE designs (
    id                      INT IDENTITY(1,1) PRIMARY KEY,
    name                    NVARCHAR(200) NOT NULL,
    description             NVARCHAR(1000),
    category                NVARCHAR(100),
    neck_style              NVARCHAR(100),
    sleeve_style            NVARCHAR(100),
    blouse_length           NVARCHAR(100),
    customisation_details   NVARCHAR(1000),
    base_price              DECIMAL(10,2) NOT NULL DEFAULT 0,
    additional_charges      DECIMAL(10,2) NOT NULL DEFAULT 0,
    image_path              NVARCHAR(500),
    status                  NVARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    created_at              DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    modified_at             DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);

CREATE TABLE gallery (
    id              INT IDENTITY(1,1) PRIMARY KEY,
    image_path      NVARCHAR(500) NOT NULL,
    category        NVARCHAR(100),
    description     NVARCHAR(500),
    display_order   INT NOT NULL DEFAULT 0,
    is_active       BIT NOT NULL DEFAULT 1,
    created_at      DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);

CREATE TABLE orders (
    id                  INT IDENTITY(1,1) PRIMARY KEY,
    order_number        NVARCHAR(30) NOT NULL UNIQUE,
    customer_id         INT NOT NULL FOREIGN KEY REFERENCES customers(id),
    design_id           INT NOT NULL FOREIGN KEY REFERENCES designs(id),
    measurement_id      INT NOT NULL FOREIGN KEY REFERENCES measurements(id),
    customisation_notes NVARCHAR(1000),
    total_amount        DECIMAL(10,2) NOT NULL DEFAULT 0,
    amount_received     DECIMAL(10,2) NOT NULL DEFAULT 0,
    amount_pending      DECIMAL(10,2) NOT NULL DEFAULT 0,
    payment_mode        NVARCHAR(30),
    payment_status      NVARCHAR(20) NOT NULL DEFAULT 'PENDING',
    delivery_date       DATE,
    status              NVARCHAR(30) NOT NULL DEFAULT 'ORDER_RECEIVED',
    cancellation_reason NVARCHAR(500),
    created_at          DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    updated_at          DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);

CREATE TABLE order_status_history (
    id              INT IDENTITY(1,1) PRIMARY KEY,
    order_id        INT NOT NULL FOREIGN KEY REFERENCES orders(id),
    previous_status NVARCHAR(30),
    new_status      NVARCHAR(30) NOT NULL,
    remarks         NVARCHAR(500),
    updated_by      NVARCHAR(100),
    created_at      DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);

CREATE TABLE payments (
    id              INT IDENTITY(1,1) PRIMARY KEY,
    order_id        INT NOT NULL FOREIGN KEY REFERENCES orders(id),
    amount          DECIMAL(10,2) NOT NULL,
    mode            NVARCHAR(30),
    reference_no    NVARCHAR(100),
    status          NVARCHAR(20) NOT NULL DEFAULT 'PENDING',
    verified_by     NVARCHAR(100),
    created_at      DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);

CREATE TABLE order_images (
    id              INT IDENTITY(1,1) PRIMARY KEY,
    order_id        INT NULL FOREIGN KEY REFERENCES orders(id),
    customer_id     INT NULL FOREIGN KEY REFERENCES customers(id),
    image_type      NVARCHAR(30) NOT NULL,
    file_name       NVARCHAR(255) NOT NULL,
    file_path       NVARCHAR(500) NOT NULL,
    uploaded_by     NVARCHAR(100),
    uploaded_at     DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    is_active       BIT NOT NULL DEFAULT 1
);

CREATE TABLE email_logs (
    id              INT IDENTITY(1,1) PRIMARY KEY,
    order_id        INT NULL FOREIGN KEY REFERENCES orders(id),
    customer_id     INT NULL FOREIGN KEY REFERENCES customers(id),
    email_to        NVARCHAR(255),
    email_type      NVARCHAR(50),
    sent_at         DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    status          NVARCHAR(20) NOT NULL,
    error_message   NVARCHAR(1000),
    retry_count     INT NOT NULL DEFAULT 0
);

CREATE TABLE website_settings (
    setting_key     NVARCHAR(100) PRIMARY KEY,
    setting_value   NVARCHAR(MAX)
);

CREATE TABLE audit_logs (
    id              INT IDENTITY(1,1) PRIMARY KEY,
    admin_user      NVARCHAR(100),
    action          NVARCHAR(100),
    module          NVARCHAR(100),
    record_id       NVARCHAR(100),
    old_value       NVARCHAR(MAX),
    new_value       NVARCHAR(MAX),
    created_at      DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    ip_address      NVARCHAR(50)
);

CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_measurements_customer ON measurements(customer_id);
CREATE INDEX idx_order_images_order ON order_images(order_id);
GO
