from sqlalchemy.orm import Session

from app.services.inventory import get_product


class PricingError(ValueError):
    pass


def calculate_price(db: Session, product: str, quantity: int) -> dict:
    item = get_product(db, product)
    if not item:
        raise PricingError(f"Unknown product: {product}")
    if quantity < 1:
        raise PricingError("Quantity must be at least 1")

    subtotal = round(item.unit_price * quantity, 2)
    return {
        "product": item.name,
        "quantity": quantity,
        "currency": "BDT",
        "unit_price": item.unit_price,
        "subtotal": subtotal,
    }
