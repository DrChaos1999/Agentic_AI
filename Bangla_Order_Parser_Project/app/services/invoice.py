from html import escape

from sqlalchemy.orm import Session

from app.models import Order


def generate_invoice(db: Session, order_id: int) -> dict:
    order = db.get(Order, order_id)
    if not order:
        return {"found": False, "order_id": order_id, "invoice_html": None}

    customer = escape(order.customer_name or "Customer")
    product_details = " ".join(
        part for part in [order.product, order.color or "", order.size or ""] if part
    )
    delivery = order.delivery_date_iso.isoformat() if order.delivery_date_iso else (order.delivery_date_label or "Not specified")
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Invoice #{order.id}</title>
  <style>
    body {{ font-family: Arial, sans-serif; max-width: 760px; margin: 40px auto; color: #222; }}
    h1 {{ margin-bottom: 4px; }}
    .muted {{ color: #666; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 24px; }}
    th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
    th {{ background: #f5f5f5; }}
    .total {{ font-size: 1.2rem; font-weight: bold; text-align: right; margin-top: 20px; }}
  </style>
</head>
<body>
  <h1>Bangla Order Agent</h1>
  <div class="muted">Invoice #{order.id}</div>
  <p><strong>Customer:</strong> {customer}</p>
  <p><strong>Delivery address:</strong> {escape(order.address)}</p>
  <p><strong>Requested delivery:</strong> {escape(delivery)}</p>
  <table>
    <thead><tr><th>Item</th><th>Quantity</th><th>Unit price</th><th>Subtotal</th></tr></thead>
    <tbody>
      <tr>
        <td>{escape(product_details)}</td>
        <td>{order.quantity}</td>
        <td>BDT {order.unit_price:,.2f}</td>
        <td>BDT {order.subtotal:,.2f}</td>
      </tr>
    </tbody>
  </table>
  <div class="total">Total: BDT {order.subtotal:,.2f}</div>
</body>
</html>"""
    return {"found": True, "order_id": order.id, "invoice_html": html}
