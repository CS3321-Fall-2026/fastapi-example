# FastAPI Foreign Exchange Example

A simple FastAPI application demonstrating REST API development with foreign exchange operations.

## Setup

1. Install dependencies:
```bash
uv sync
```

2. Activate virtual environment:
```bash
source .venv/bin/activate
```

## Running the Application

```bash
uvicorn src.fastapi_example.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### GET /currencies
Returns list of supported currencies.

**Example:**
```bash
curl http://localhost:8000/currencies
```

### POST /currency_supported
Check if a currency is supported.

**Example:**
```bash
curl -X POST http://localhost:8000/currency_supported \
  -H "Content-Type: application/json" \
  -d '{"currency_name": "dollar"}'
```

### GET /exchange_rate
Get real-time exchange rates (uses free Frankfurter API).

**Parameters:**
- `from_currency`: Source currency code (default: USD)
- `to_currency`: Target currency code (default: EUR)
- `amount`: Amount to convert (default: 1.0)

**Example:**
```bash
curl "http://localhost:8000/exchange_rate?from_currency=USD&to_currency=GBP&amount=100"
```

## Interactive Documentation
The bottom are some examples - 
FastAPI automatically generates interactive API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
