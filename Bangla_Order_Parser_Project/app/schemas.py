from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


ParserMode = Literal["auto", "rule", "openai"]


class MessageRequest(BaseModel):
    message: str = Field(min_length=3, max_length=2000)
    parser_mode: ParserMode = "auto"

    @field_validator("message")
    @classmethod
    def clean_message(cls, value: str) -> str:
        cleaned = " ".join(value.strip().split())
        if not cleaned:
            raise ValueError("message cannot be empty")
        return cleaned


class ProcessOrderRequest(MessageRequest):
    commit: bool = True
    idempotency_key: str | None = Field(default=None, min_length=4, max_length=100)


class OrderExtraction(BaseModel):
    product: str | None = None
    quantity: int | None = Field(default=None, ge=1, le=1000)
    size: str | None = None
    color: str | None = None
    delivery_date: str | None = None
    delivery_date_iso: date | None = None
    address: str | None = None
    customer_name: str | None = None
    phone: str | None = None
    notes: str | None = None
    missing_fields: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    normalized_message: str
    parser_used: str

    @field_validator("size")
    @classmethod
    def normalize_size(cls, value: str | None) -> str | None:
        return value.upper() if value else value


class ToolTraceItem(BaseModel):
    tool: str
    arguments: dict[str, Any]
    result: dict[str, Any]


class ProcessOrderResponse(BaseModel):
    status: Literal[
        "needs_information",
        "out_of_stock",
        "ready_to_create",
        "created",
        "duplicate",
    ]
    extraction: OrderExtraction
    confirmation_message: str
    order_id: int | None = None
    invoice_html: str | None = None
    tool_trace: list[ToolTraceItem] = Field(default_factory=list)


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sku: str
    name: str
    unit_price: float
    stock_quantity: int
    active: bool


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    idempotency_key: str | None
    original_message: str
    product: str
    quantity: int
    size: str | None
    color: str | None
    delivery_date_label: str | None
    delivery_date_iso: date | None
    address: str
    customer_name: str | None
    phone: str | None
    notes: str | None
    unit_price: float
    subtotal: float
    status: str
    created_at: datetime


class OpenAIAgentRequest(BaseModel):
    message: str = Field(min_length=3, max_length=2000)
    idempotency_key: str | None = Field(default=None, min_length=4, max_length=100)


class OpenAIAgentResponse(BaseModel):
    final_text: str
    tool_trace: list[ToolTraceItem]
