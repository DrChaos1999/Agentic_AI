import pytest

from app.parsers.rule_based import RuleBasedBanglaOrderParser
from app.services.inventory import check_inventory
from app.services.invoice import generate_invoice
from app.services.order_service import DuplicateOrderError, create_order
from app.services.pricing import calculate_price


def test_inventory_available(db):
    result = check_inventory(db, "shirt", 2)
    assert result["available"] is True
    assert result["stock_quantity"] == 25


def test_inventory_insufficient(db):
    result = check_inventory(db, "hoodie", 99)
    assert result["available"] is False
    assert result["reason"] == "insufficient_stock"


def test_price_calculation(db):
    result = calculate_price(db, "shirt", 2)
    assert result["subtotal"] == 2400.0
    assert result["currency"] == "BDT"


def test_create_order_reduces_stock(db):
    message = "blue XL shirt 2টা আগের address"
    extraction = RuleBasedBanglaOrderParser().parse(message)
    order = create_order(db, extraction, message, idempotency_key="test-order-1")
    assert order.id is not None
    inventory = check_inventory(db, "shirt", 24)
    assert inventory["available"] is False
    assert inventory["stock_quantity"] == 23


def test_duplicate_by_message(db):
    message = "blue XL shirt 2টা আগের address"
    extraction = RuleBasedBanglaOrderParser().parse(message)
    create_order(db, extraction, message)
    with pytest.raises(DuplicateOrderError):
        create_order(db, extraction, message)


def test_invoice_generation(db):
    message = "blue XL shirt 2টা আগের address"
    extraction = RuleBasedBanglaOrderParser().parse(message)
    order = create_order(db, extraction, message, idempotency_key="invoice-test")
    result = generate_invoice(db, order.id)
    assert result["found"] is True
    assert f"Invoice #{order.id}" in result["invoice_html"]
    assert "BDT 2,400.00" in result["invoice_html"]
