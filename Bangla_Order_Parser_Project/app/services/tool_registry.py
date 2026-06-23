from typing import Any, Callable

from sqlalchemy.orm import Session

from app.schemas import OrderExtraction
from app.services.inventory import check_inventory
from app.services.invoice import generate_invoice
from app.services.order_service import create_order
from app.services.pricing import calculate_price
from app.utils.text import normalize_text


ToolFunction = Callable[..., dict]


class ToolRegistry:
    """Routes explicit tool names to safe business functions."""

    def __init__(self, db: Session):
        self.db = db

    def execute(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name == "check_inventory":
            return check_inventory(self.db, arguments["product"], int(arguments["quantity"]))
        if name == "calculate_price":
            return calculate_price(self.db, arguments["product"], int(arguments["quantity"]))
        if name == "create_order":
            original_message = arguments.get("original_message", "")
            extraction = OrderExtraction(
                product=arguments.get("product"),
                quantity=arguments.get("quantity"),
                size=arguments.get("size"),
                color=arguments.get("color"),
                delivery_date=arguments.get("delivery_date"),
                address=arguments.get("address"),
                customer_name=arguments.get("customer_name"),
                phone=arguments.get("phone"),
                notes=arguments.get("notes"),
                missing_fields=[],
                confidence=1.0,
                normalized_message=normalize_text(original_message),
                parser_used="openai_tool_agent",
            )
            order = create_order(
                self.db,
                extraction=extraction,
                original_message=original_message,
                idempotency_key=arguments.get("idempotency_key"),
            )
            return {"created": True, "order_id": order.id, "subtotal": order.subtotal}
        if name == "generate_invoice":
            return generate_invoice(self.db, int(arguments["order_id"]))
        raise ValueError(f"Unknown tool: {name}")


OPENAI_TOOLS = [
    {
        "type": "function",
        "name": "check_inventory",
        "description": "Check whether a normalized product and requested quantity are available.",
        "parameters": {
            "type": "object",
            "properties": {
                "product": {"type": "string"},
                "quantity": {"type": "integer", "minimum": 1},
            },
            "required": ["product", "quantity"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "calculate_price",
        "description": "Calculate the order subtotal in BDT for a product and quantity.",
        "parameters": {
            "type": "object",
            "properties": {
                "product": {"type": "string"},
                "quantity": {"type": "integer", "minimum": 1},
            },
            "required": ["product", "quantity"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "create_order",
        "description": "Create an order only after required fields exist and inventory is available.",
        "parameters": {
            "type": "object",
            "properties": {
                "product": {"type": "string"},
                "quantity": {"type": "integer", "minimum": 1},
                "size": {"type": ["string", "null"]},
                "color": {"type": ["string", "null"]},
                "delivery_date": {"type": ["string", "null"]},
                "address": {"type": "string"},
                "customer_name": {"type": ["string", "null"]},
                "phone": {"type": ["string", "null"]},
                "notes": {"type": ["string", "null"]},
                "original_message": {"type": "string"},
                "idempotency_key": {"type": ["string", "null"]},
            },
            "required": [
                "product", "quantity", "size", "color", "delivery_date", "address",
                "customer_name", "phone", "notes", "original_message", "idempotency_key"
            ],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "generate_invoice",
        "description": "Generate an HTML invoice for a successfully created order.",
        "parameters": {
            "type": "object",
            "properties": {"order_id": {"type": "integer", "minimum": 1}},
            "required": ["order_id"],
            "additionalProperties": False,
        },
        "strict": True,
    },
]
