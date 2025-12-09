from db import get_db_connection

def get_sales_list():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT sale_id, sale_date, sold_by AS username,
               SUM(line_total) AS total_amount
        FROM sales_report
        GROUP BY sale_id
        ORDER BY sale_id DESC
    """)
    rows = cursor.fetchall()

    cursor.close()
    conn.close()
    return rows


def get_sale_details(sale_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT DISTINCT sale_id, sale_date, sold_by AS username,
               SUM(line_total) AS total_amount
        FROM sales_report
        WHERE sale_id=%s
        GROUP BY sale_id
    """, (sale_id,))
    sale = cursor.fetchone()

    cursor.execute("""
        SELECT product_name, sku, quantity_sold, item_price, line_total
        FROM sales_report
        WHERE sale_id=%s
    """, (sale_id,))
    items = cursor.fetchall()

    cursor.close()
    conn.close()
    return sale, items
