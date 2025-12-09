from flask import Flask, render_template, request, redirect, session
from db import get_db_connection,initialize_database
from config import SECRET_KEY

from services.product_service import (
    list_products,
    product_details,
    create_product,
    edit_product,
    remove_product,
)
from services.supplier_service import (
    list_suppliers,
    supplier_details,
    create_supplier,
    edit_supplier,
    remove_supplier,
)
from services.sales_service import (
    list_sales,
    sale_info,
)

app = Flask(__name__)
app.secret_key = SECRET_KEY


# -----------------------------------
# Login Page
# -----------------------------------
@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Validate login (password stored as SHA2)
        cursor.execute("""
            SELECT * FROM users
            WHERE username = %s AND password_hash = SHA2(%s, 256)
        """, (username, password))

        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user:
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect('/dashboard')
        else:
            return render_template('login.html', error="Invalid username or password")

    return render_template('login.html')


# ----------------------------------------------------
# Helper: Check if user is manager
# ----------------------------------------------------
def manager_only():
    return 'role' in session and session['role'] == 'manager'


# ----------------------------------------------------
# DASHBOARD
# ----------------------------------------------------
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    role = session['role']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 1. LOW STOCK (manager only)
    low_stock = []
    if role == 'manager':
        cursor.execute("""
            SELECT product_name, sku, quantity
            FROM products
            WHERE quantity < 10
            ORDER BY quantity ASC
        """)
        low_stock = cursor.fetchall()

    # 2. TODAY'S SALES SUMMARY
    cursor.execute("""
        SELECT 
            COUNT(*) AS total_sales,
            SUM(total_amount) AS total_amount
        FROM sales
        WHERE DATE(sale_date) = CURDATE()
    """)
    today_sales = cursor.fetchone()

    # 3. MONTHLY SALES SUMMARY
    cursor.execute("""
        SELECT 
            COUNT(*) AS monthly_sales,
            SUM(total_amount) AS monthly_amount
        FROM sales
        WHERE MONTH(sale_date) = MONTH(CURDATE())
          AND YEAR(sale_date) = YEAR(CURDATE())
    """)
    month_sales = cursor.fetchone()

    # 4. TOP SELLING PRODUCTS (manager only)
    top_products = []
    if role == 'manager':
        cursor.execute("""
            SELECT 
                p.product_name,
                SUM(si.quantity_sold) AS total_sold
            FROM sale_items si
            JOIN products p ON si.product_id = p.product_id
            GROUP BY si.product_id
            ORDER BY total_sold DESC
            LIMIT 5
        """)
        top_products = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'dashboard.html',
        role=role,
        low_stock=low_stock,
        today_sales=today_sales,
        month_sales=month_sales,
        top_products=top_products
    )


# ----------------------------------------------------
# PRODUCTS (use Product Service)
# ----------------------------------------------------
@app.route('/products')
def products():
    if not manager_only():
        return redirect('/dashboard')

    products = list_products()
    return render_template('products.html', products=products)


@app.route('/products/add', methods=['GET', 'POST'])
def add_product():
    if not manager_only():
        return redirect('/dashboard')

    suppliers = list_suppliers()

    if request.method == 'POST':
        name = request.form['product_name'].strip()
        sku = request.form['sku'].strip()
        price = request.form['price']
        qty = request.form['quantity']
        supplier_id = request.form['supplier_id']

        # SERVER SIDE VALIDATION
        if not name or not sku or not price or not qty:
            return render_template('add_product.html', suppliers=suppliers,
                                error="All fields are required.")

        try:
            price = float(price)
            qty = int(qty)
        except ValueError:
            return render_template('add_product.html', suppliers=suppliers,
                                error="Invalid price or quantity.")

        if price <= 0 or qty < 0:
            return render_template('add_product.html', suppliers=suppliers,
                                error="Price must be > 0 and Quantity ≥ 0.")

        try:
            create_product(name, sku, price, qty, supplier_id)
        except Exception as e:
            return render_template('add_product.html', suppliers=suppliers,
                                error="Database error: " + str(e))

        return redirect('/products')


    return render_template('add_product.html', suppliers=suppliers)


