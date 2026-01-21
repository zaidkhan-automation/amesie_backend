def product_list_key(**kwargs):
    return "products:list:" + ":".join(str(v) for v in kwargs.values())

def product_key(product_id: int):
    return f"product:{product_id}"
