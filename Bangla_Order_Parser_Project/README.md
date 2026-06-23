# Bangla Order Agent

[![Tests](https://img.shields.io/badge/tests-pytest-blue)](#testing)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Convert informal **Bangla, Banglish, and English customer messages** into structured, validated online orders. The application extracts products, quantities, variants, delivery information, and addresses; checks inventory; calculates prices; prevents duplicates; creates orders in SQLite; and generates downloadable HTML invoices.

The project runs in a completely free **rule-based mode** and offers optional OpenAI structured extraction and function calling.

## Demo input and output

**Input**

```text
ভাই blue color এর XL shirt দুইটা কালকে আগের address এ পাঠাবেন
```

**Structured extraction**

```json
{
  "product": "shirt",
  "quantity": 2,
  "size": "XL",
  "color": "blue",
  "delivery_date": "tomorrow",
  "address": "previous address",
  "missing_fields": []
}
```

## Why this is more than a chatbot

The language layer does not directly change inventory or write arbitrary database records. It produces structured information or requests explicit tools. The transactional layer then validates and executes those operations.

```text
Customer message
      │
      ▼
Rule parser or OpenAI structured parser
      │
      ▼
Pydantic OrderExtraction
      │
      ▼
Order workflow / optional model tool agent
      │
      ├── check_inventory
      ├── calculate_price
      ├── create_order
      └── generate_invoice
      │
      ▼
SQLite + FastAPI + Streamlit dashboard
```

## Features

- Bangla, Banglish, and English message parsing
- Product, quantity, size, color, date, address, and phone extraction
- Bengali-digit and number-word handling
- Pydantic v2 structured validation
- Missing-information detection
- Inventory availability checks
- Price calculation in BDT
- Confirmation-message generation in Bangla
- SQLite persistence with SQLAlchemy 2
- Idempotency-key and message-hash duplicate protection
- Downloadable HTML invoices
- FastAPI REST endpoints and automatic Swagger documentation
- Streamlit order and inventory dashboard
- Optional OpenAI structured output parser
- Optional OpenAI Responses API function-calling agent
- Docker Compose, Pytest coverage, and GitHub Actions CI

## Project structure

```text
bangla-order-agent/
├── app/
│   ├── api/routes.py
│   ├── parsers/
│   │   ├── factory.py
│   │   ├── openai_parser.py
│   │   └── rule_based.py
│   ├── services/
│   │   ├── agent.py
│   │   ├── inventory.py
│   │   ├── invoice.py
│   │   ├── order_service.py
│   │   ├── pricing.py
│   │   └── tool_registry.py
│   ├── config.py
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   └── schemas.py
├── data/sample_messages.json
├── scripts/seed_db.py
├── tests/
├── dashboard.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## Quick start on Windows

### 1. Create and activate a virtual environment

```powershell
python -m venv .venv
.venv\Scriptsctivate
```

### 2. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Create environment file

```powershell
Copy-Item .env.example .env
```

The project works immediately without an OpenAI key.

### 4. Start the API

```powershell
uvicorn app.main:app --reload
```

Open:

- API documentation: `http://localhost:8000/docs`
- Health endpoint: `http://localhost:8000/health`

### 5. Start the Streamlit dashboard

Open a second terminal, activate the same virtual environment, and run:

```powershell
streamlit run dashboard.py
```

Dashboard: `http://localhost:8501`

## Quick start with Docker

```bash
docker compose up --build
```

Then open:

- Dashboard: `http://localhost:8501`
- Swagger API docs: `http://localhost:8000/docs`

SQLite data is persisted in the `order_data` Docker volume.

## API examples

### Parse without creating an order

```bash
curl -X POST http://localhost:8000/api/v1/parse   -H "Content-Type: application/json"   -d '{
    "message": "ভাই blue XL shirt দুইটা আগের address এ পাঠাবেন",
    "parser_mode": "rule"
  }'
```

### Preview the full workflow

```bash
curl -X POST http://localhost:8000/api/v1/orders/process   -H "Content-Type: application/json"   -d '{
    "message": "ভাই blue XL shirt দুইটা আগের address এ পাঠাবেন",
    "parser_mode": "rule",
    "commit": false
  }'
```

### Create an order

```bash
curl -X POST http://localhost:8000/api/v1/orders/process   -H "Content-Type: application/json"   -d '{
    "message": "ভাই blue XL shirt দুইটা আগের address এ পাঠাবেন",
    "parser_mode": "rule",
    "commit": true,
    "idempotency_key": "customer-101-message-55"
  }'
```

## Parser modes

| Mode | Behavior |
|---|---|
| `rule` | Always uses the transparent local parser. No API key required. |
| `openai` | Requires OpenAI configuration and returns an error when unavailable. |
| `auto` | Tries OpenAI when configured, then safely falls back to the rule parser. |

## Optional OpenAI integration

Add these values to `.env`:

```env
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=your_supported_model_name
```

Two separate OpenAI capabilities are included:

1. **Structured extraction** through `POST /api/v1/parse` with `parser_mode=openai`.
2. **Function-calling agent** through `POST /api/v1/agent/openai`.

The function-calling agent can request these tools:

- `check_inventory`
- `calculate_price`
- `create_order`
- `generate_invoice`

The Python service layer—not the model—performs the real transaction and validates every tool argument.

## Duplicate handling

The project prevents accidental repeated orders in two ways:

1. `idempotency_key`: the calling client can reuse the same key during retries.
2. Normalized message hash: identical messages are treated as duplicates for `DUPLICATE_WINDOW_HOURS` (24 by default).

A duplicate request returns the existing order ID and does not reduce inventory again.

## Testing

Run all tests:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=app --cov-report=term-missing
```

The included suite covers:

- Bangla digits and number words
- Bangla/Banglish product and color aliases
- Missing fields
- Delivery dates
- Inventory and pricing
- Stock reduction
- Duplicate protection
- Invoice generation
- API parsing, preview, creation, listing, and errors

## Suggested GitHub screenshots

After running the project, add these images to a `screenshots/` folder:

1. Streamlit parser screen with the sample Bangla order
2. Structured extraction JSON
3. Tool trace showing four tool calls
4. Orders dashboard
5. Inventory dashboard
6. Swagger API documentation
7. Generated invoice
8. Passing test and coverage output

Embed them near the top of this README to improve recruiter impact.

## Production improvements

- Replace SQLite with PostgreSQL
- Add authentication and seller workspaces
- Encrypt customer phone and address data
- Add catalog-specific size/color validation
- Add customer confirmation before `create_order`
- Add Messenger or WhatsApp webhook adapters
- Add observability, rate limiting, and background jobs
- Build a labeled Bangla/Banglish evaluation dataset
- Compare rule, LLM, and hybrid parser precision/recall
- Add human review for low-confidence extractions
- Render invoices to PDF with an embedded Bengali font

## Responsible use

This is a portfolio and learning project. Before using it with real customers, add access control, privacy notices, secrets management, audit logging, backups, and a human confirmation step for uncertain orders.

## License

MIT — see [LICENSE](LICENSE).
