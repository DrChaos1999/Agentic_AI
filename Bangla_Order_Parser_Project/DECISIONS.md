# Engineering Decisions

## 1. Rule parser first, LLM second

The repository works without an API key. The deterministic parser makes the core behavior inspectable, cheap, and easy to test. OpenAI structured output and function calling are optional enhancements.

## 2. Business tools are ordinary Python functions

Inventory checks, pricing, order creation, duplicate detection, and invoice generation are independent of the language model. This prevents the LLM from becoming the source of truth for transactions.

## 3. Required fields are intentionally small

The MVP requires `product`, `quantity`, and `address`. Size, color, delivery date, phone, and customer name are optional because real messages often omit them.

## 4. Duplicate protection uses two mechanisms

- An optional idempotency key protects clients retrying the same request.
- A normalized-message hash blocks accidental duplicate submissions during a configurable time window.

## 5. HTML invoices instead of PDF

HTML is dependency-light, browser friendly, downloadable, and avoids Bengali-font embedding problems. A production extension can render the HTML to PDF.

## 6. SQLite for the portfolio MVP

SQLite keeps local setup simple. The SQLAlchemy layer allows a later move to PostgreSQL without rewriting the service layer.