@app.route('/products/edit/<int:product_id>', methods=['GET', 'POST'])
def edit_product_route(product_id):
    if not manager_only():
        return redirect('/dashboard')

    product = product_details(product_id)
    suppliers = list_suppliers()

    if request.method == 'POST':
        name = request.form['product_name']
        sku = request.form['sku']
        price = request.form['price']
        qty = request.form['quantity']
        supplier_id = request.form['supplier_id']

        edit_product(product_id, name, sku, price, qty, supplier_id)
        return redirect('/products')

    return render_template('edit_product.html', product=product, suppliers=suppliers)


@app.route('/products/delete/<int:product_id>')
def delete_product(product_id):
    if not manager_only():
        return redirect('/dashboard')

    remove_product(product_id)
    return redirect('/products')


# ----------------------------------------------------
# SUPPLIERS (use Supplier Service)
# ----------------------------------------------------
@app.route('/suppliers')
def suppliers():
    if not manager_only():
        return redirect('/dashboard')

    suppliers_list = list_suppliers()
    return render_template('suppliers.html', suppliers=suppliers_list)


@app.route('/suppliers/add', methods=['GET', 'POST'])
def add_supplier():
    if not manager_only():
        return redirect('/dashboard')

    if request.method == 'POST':
        name = request.form['supplier_name']
        contact = request.form['contact_info']
        if not name or not contact:
            return render_template('add_supplier.html', error="Both fields required.")

        try:
            create_supplier(name, contact)
        except Exception as e:
            return render_template('add_supplier.html', error="Database error: " + str(e))
        return redirect('/suppliers')

    return render_template('add_supplier.html')


@app.route('/suppliers/edit/<int:supplier_id>', methods=['GET', 'POST'])
def edit_supplier_route(supplier_id):
    if not manager_only():
        return redirect('/dashboard')

    supplier = supplier_details(supplier_id)

    if request.method == 'POST':
        name = request.form['supplier_name']
        contact = request.form['contact_info']
        if not name or not contact:
            return render_template('edit_supplier.html', supplier=supplier, error="Fields required.")
        edit_supplier(supplier_id, name, contact)
        return redirect('/suppliers')

    return render_template('edit_supplier.html', supplier=supplier)


@app.route('/suppliers/delete/<int:supplier_id>')
def delete_supplier_route(supplier_id):
    if not manager_only():
        return redirect('/dashboard')

    remove_supplier(supplier_id)
    return redirect('/suppliers')


# ----------------------------------------------------
# SALES LIST (uses Sales Service)
# ----------------------------------------------------
@app.route('/sales')
def sales():
    if 'user_id' not in session:
        return redirect('/login')

    sales_rows = list_sales()
    return render_template('sales.html', sales=sales_rows)


