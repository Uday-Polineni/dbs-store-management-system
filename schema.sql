-- ============================================
-- Inventory Management System - MySQL Schema
-- With Store Manager + Cashier users
-- Safe version with IF NOT EXISTS checks
-- ============================================

CREATE DATABASE IF NOT EXISTS store_db;
USE store_db;

-- ============================================
-- 1. Users table
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('manager', 'cashier') NOT NULL
);

-- Insert seed users ONLY if table is empty
INSERT INTO users (username, password_hash, role)
SELECT * FROM (
    SELECT 
        'manager' AS username,
        SHA2('manager123', 256) AS password_hash,
        'manager' AS role
) AS tmp
WHERE NOT EXISTS (SELECT 1 FROM users WHERE username='manager');


INSERT INTO users (username, password_hash, role)
SELECT * FROM (
    SELECT 
        'cashier1' AS username,
        SHA2('cashier123', 256) AS password_hash,
        'cashier' AS role
) AS tmp
WHERE NOT EXISTS (SELECT 1 FROM users WHERE username='cashier1');


-- ============================================
-- 2. Suppliers
-- ============================================
CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id INT AUTO_INCREMENT PRIMARY KEY,
    supplier_name VARCHAR(100) NOT NULL,
    contact_info VARCHAR(150)
);

-- Insert default suppliers ONLY if table is empty
INSERT INTO suppliers (supplier_name, contact_info)
SELECT * FROM (SELECT 'ABC Distributors', 'abc@gmail.com') AS tmp
WHERE NOT EXISTS (SELECT 1 FROM suppliers WHERE supplier_name='ABC Distributors');

INSERT INTO suppliers (supplier_name, contact_info)
SELECT * FROM (SELECT 'Fresh Foods Supply Co.', 'fresh@foods.com') AS tmp
WHERE NOT EXISTS (SELECT 1 FROM suppliers WHERE supplier_name='Fresh Foods Supply Co.');


-- ============================================
-- 3. Products
-- ============================================
CREATE TABLE IF NOT EXISTS products (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    supplier_id INT,
    product_name VARCHAR(100) NOT NULL,
    sku VARCHAR(50) NOT NULL UNIQUE,
    price DECIMAL(10,2) NOT NULL,
    quantity INT NOT NULL DEFAULT 0,

    CONSTRAINT fk_products_supplier
        FOREIGN KEY (supplier_id)
        REFERENCES suppliers(supplier_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);

-- Insert sample products ONLY if table empty
INSERT INTO products (supplier_id, product_name, sku, price, quantity)
SELECT * FROM (SELECT 1, 'Rice Bag 25kg', 'RICE25KG', 18.50, 40) AS tmp
WHERE NOT EXISTS (SELECT 1 FROM products WHERE sku='RICE25KG');

INSERT INTO products (supplier_id, product_name, sku, price, quantity)
SELECT * FROM (SELECT 2, 'Milk 1L', 'MILK1L', 1.20, 100) AS tmp
WHERE NOT EXISTS (SELECT 1 FROM products WHERE sku='MILK1L');


-- ============================================
-- 4. Sales
-- ============================================
CREATE TABLE IF NOT EXISTS sales (
    sale_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    sale_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(10,2) NOT NULL DEFAULT 0,

    CONSTRAINT fk_sales_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);


-- ============================================
-- 5. Sale Items (Composite Key)
-- ============================================
CREATE TABLE IF NOT EXISTS sale_items (
    sale_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity_sold INT NOT NULL,
    item_price DECIMAL(10,2) NOT NULL,

    PRIMARY KEY (sale_id, product_id),

    CONSTRAINT fk_saleitems_sale
        FOREIGN KEY (sale_id)
        REFERENCES sales(sale_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    CONSTRAINT fk_saleitems_product
        FOREIGN KEY (product_id)
        REFERENCES products(product_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);


-- ============================================
-- 6. Reporting View (auto-updates)
-- ============================================
CREATE OR REPLACE VIEW sales_report AS
SELECT
    s.sale_id,
    s.sale_date,
    u.username AS sold_by,
    p.product_name,
    p.sku,
    si.quantity_sold,
    si.item_price,
    (si.quantity_sold * si.item_price) AS line_total
FROM sales s
JOIN users u ON s.user_id = u.user_id
JOIN sale_items si ON s.sale_id = si.sale_id
JOIN products p ON si.product_id = p.product_id;
