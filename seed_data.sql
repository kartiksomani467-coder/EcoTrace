
USE ecotrace_db;

-- 1. Categories
INSERT INTO categories
    (category_name, description, default_shelf_life_days)
VALUES
    ('Dairy', 'Milk and dairy products', 7),
    ('Bakery', 'Bread and bakery products', 5),
    ('Beverages', 'Packaged drinks', 180),
    ('Personal Care', 'Daily personal care products', NULL);

-- 2. Items
INSERT INTO items
    (sku, item_name, category_id, unit, is_perishable, reorder_level)
VALUES
    ('DAI001', 'Fresh Milk', 
     (SELECT category_id FROM categories WHERE category_name = 'Dairy'),
     'litre', TRUE, 10),
    ('BAK001', 'Whole Wheat Bread',
     (SELECT category_id FROM categories WHERE category_name = 'Bakery'),
     'pack', TRUE, 5),
    ('BEV001', 'Orange Juice',
     (SELECT category_id FROM categories WHERE category_name = 'Beverages'),
     'bottle', TRUE, 8),
    ('CARE001', 'Hand Wash',
     (SELECT category_id FROM categories WHERE category_name = 'Personal Care'),
     'bottle', FALSE, 4);

-- 3. Suppliers
INSERT INTO suppliers
    (supplier_name, contact_person, phone, email, address)
VALUES
    ('Fresh Farms Supply', 'Amit Sharma', '9000000001',
     'fresh@example.com', 'Pune, Maharashtra'),
    ('Daily Needs Distributors', 'Neha Patel', '9000000002',
     'daily@example.com', 'Pune, Maharashtra');

-- 4. Inventory batches
INSERT INTO inventory_batches
    (item_id, batch_code, quantity_received, quantity_available,
     received_date, shelf_life_days, expiry_date)
VALUES
    (
        (SELECT item_id FROM items WHERE sku = 'DAI001'),
        'MILK-001', 50, 20, CURRENT_DATE - INTERVAL 4 DAY,
        7, CURRENT_DATE + INTERVAL 3 DAY
    ),
    (
        (SELECT item_id FROM items WHERE sku = 'BAK001'),
        'BREAD-001', 30, 4, CURRENT_DATE - INTERVAL 4 DAY,
        5, CURRENT_DATE + INTERVAL 1 DAY
    ),
    (
        (SELECT item_id FROM items WHERE sku = 'BEV001'),
        'JUICE-001', 40, 15, CURRENT_DATE - INTERVAL 10 DAY,
        180, CURRENT_DATE + INTERVAL 170 DAY
    ),
    (
        (SELECT item_id FROM items WHERE sku = 'CARE001'),
        'WASH-001', 20, 12, CURRENT_DATE - INTERVAL 20 DAY,
        NULL, NULL
    );

-- 5. Initial stock receipts
INSERT INTO stock_movements
    (batch_id, movement_type, quantity, reason)
SELECT batch_id, 'RECEIPT', quantity_received, 'Initial sample stock'
FROM inventory_batches
WHERE batch_code IN ('MILK-001', 'BREAD-001', 'JUICE-001', 'WASH-001');

-- 6. Sample consumption history
INSERT INTO usage_logs
    (batch_id, quantity_consumed, consumed_at, notes)
SELECT batch_id, 2, NOW() - INTERVAL 1 DAY, 'Sample daily consumption'
FROM inventory_batches
WHERE batch_code = 'MILK-001';

INSERT INTO usage_logs
    (batch_id, quantity_consumed, consumed_at, notes)
SELECT batch_id, 3, NOW() - INTERVAL 2 DAY, 'Sample bread consumption'
FROM inventory_batches
WHERE batch_code = 'BREAD-001';

-- 7. Sample purchase
INSERT INTO purchases
    (supplier_id, reference_number, purchase_date, status, notes)
VALUES
    (
        (SELECT supplier_id FROM suppliers
         WHERE supplier_name = 'Fresh Farms Supply'),
        'PO-1001', CURRENT_DATE, 'RECEIVED',
        'Initial sample purchase'
    );

INSERT INTO purchase_items
    (purchase_id, item_id, quantity_ordered, quantity_received, unit_cost)
VALUES
    (
        (SELECT purchase_id FROM purchases WHERE reference_number = 'PO-1001'),
        (SELECT item_id FROM items WHERE sku = 'DAI001'),
        50, 50, 55.00
    );

-- 8. Verify sample data
SELECT 'categories' AS table_name, COUNT(*) AS total FROM categories
UNION ALL
SELECT 'items', COUNT(*) FROM items
UNION ALL
SELECT 'suppliers', COUNT(*) FROM suppliers
UNION ALL
SELECT 'inventory_batches', COUNT(*) FROM inventory_batches
UNION ALL
SELECT 'stock_movements', COUNT(*) FROM stock_movements
UNION ALL
SELECT 'usage_logs', COUNT(*) FROM usage_logs
UNION ALL
SELECT 'purchases', COUNT(*) FROM purchases
UNION ALL
SELECT 'purchase_items', COUNT(*) FROM purchase_items;
