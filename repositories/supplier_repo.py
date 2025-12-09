from db import get_db_connection

def get_suppliers():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM suppliers ORDER BY supplier_id DESC")
    rows = cursor.fetchall()

    cursor.close()
    conn.close()
    return rows


def get_supplier(supplier_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM suppliers WHERE supplier_id=%s", (supplier_id,))
    row = cursor.fetchone()

    cursor.close()
    conn.close()
    return row


def add_supplier(name, contact):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO suppliers (supplier_name, contact_info)
        VALUES (%s, %s)
    """, (name, contact))

    conn.commit()
    cursor.close()
    conn.close()


def update_supplier(supplier_id, name, contact):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE suppliers
        SET supplier_name=%s, contact_info=%s
        WHERE supplier_id=%s
    """, (name, contact, supplier_id))

    conn.commit()
    cursor.close()
    conn.close()


def delete_supplier(supplier_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM suppliers WHERE supplier_id=%s", (supplier_id,))
    conn.commit()

    cursor.close()
    conn.close()
