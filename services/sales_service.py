from repositories.sales_repo import (
    get_sales_list,
    get_sale_details,
)
from repositories.product_repo import get_product

def list_sales():
    return get_sales_list()

def sale_info(sale_id):
    return get_sale_details(sale_id)
