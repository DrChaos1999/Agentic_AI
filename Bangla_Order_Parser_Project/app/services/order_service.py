from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Order
from app.schemas import OrderExtraction
from app.services.inventory import get_product
from app.utils.text import stable_message_hash


class DuplicateOrderError(RuntimeError):
    def __init__(self, existing_order_id: int):
        super().__init__(f"Duplicate order detected. Existing order ID: {existing_order_id}")
        self.existing_order_id = existing_order_id


class OrderCreationError(RuntimeError):
    pass


def find_duplicate(
    db: Session,
    message: str,
    idempotency_key: str | None = None,
) -> Order | None:
    if idempotency_key:
        existing = db.scalar(select(Order).where(Order.idempotency_key == idempotency_key))
        if existing:
            return existing

    cutoff = datetime.now(timezone.utc) - timedelta(hours=get_settings().duplicate_window_hours)
    message_hash = stable_message_hash(message)
    return db.scalar(
        select(Order)
        .where(Order.duplicate_hash == message_hash, Order.created_at >= cutoff)
        .order_by(Order.created_at.desc())
    )


def create_order(
    db: Session,
    extraction: OrderExtraction,
    original_message: str,
    idempotency_key: str | None = None,
) -> Order:
    if extraction.missing_fields:
        raise OrderCreationError(f"Missing fields: {', '.join(extraction.missing_fields)}")
    if not extraction.product or not extraction.quantity or not extraction.address:
        raise OrderCreationError("Product, quantity, and address are required")

    duplicate = find_duplicate(db, original_message, idempotency_key)
    if duplicate:
        raise DuplicateOrderError(duplicate.id)

    product = get_product(db, extraction.product)
    if not product:
        raise OrderCreationError(f"Unknown product: {extraction.product}")
    if product.stock_quantity < extraction.quantity:
        raise OrderCreationError("Insufficient stock")

    subtotal = round(product.unit_price * extraction.quantity, 2)
    order = Order(
        idempotency_key=idempotency_key,
        duplicate_hash=stable_message_hash(original_message),
        original_message=original_message,
        normalized_message=extraction.normalized_message,
        product=product.name,
        quantity=extraction.quantity,
        size=extraction.size,
        color=extraction.color,
        delivery_date_label=extraction.delivery_date,
        delivery_date_iso=extraction.delivery_date_iso,
        address=extraction.address,
        customer_name=extraction.customer_name,
        phone=extraction.phone,
        notes=extraction.notes,
        unit_price=product.unit_price,
        subtotal=subtotal,
        status="confirmed",
    )
    product.stock_quantity -= extraction.quantity
    db.add(order)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        duplicate = find_duplicate(db, original_message, idempotency_key)
        if duplicate:
            raise DuplicateOrderError(duplicate.id) from exc
        raise OrderCreationError("Could not create order") from exc
    db.refresh(order)
    return order