# ----------------------------------------------------
# NEW SALE (creates base sale row)
# ----------------------------------------------------
@app.route('/sales/new')
def new_sale():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO sales (user_id, total_amount)
        VALUES (%s, 0)
    """, (user_id,))

    conn.commit()
    sale_id = cursor.lastrowid

    cursor.close()
    conn.close()

    return redirect(f'/sales/add-item/{sale_id}')


# ----------------------------------------------------
# ADD ITEM TO A SALE (with list + add)
# ----------------------------------------------------
@app.route('/sales/add-item/<int:sale_id>', methods=['GET', 'POST'])
def add_sale_item(sale_id):
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Load product list
    cursor.execute("SELECT * FROM products ORDER BY product_name")
    products = cursor.fetchall()

    # Load existing items in this sale
    cursor.execute("""
        SELECT 
            si.product_id,
            si.quantity_sold,
            si.item_price,
            p.product_name,
            p.sku
        FROM sale_items si
        JOIN products p ON si.product_id = p.product_id
        WHERE si.sale_id = %s
    """, (sale_id,))
    added_items = cursor.fetchall()

    # Add new item
    if request.method == 'POST':
        product_id = int(request.form['product_id'])
        qty = int(request.form['quantity'])

        # Get product details
        cursor.execute("SELECT * FROM products WHERE product_id = %s", (product_id,))
        product = cursor.fetchone()

        if qty <= 0:
            return render_template(
                'add_sale_item.html',
                sale_id=sale_id,
                products=products,
                added_items=added_items,
                error="Quantity must be at least 1."
            )

        if product['quantity'] < qty:
            cursor.close()
            conn.close()
            return render_template(
                'add_sale_item.html',
                sale_id=sale_id,
                products=products,
                added_items=added_items,
                error=f"Not enough stock. Available: {product['quantity']}"
            )

        item_price = product['price']

        # Check if already exists in this sale
        cursor.execute("""
            SELECT quantity_sold FROM sale_items
            WHERE sale_id=%s AND product_id=%s
        """, (sale_id, product_id))
        existing = cursor.fetchone()

        cursor2 = conn.cursor()

        if existing:
            cursor2.execute("""
                UPDATE sale_items
                SET quantity_sold = quantity_sold + %s
                WHERE sale_id=%s AND product_id=%s
            """, (qty, sale_id, product_id))
        else:
            cursor2.execute("""
                INSERT INTO sale_items (sale_id, product_id, quantity_sold, item_price)
                VALUES (%s, %s, %s, %s)
            """, (sale_id, product_id, qty, item_price))

        # Update stock
        cursor2.execute("""
            UPDATE products
            SET quantity = quantity - %s
            WHERE product_id = %s
        """, (qty, product_id))

        # Update sale total
        cursor2.execute("""
            UPDATE sales
            SET total_amount = total_amount + (%s * %s)
            WHERE sale_id = %s
        """, (item_price, qty, sale_id))

        conn.commit()
        cursor2.close()

        return redirect(f"/sales/add-item/{sale_id}")

    cursor.close()
    conn.close()
    return render_template(
        'add_sale_item.html',
        sale_id=sale_id,
        products=products,
        added_items=added_items
    )


# ----------------------------------------------------
# VIEW SALE DETAILS (uses Sales Service with sales_report view)
# ----------------------------------------------------
@app.route('/sales/view/<int:sale_id>')
def view_sale(sale_id):
    if 'user_id' not in session:
        return redirect('/login')

    sale, items = sale_info(sale_id)
    return render_template('view_sale.html', sale=sale, items=items)


# ----------------------------------------------------
# INCREASE / DECREASE / REMOVE SALE ITEM
# ----------------------------------------------------
@app.route('/sales/item/increase/<int:sale_id>/<int:product_id>')
def increase_item(sale_id, product_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT quantity, price FROM products WHERE product_id=%s", (product_id,))
    product = cursor.fetchone()

    if not product or product['quantity'] <= 0:
        cursor.close()
        conn.close()
        return redirect(f"/sales/add-item/{sale_id}")

    price = product['price']
    cursor2 = conn.cursor()

    # Increase quantity_sold
    cursor2.execute("""
        UPDATE sale_items
        SET quantity_sold = quantity_sold + 1
        WHERE sale_id=%s AND product_id=%s
    """, (sale_id, product_id))

    # Decrease stock
    cursor2.execute("""
        UPDATE products
        SET quantity = quantity - 1
        WHERE product_id=%s
    """, (product_id,))

    # Increase sale total
    cursor2.execute("""
        UPDATE sales
        SET total_amount = total_amount + %s
        WHERE sale_id=%s
    """, (price, sale_id))

    conn.commit()
    cursor2.close()
    cursor.close()
    conn.close()

    return redirect(f"/sales/add-item/{sale_id}")


@app.route('/sales/item/decrease/<int:sale_id>/<int:product_id>')
def decrease_item(sale_id, product_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT quantity_sold, item_price
        FROM sale_items
        WHERE sale_id=%s AND product_id=%s
    """, (sale_id, product_id))
    item = cursor.fetchone()

    if not item:
        cursor.close()
        conn.close()
        return redirect(f"/sales/add-item/{sale_id}")

    qty = item['quantity_sold']
    price = item['item_price']

    # If would go to zero, remove instead
    if qty == 1:
        cursor.close()
        conn.close()
        return redirect(f"/sales/item/remove/{sale_id}/{product_id}")

    cursor2 = conn.cursor()

    # Decrease quantity
    cursor2.execute("""
        UPDATE sale_items
        SET quantity_sold = quantity_sold - 1
        WHERE sale_id=%s AND product_id=%s
    """, (sale_id, product_id))

    # Restore stock
    cursor2.execute("""
        UPDATE products
        SET quantity = quantity + 1
        WHERE product_id=%s
    """, (product_id,))

    # Reduce sale total
    cursor2.execute("""
        UPDATE sales
        SET total_amount = total_amount - %s
        WHERE sale_id=%s
    """, (price, sale_id))

    conn.commit()
    cursor2.close()
    cursor.close()
    conn.close()

    return redirect(f"/sales/add-item/{sale_id}")


