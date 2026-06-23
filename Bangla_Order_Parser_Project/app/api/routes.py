from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import Order, Product
from app.parsers.factory import parse_order_message
from app.parsers.openai_parser import ParserUnavailableError
from app.schemas import (
    MessageRequest,
    OpenAIAgentRequest,
    OpenAIAgentResponse,
    OrderExtraction,
    OrderRead,
    ProcessOrderRequest,
    ProcessOrderResponse,
    ProductRead,
)
from app.services.agent import OpenAIToolCallingAgent, OrderWorkflowAgent
from app.services.inventory import seed_inventory
from app.services.invoice import generate_invoice


router = APIRouter()


@router.get("/health")
def health() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "openai_enabled": settings.openai_enabled,
    }


@router.post("/api/v1/parse", response_model=OrderExtraction)
def parse_message(payload: MessageRequest) -> OrderExtraction:
    try:
        return parse_order_message(payload.message, payload.parser_mode)
    except ParserUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/api/v1/orders/process", response_model=ProcessOrderResponse)
def process_order(payload: ProcessOrderRequest, db: Session = Depends(get_db)) -> ProcessOrderResponse:
    return OrderWorkflowAgent(db).run(payload)


@router.get("/api/v1/orders", response_model=list[OrderRead])
def list_orders(
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[Order]:
    return list(db.scalars(select(Order).order_by(desc(Order.created_at)).limit(limit)).all())


@router.get("/api/v1/orders/{order_id}", response_model=OrderRead)
def get_order(order_id: int, db: Session = Depends(get_db)) -> Order:
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.get("/api/v1/inventory", response_model=list[ProductRead])
def list_inventory(db: Session = Depends(get_db)) -> list[Product]:
    return list(db.scalars(select(Product).order_by(Product.name)).all())


@router.post("/api/v1/inventory/seed")
def seed(db: Session = Depends(get_db)) -> dict:
    return {"created": seed_inventory(db)}


@router.get("/api/v1/invoices/{order_id}", response_class=HTMLResponse)
def invoice(order_id: int, db: Session = Depends(get_db)) -> HTMLResponse:
    result = generate_invoice(db, order_id)
    if not result["found"]:
        raise HTTPException(status_code=404, detail="Order not found")
    return HTMLResponse(result["invoice_html"])


@router.post("/api/v1/agent/openai", response_model=OpenAIAgentResponse)
def openai_agent(payload: OpenAIAgentRequest, db: Session = Depends(get_db)) -> OpenAIAgentResponse:
    if not get_settings().openai_enabled:
        raise HTTPException(
            status_code=503,
            detail="Set OPENAI_API_KEY and OPENAI_MODEL to enable the OpenAI tool agent.",
        )
    final_text, trace = OpenAIToolCallingAgent(db).run(payload.message, payload.idempotency_key)
    return OpenAIAgentResponse(final_text=final_text, tool_trace=trace)
