from repositories.product_repo import (
    get_all_products,
    get_product,
    add_product,
    update_product,
    delete_product
)

def list_products():
    return get_all_products()

def product_details(product_id):
    return get_product(product_id)

def create_product(name, sku, price, qty, supplier_id):
    add_product(name, sku, price, qty, supplier_id)

def edit_product(product_id, name, sku, price, qty, supplier_id):
    update_product(product_id, name, sku, price, qty, supplier_id)

def remove_product(product_id):
    delete_product(product_id)