@app.route('/sales/item/remove/<int:sale_id>/<int:product_id>')
def remove_item(sale_id, product_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT quantity_sold, item_price
        FROM sale_items
        WHERE sale_id=%s AND product_id=%s
    """, (sale_id, product_id))
    item = cursor.fetchone()

    if item:
        qty = item['quantity_sold']
        price = item['item_price']
        cursor2 = conn.cursor()

        # Delete the row
        cursor2.execute("""
            DELETE FROM sale_items
            WHERE sale_id=%s AND product_id=%s
        """, (sale_id, product_id))

        # Restore stock
        cursor2.execute("""
            UPDATE products
            SET quantity = quantity + %s
            WHERE product_id=%s
        """, (qty, product_id))

        # Reduce sale total
        cursor2.execute("""
            UPDATE sales
            SET total_amount = total_amount - (%s * %s)
            WHERE sale_id=%s
        """, (price, qty, sale_id))

        conn.commit()
        cursor2.close()

    cursor.close()
    conn.close()
    return redirect(f"/sales/add-item/{sale_id}")


# ----------------------------------------------------
# SALES REPORTS PAGE (uses sales_report view directly)
# ----------------------------------------------------
@app.route('/sales/reports')
def sales_reports():
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Total revenue + items
    cursor.execute("""
        SELECT 
            SUM(line_total) AS total_revenue,
            SUM(quantity_sold) AS total_items
        FROM sales_report
    """)
    summary = cursor.fetchone()

    # Top products
    cursor.execute("""
        SELECT 
            product_name,
            SUM(quantity_sold) AS total_qty,
            SUM(line_total) AS total_amount
        FROM sales_report
        GROUP BY product_name
        ORDER BY total_qty DESC
        LIMIT 10
    """)
    top_products = cursor.fetchall()

    # Today
    cursor.execute("""
        SELECT 
            SUM(line_total) AS revenue_today,
            SUM(quantity_sold) AS qty_today
        FROM sales_report
        WHERE DATE(sale_date) = CURDATE()
    """)
    today = cursor.fetchone()

    # This month
    cursor.execute("""
        SELECT 
            SUM(line_total) AS revenue_month,
            SUM(quantity_sold) AS qty_month
        FROM sales_report
        WHERE MONTH(sale_date) = MONTH(CURDATE())
          AND YEAR(sale_date) = YEAR(CURDATE())
    """)
    month = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template(
        'sales_reports.html',
        summary=summary,
        top_products=top_products,
        today=today,
        month=month
    )


# -----------------------------------
# Logout
# -----------------------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template("500.html"), 500

if __name__ == '__main__':
    initialize_database()
    app.run(debug=True)