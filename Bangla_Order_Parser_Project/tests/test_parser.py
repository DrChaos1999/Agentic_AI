from datetime import date, timedelta

import pytest

from app.parsers.rule_based import RuleBasedBanglaOrderParser


@pytest.fixture
def parser() -> RuleBasedBanglaOrderParser:
    return RuleBasedBanglaOrderParser()


def test_expected_example(parser):
    result = parser.parse("ভাই blue color এর XL shirt দুইটা কালকে আগের address এ পাঠাবেন")
    assert result.product == "shirt"
    assert result.quantity == 2
    assert result.size == "XL"
    assert result.color == "blue"
    assert result.delivery_date == "tomorrow"
    assert result.delivery_date_iso == date.today() + timedelta(days=1)
    assert result.address == "previous address"
    assert result.missing_fields == []


@pytest.mark.parametrize(
    ("message", "product", "quantity"),
    [
        ("কালো t-shirt 3টা আগের ঠিকানায় পাঠান", "t-shirt", 3),
        ("একটা লাল পাঞ্জাবি previous address", "panjabi", 1),
        ("2 pcs blue shoes address: Dhanmondi 27, Dhaka", "shoes", 2),
        ("সাদা শাড়ি দুইটা ঠিকানা: মিরপুর ১০", "saree", 2),
        ("green hoodie one pc same address", "hoodie", 1),
    ],
)
def test_product_and_quantity_variations(parser, message, product, quantity):
    result = parser.parse(message)
    assert result.product == product
    assert result.quantity == quantity


def test_bangla_digits(parser):
    result = parser.parse("নীল shirt ৪টা আগের address")
    assert result.quantity == 4


def test_phone_extraction(parser):
    result = parser.parse("shirt 1টা address: Uttara phone: 01712345678")
    assert result.phone == "01712345678"


def test_missing_fields(parser):
    result = parser.parse("কালকে পাঠাবেন")
    assert set(result.missing_fields) == {"product", "quantity", "address"}


def test_explicit_iso_date(parser):
    result = parser.parse("shirt 1টা 2026-07-01 address: Banani")
    assert result.delivery_date_iso.isoformat() == "2026-07-01"
