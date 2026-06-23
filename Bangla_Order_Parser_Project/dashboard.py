import os
import uuid

import pandas as pd
import requests
import streamlit as st


API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")

st.set_page_config(page_title="Bangla Order Agent", page_icon="🛒", layout="wide")
st.title("🛒 Bangla Order Agent")
st.caption("Informal Bangla/Banglish messages → structured, validated online orders")


def api_request(method: str, path: str, **kwargs):
    try:
        response = requests.request(method, f"{API_URL}{path}", timeout=30, **kwargs)
        if response.status_code >= 400:
            detail = response.json().get("detail", response.text)
            raise RuntimeError(f"API error {response.status_code}: {detail}")
        return response
    except requests.RequestException as exc:
        raise RuntimeError(f"Cannot reach API at {API_URL}: {exc}") from exc


with st.sidebar:
    st.subheader("Connection")
    st.code(API_URL)
    try:
        health = api_request("GET", "/health").json()
        st.success("API connected")
        st.write(f"OpenAI mode: {'enabled' if health['openai_enabled'] else 'disabled'}")
    except RuntimeError as exc:
        st.error(str(exc))

parse_tab, orders_tab, inventory_tab, about_tab = st.tabs(
    ["Parse & Create", "Orders", "Inventory", "About"]
)

with parse_tab:
    st.subheader("Create an order from a message")
    example = "ভাই blue color এর XL shirt দুইটা কালকে আগের address এ পাঠাবেন"
    message = st.text_area("Customer message", value=example, height=120)
    col1, col2, col3 = st.columns(3)
    parser_mode = col1.selectbox("Parser", ["auto", "rule", "openai"])
    commit = col2.checkbox("Create order in database", value=True)
    use_unique_key = col3.checkbox("Generate idempotency key", value=True)

    if st.button("Process order", type="primary", use_container_width=True):
        payload = {
            "message": message,
            "parser_mode": parser_mode,
            "commit": commit,
            "idempotency_key": str(uuid.uuid4()) if use_unique_key else None,
        }
        try:
            result = api_request("POST", "/api/v1/orders/process", json=payload).json()
            status = result["status"]
            if status == "created":
                st.success(result["confirmation_message"])
            elif status in {"needs_information", "out_of_stock", "duplicate"}:
                st.warning(result["confirmation_message"])
            else:
                st.info(result["confirmation_message"])

            st.markdown("#### Structured extraction")
            st.json(result["extraction"])
            st.markdown("#### Tool trace")
            st.json(result["tool_trace"])

            if result.get("invoice_html"):
                st.download_button(
                    "Download invoice (HTML)",
                    data=result["invoice_html"],
                    file_name=f"invoice-{result['order_id']}.html",
                    mime="text/html",
                )
        except RuntimeError as exc:
            st.error(str(exc))

    st.divider()
    st.subheader("Optional: OpenAI function-calling agent")
    st.caption("Requires OPENAI_API_KEY and OPENAI_MODEL in the API environment.")
    if st.button("Run model-driven tool agent"):
        payload = {"message": message, "idempotency_key": str(uuid.uuid4())}
        try:
            result = api_request("POST", "/api/v1/agent/openai", json=payload).json()
            st.write(result["final_text"])
            st.json(result["tool_trace"])
        except RuntimeError as exc:
            st.error(str(exc))

with orders_tab:
    st.subheader("Recent orders")
    if st.button("Refresh orders"):
        st.rerun()
    try:
        orders = api_request("GET", "/api/v1/orders").json()
        if orders:
            df = pd.DataFrame(orders)
            st.dataframe(df, use_container_width=True, hide_index=True)
            csv = df.to_csv(index=False).encode("utf-8-sig")
            st.download_button("Download orders CSV", csv, "orders.csv", "text/csv")
        else:
            st.info("No orders yet.")
    except RuntimeError as exc:
        st.error(str(exc))

with inventory_tab:
    st.subheader("Inventory")
    try:
        inventory = api_request("GET", "/api/v1/inventory").json()
        st.dataframe(pd.DataFrame(inventory), use_container_width=True, hide_index=True)
    except RuntimeError as exc:
        st.error(str(exc))

with about_tab:
    st.markdown(
        """
### What this project demonstrates

- Bangla and Banglish information extraction
- Pydantic structured validation
- FastAPI endpoints and OpenAPI documentation
- SQLite persistence with SQLAlchemy
- Inventory, price, duplicate, and invoice tools
- A deterministic agent workflow plus optional OpenAI function calling
- Streamlit dashboard, tests, Docker, and CI

The rule parser works without paid APIs. OpenAI integration is optional.
"""
    )
