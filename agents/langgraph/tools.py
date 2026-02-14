from typing import Optional, Dict, Any
from sqlalchemy.exc import SQLAlchemyError
import uuid
import ast
import operator as op

from core.database import SessionLocal
from db import models


# ---------- CREATE PRODUCT ----------
def seller_create_product_tool(
    *,
    seller_id: int,
    name: str,
    price: float,
    stock_quantity: int,
    category_id: int,
    description: Optional[str] = None,
):
    db = SessionLocal()
    try:
        sku = f"SKU-{uuid.uuid4().hex[:10].upper()}"

        product = models.Product(
            name=name,
            description=description,
            price=price,
            sku=sku,
            stock_quantity=stock_quantity,
            category_id=category_id,
            seller_id=seller_id,
        )

        db.add(product)
        db.commit()
        db.refresh(product)

        return {
            "status": "ok",
            "product": {
                "id": product.id,
                "name": product.name,
                "price": product.price,
                "stock_quantity": product.stock_quantity,
                "sku": product.sku,
            },
        }

    except SQLAlchemyError as e:
        db.rollback()
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


# ---------- UPDATE PRICE ----------
def seller_update_price_tool(*, seller_id: int, product_id: int, new_price: float):
    db = SessionLocal()
    try:
        product = db.query(models.Product).filter(
            models.Product.id == product_id,
            models.Product.seller_id == seller_id,
            models.Product.is_deleted == False,
        ).first()

        if not product:
            return {"status": "error", "error": "Product not found"}

        product.price = new_price
        db.commit()
        return {"status": "ok", "product_id": product_id, "new_price": new_price}

    except SQLAlchemyError as e:
        db.rollback()
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


# ---------- UPDATE STOCK ----------
def seller_update_stock_tool(*, seller_id: int, product_id: int, stock_quantity: int):
    db = SessionLocal()
    try:
        product = db.query(models.Product).filter(
            models.Product.id == product_id,
            models.Product.seller_id == seller_id,
            models.Product.is_deleted == False,
        ).first()

        if not product:
            return {"status": "error", "error": "Product not found"}

        product.stock_quantity = stock_quantity
        db.commit()
        return {"status": "ok", "product_id": product_id, "stock_quantity": stock_quantity}

    except SQLAlchemyError as e:
        db.rollback()
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


# ---------- DELETE PRODUCT ----------
def seller_delete_product_tool(*, seller_id: int, product_id: int):
    db = SessionLocal()
    try:
        product = db.query(models.Product).filter(
            models.Product.id == product_id,
            models.Product.seller_id == seller_id,
            models.Product.is_deleted == False,
        ).first()

        if not product:
            return {"status": "error", "error": "Product not found"}

        product.is_deleted = True
        db.commit()
        return {"status": "ok", "product_id": product_id}

    except SQLAlchemyError as e:
        db.rollback()
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


# ---------- LIST PRODUCTS ----------
def seller_list_products_tool(*, seller_id: int):
    db = SessionLocal()
    try:
        products = db.query(models.Product).filter(
            models.Product.seller_id == seller_id,
            models.Product.is_deleted == False,
        ).order_by(models.Product.created_at.desc()).all()

        return {
            "status": "ok",
            "products": [
                {
                    "id": p.id,
                    "name": p.name,
                    "price": p.price,
                    "stock_quantity": p.stock_quantity,
                    "sku": p.sku,
                }
                for p in products
            ],
        }

    except SQLAlchemyError as e:
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


# ---------- CALCULATOR (FIXED, SAFE, PRECEDENCE AWARE) ----------
_ALLOWED_OPS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.USub: op.neg,
}

def _safe_eval(node):
    if isinstance(node, ast.Num):
        return node.n
    if isinstance(node, ast.BinOp):
        return _ALLOWED_OPS[type(node.op)](
            _safe_eval(node.left),
            _safe_eval(node.right),
        )
    if isinstance(node, ast.UnaryOp):
        return _ALLOWED_OPS[type(node.op)](_safe_eval(node.operand))
    raise ValueError("Invalid expression")

def calculator_tool(*, expression: str) -> Dict[str, Any]:
    try:
        tree = ast.parse(expression, mode="eval")
        result = _safe_eval(tree.body)
        return {"status": "ok", "expression": expression, "result": result}
    except ZeroDivisionError:
        return {"status": "error", "error": "Division by zero"}
    except Exception:
        return {"status": "error", "error": "Invalid expression"}
