from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Product


SEED_PRODUCTS = [
    {"sku": "SHIRT-001", "name": "shirt", "aliases": "shirt,shirts,শার্ট", "unit_price": 1200.0, "stock_quantity": 25},
    {"sku": "TSHIRT-001", "name": "t-shirt", "aliases": "t-shirt,tshirt,টি-শার্ট,টিশার্ট", "unit_price": 650.0, "stock_quantity": 40},
    {"sku": "PANTS-001", "name": "pants", "aliases": "pant,pants,trouser,প্যান্ট", "unit_price": 1500.0, "stock_quantity": 18},
    {"sku": "PANJABI-001", "name": "panjabi", "aliases": "panjabi,punjabi,পাঞ্জাবি", "unit_price": 1800.0, "stock_quantity": 12},
    {"sku": "SAREE-001", "name": "saree", "aliases": "saree,sari,শাড়ি,শাড়ি", "unit_price": 2200.0, "stock_quantity": 15},
    {"sku": "SHOES-001", "name": "shoes", "aliases": "shoe,shoes,sneaker,জুতা", "unit_price": 2500.0, "stock_quantity": 10},
    {"sku": "HOODIE-001", "name": "hoodie", "aliases": "hoodie,হুডি", "unit_price": 1700.0, "stock_quantity": 8},
]


def seed_inventory(db: Session) -> int:
    created = 0
    for item in SEED_PRODUCTS:
        existing = db.scalar(select(Product).where(Product.sku == item["sku"]))
        if existing:
            continue
        db.add(Product(**item))
        created += 1
    db.commit()
    return created


def get_product(db: Session, product_name: str) -> Product | None:
    normalized = product_name.strip().lower()
    direct = db.scalar(select(Product).where(Product.name == normalized, Product.active.is_(True)))
    if direct:
        return direct

    products = db.scalars(select(Product).where(Product.active.is_(True))).all()
    for product in products:
        aliases = {alias.strip().lower() for alias in product.aliases.split(",") if alias.strip()}
        if normalized in aliases:
            return product
    return None


def check_inventory(db: Session, product: str, quantity: int) -> dict:
    item = get_product(db, product)
    if not item:
        return {
            "available": False,
            "reason": "unknown_product",
            "product": product,
            "requested_quantity": quantity,
            "stock_quantity": 0,
        }
    return {
        "available": item.stock_quantity >= quantity,
        "reason": None if item.stock_quantity >= quantity else "insufficient_stock",
        "product": item.name,
        "sku": item.sku,
        "requested_quantity": quantity,
        "stock_quantity": item.stock_quantity,
        "unit_price": item.unit_price,
    }
