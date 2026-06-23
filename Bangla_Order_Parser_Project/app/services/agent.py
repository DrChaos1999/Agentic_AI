import json

from sqlalchemy.orm import Session

from app.config import get_settings
from app.parsers.factory import parse_order_message
from app.schemas import ProcessOrderResponse, ProcessOrderRequest, ToolTraceItem
from app.services.invoice import generate_invoice
from app.services.order_service import DuplicateOrderError
from app.services.tool_registry import OPENAI_TOOLS, ToolRegistry


class OrderWorkflowAgent:
    """Deterministic, testable tool workflow used by the normal API."""

    def __init__(self, db: Session):
        self.registry = ToolRegistry(db)

    def run(self, request: ProcessOrderRequest) -> ProcessOrderResponse:
        extraction = parse_order_message(request.message, request.parser_mode)
        trace: list[ToolTraceItem] = []

        if extraction.missing_fields:
            missing = ", ".join(extraction.missing_fields)
            return ProcessOrderResponse(
                status="needs_information",
                extraction=extraction,
                confirmation_message=f"অর্ডারটি সম্পূর্ণ করতে এই তথ্যগুলো দিন: {missing}।",
                tool_trace=trace,
            )

        inventory_args = {"product": extraction.product, "quantity": extraction.quantity}
        inventory_result = self.registry.execute("check_inventory", inventory_args)
        trace.append(ToolTraceItem(tool="check_inventory", arguments=inventory_args, result=inventory_result))
        if not inventory_result["available"]:
            return ProcessOrderResponse(
                status="out_of_stock",
                extraction=extraction,
                confirmation_message=(
                    f"দুঃখিত, {extraction.product} এর পর্যাপ্ত স্টক নেই। "
                    f"বর্তমান স্টক: {inventory_result['stock_quantity']}।"
                ),
                tool_trace=trace,
            )

        price_args = {"product": extraction.product, "quantity": extraction.quantity}
        price_result = self.registry.execute("calculate_price", price_args)
        trace.append(ToolTraceItem(tool="calculate_price", arguments=price_args, result=price_result))

        if not request.commit:
            return ProcessOrderResponse(
                status="ready_to_create",
                extraction=extraction,
                confirmation_message=(
                    f"অর্ডার প্রস্তুত: {extraction.quantity}টি {extraction.product}, "
                    f"মোট BDT {price_result['subtotal']:,.2f}।"
                ),
                tool_trace=trace,
            )

        create_args = {
            "product": extraction.product,
            "quantity": extraction.quantity,
            "size": extraction.size,
            "color": extraction.color,
            "delivery_date": extraction.delivery_date,
            "address": extraction.address,
            "customer_name": extraction.customer_name,
            "phone": extraction.phone,
            "notes": extraction.notes,
            "original_message": request.message,
            "idempotency_key": request.idempotency_key,
        }
        try:
            create_result = self.registry.execute("create_order", create_args)
        except DuplicateOrderError as exc:
            return ProcessOrderResponse(
                status="duplicate",
                extraction=extraction,
                order_id=exc.existing_order_id,
                confirmation_message=(
                    f"একই অর্ডার আগে তৈরি হয়েছে। বিদ্যমান Order ID: {exc.existing_order_id}।"
                ),
                tool_trace=trace,
            )

        trace.append(ToolTraceItem(tool="create_order", arguments=create_args, result=create_result))
        invoice_args = {"order_id": create_result["order_id"]}
        invoice_result = self.registry.execute("generate_invoice", invoice_args)
        trace.append(ToolTraceItem(tool="generate_invoice", arguments=invoice_args, result=invoice_result))

        return ProcessOrderResponse(
            status="created",
            extraction=extraction,
            order_id=create_result["order_id"],
            invoice_html=invoice_result["invoice_html"],
            confirmation_message=(
                f"অর্ডার নিশ্চিত হয়েছে। Order ID: {create_result['order_id']}, "
                f"মোট BDT {price_result['subtotal']:,.2f}।"
            ),
            tool_trace=trace,
        )


class OpenAIToolCallingAgent:
    """Optional model-driven function-calling workflow using the Responses API."""

    def __init__(self, db: Session):
        settings = get_settings()
        if not settings.openai_enabled:
            raise RuntimeError("Set OPENAI_API_KEY and OPENAI_MODEL to use the OpenAI tool agent.")
        from openai import OpenAI

        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.registry = ToolRegistry(db)

    def run(self, message: str, idempotency_key: str | None = None) -> tuple[str, list[ToolTraceItem]]:
        system = f"""
You are an order-processing agent for a Bangladeshi online shop.
Understand informal Bangla, Banglish, and English. Normalize products to one of:
shirt, t-shirt, pants, panjabi, saree, shoes, hoodie.
Required fields are product, quantity, and address. If any are missing, ask for them and do not call create_order.
When complete, call tools in a sensible order: check_inventory, calculate_price, create_order, generate_invoice.
Never invent an address. Preserve the original user message in create_order.original_message.
Use this idempotency key when creating the order: {idempotency_key!r}.
""".strip()
        input_items: list = [
            {"role": "system", "content": system},
            {"role": "user", "content": message},
        ]
        trace: list[ToolTraceItem] = []

        for _ in range(8):
            response = self.client.responses.create(
                model=self.model,
                input=input_items,
                tools=OPENAI_TOOLS,
                parallel_tool_calls=False,
            )
            input_items += list(response.output)
            calls = [item for item in response.output if item.type == "function_call"]
            if not calls:
                return response.output_text, trace

            for call in calls:
                arguments = json.loads(call.arguments)
                if call.name == "create_order":
                    arguments["original_message"] = message
                    arguments["idempotency_key"] = idempotency_key
                try:
                    result = self.registry.execute(call.name, arguments)
                except DuplicateOrderError as exc:
                    result = {"created": False, "duplicate": True, "existing_order_id": exc.existing_order_id}
                except Exception as exc:
                    result = {"error": type(exc).__name__, "message": str(exc)}

                trace.append(ToolTraceItem(tool=call.name, arguments=arguments, result=result))
                input_items.append(
                    {
                        "type": "function_call_output",
                        "call_id": call.call_id,
                        "output": json.dumps(result, ensure_ascii=False, default=str),
                    }
                )

        return "The tool-calling loop reached its safety limit.", trace
