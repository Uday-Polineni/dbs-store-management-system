from repositories.supplier_repo import (
    get_suppliers,
    get_supplier,
    add_supplier,
    update_supplier,
    delete_supplier
)

def list_suppliers():
    return get_suppliers()

def supplier_details(supplier_id):
    return get_supplier(supplier_id)

def create_supplier(name, contact):
    add_supplier(name, contact)

def edit_supplier(supplier_id, name, contact):
    update_supplier(supplier_id, name, contact)

def remove_supplier(supplier_id):
    delete_supplier(supplier_id)
