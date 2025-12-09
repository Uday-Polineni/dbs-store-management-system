from db import get_db_connection

def get_all_products():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT p.*, s.supplier_name
        FROM products p
        LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id
        ORDER BY p.product_id DESC
    """)
    rows = cursor.fetchall()

    cursor.close()
    conn.close()
    return rows


def get_product(product_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM products WHERE product_id=%s", (product_id,))
    row = cursor.fetchone()

    cursor.close()
    conn.close()
    return row


def add_product(name, sku, price, qty, supplier_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO products (product_name, sku, price, quantity, supplier_id)
        VALUES (%s, %s, %s, %s, %s)
    """, (name, sku, price, qty, supplier_id))

    conn.commit()
    cursor.close()
    conn.close()


def update_product(product_id, name, sku, price, qty, supplier_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE products
        SET product_name=%s, sku=%s, price=%s, quantity=%s, supplier_id=%s
        WHERE product_id=%s
    """, (name, sku, price, qty, supplier_id, product_id))

    conn.commit()
    cursor.close()
    conn.close()


def delete_product(product_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM products WHERE product_id=%s", (product_id,))
    conn.commit()

    cursor.close()
    conn.close()
