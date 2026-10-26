
-- =====================================================
-- EcoTrace: Micro-Logistics & Shelf-Life Tracker
-- Compatible with MySQL 8.0+
-- =====================================================

CREATE DATABASE IF NOT EXISTS ecotrace_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_0900_ai_ci;

USE ecotrace_db;

-- 1. Categories
CREATE TABLE IF NOT EXISTS categories (
    category_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(500),
    default_shelf_life_days INT UNSIGNED NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 2. Items
CREATE TABLE IF NOT EXISTS items (
    item_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    sku VARCHAR(50) NOT NULL UNIQUE,
    item_name VARCHAR(150) NOT NULL,
    category_id INT UNSIGNED NOT NULL,
    unit VARCHAR(30) NOT NULL,
    is_perishable BOOLEAN NOT NULL DEFAULT TRUE,
    reorder_level DECIMAL(12,3) NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_items_reorder_level
        CHECK (reorder_level >= 0),

    CONSTRAINT fk_items_category
        FOREIGN KEY (category_id)
        REFERENCES categories(category_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    INDEX idx_items_name (item_name),
    INDEX idx_items_category (category_id)
) ENGINE=InnoDB;

-- 3. Inventory batches
CREATE TABLE IF NOT EXISTS inventory_batches (
    batch_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    item_id INT UNSIGNED NOT NULL,
    batch_code VARCHAR(80) NOT NULL,
    quantity_received DECIMAL(12,3) NOT NULL,
    quantity_available DECIMAL(12,3) NOT NULL,
    received_date DATE NOT NULL,
    opened_date DATE NULL,
    shelf_life_days INT UNSIGNED NULL,
    expiry_date DATE NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_batch_item_code
        UNIQUE (item_id, batch_code),

    CONSTRAINT chk_batch_received
        CHECK (quantity_received > 0),

    CONSTRAINT chk_batch_available
        CHECK (
            quantity_available >= 0
            AND quantity_available <= quantity_received
        ),

    CONSTRAINT fk_batches_item
        FOREIGN KEY (item_id)
        REFERENCES items(item_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    INDEX idx_batches_expiry (expiry_date),
    INDEX idx_batches_item (item_id)
) ENGINE=InnoDB;

-- 4. Consumption history
CREATE TABLE IF NOT EXISTS usage_logs (
    usage_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    batch_id INT UNSIGNED NOT NULL,
    quantity_consumed DECIMAL(12,3) NOT NULL,
    consumed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notes VARCHAR(500),

    CONSTRAINT chk_usage_quantity
        CHECK (quantity_consumed > 0),

    CONSTRAINT fk_usage_batch
        FOREIGN KEY (batch_id)
        REFERENCES inventory_batches(batch_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    INDEX idx_usage_consumed_at (consumed_at),
    INDEX idx_usage_batch_date (batch_id, consumed_at)
) ENGINE=InnoDB;

-- 5. Stock movement history
CREATE TABLE IF NOT EXISTS stock_movements (
    movement_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    batch_id INT UNSIGNED NOT NULL,
    movement_type ENUM(
        'RECEIPT',
        'CONSUMPTION',
        'ADJUSTMENT_IN',
        'ADJUSTMENT_OUT',
        'WASTAGE',
        'EXPIRY'
    ) NOT NULL,
    quantity DECIMAL(12,3) NOT NULL,
    reason VARCHAR(500),
    movement_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_movement_quantity
        CHECK (quantity > 0),

    CONSTRAINT fk_movements_batch
        FOREIGN KEY (batch_id)
        REFERENCES inventory_batches(batch_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    INDEX idx_movements_date (movement_at),
    INDEX idx_movements_batch (batch_id)
) ENGINE=InnoDB;

-- 6. Suppliers
CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    supplier_name VARCHAR(150) NOT NULL,
    contact_person VARCHAR(100),
    phone VARCHAR(30),
    email VARCHAR(254),
    address VARCHAR(500),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_suppliers_name (supplier_name)
) ENGINE=InnoDB;

-- 7. Purchases
CREATE TABLE IF NOT EXISTS purchases (
    purchase_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    supplier_id INT UNSIGNED NOT NULL,
    reference_number VARCHAR(80) NOT NULL UNIQUE,
    purchase_date DATE NOT NULL,
    status ENUM(
        'DRAFT',
        'ORDERED',
        'PARTIALLY_RECEIVED',
        'RECEIVED',
        'CANCELLED'
    ) NOT NULL DEFAULT 'DRAFT',
    notes VARCHAR(500),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_purchases_supplier
        FOREIGN KEY (supplier_id)
        REFERENCES suppliers(supplier_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    INDEX idx_purchases_date (purchase_date),
    INDEX idx_purchases_status (status)
) ENGINE=InnoDB;

-- 8. Purchase line items
CREATE TABLE IF NOT EXISTS purchase_items (
    purchase_item_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    purchase_id BIGINT UNSIGNED NOT NULL,
    item_id INT UNSIGNED NOT NULL,
    quantity_ordered DECIMAL(12,3) NOT NULL,
    quantity_received DECIMAL(12,3) NOT NULL DEFAULT 0,
    unit_cost DECIMAL(12,2) NOT NULL DEFAULT 0,

    CONSTRAINT uq_purchase_item
        UNIQUE (purchase_id, item_id),

    CONSTRAINT chk_purchase_ordered
        CHECK (quantity_ordered > 0),

    CONSTRAINT chk_purchase_received
        CHECK (
            quantity_received >= 0
            AND quantity_received <= quantity_ordered
        ),

    CONSTRAINT chk_purchase_cost
        CHECK (unit_cost >= 0),

    CONSTRAINT fk_purchase_items_purchase
        FOREIGN KEY (purchase_id)
        REFERENCES purchases(purchase_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_purchase_items_item
        FOREIGN KEY (item_id)
        REFERENCES items(item_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    INDEX idx_purchase_items_item (item_id)
) ENGINE=InnoDB;

-- 9. Application settings
CREATE TABLE IF NOT EXISTS app_settings (
    setting_key VARCHAR(100) PRIMARY KEY,
    setting_value VARCHAR(255) NOT NULL,
    description VARCHAR(500),
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Default settings
INSERT INTO app_settings
    (setting_key, setting_value, description)
VALUES
    (
        'expiry_warning_days',
        '3',
        'Number of days before expiry to trigger a warning'
    ),
    (
        'depletion_history_days',
        '7',
        'Historical window used for stock depletion estimates'
    ) AS new
ON DUPLICATE KEY UPDATE
    setting_value = new.setting_value,
    description = new.description;
