# InvoicePDF

**Generate clean invoice & receipt PDFs from JSON — one API call.**

Stop wrestling with PDF libraries, templates, and headless browsers. POST
structured JSON, get a professional invoice PDF back. Exact money math (integer
minor units — no floating-point drift), tax support, notes, due dates.

Only one dependency (`fpdf2`) — **no headless browser, no system libraries** — so
it deploys free anywhere, like a static app.

---

## The whole API

```bash
curl -X POST https://YOUR-HOST/invoice \
  -H "Content-Type: application/json" \
  -d '{
    "number": "INV-2026-001",
    "currency": "USD",
    "seller_name": "Your Company LLC",
    "buyer_name": "Acme Corp",
    "items": [
      { "description": "Consulting (hours)", "quantity": 8, "unit_price": 120 },
      { "description": "Software license", "quantity": 1, "unit_price": 299 }
    ],
    "tax_rate_percent": 10,
    "notes": "Thank you!"
  }' --output invoice.pdf
```

JSON in, `application/pdf` out. That's the whole product.

- `GET /` — landing page with a live "try it" editor
- `GET /sample` — a sample invoice PDF (see output instantly)
- `GET /healthz` — health check
- `POST /invoice` — JSON → PDF

## Run it

```bash
pip install -e .
python -m invoicepdf.api           # serves on :8000
# or for production:
gunicorn --bind=0.0.0.0:8000 wsgi:app
```

## Deploy free

Single small process, one Python dep. Host on any free tier:

```bash
docker build -t invoicepdf . && docker run -p 8000:8000 invoicepdf
```

Or Azure App Service (Python): startup command `gunicorn --bind=0.0.0.0:8000 wsgi:app`.

## Pricing

| | Price | |
| --- | --- | --- |
| Free | $0 | 100 invoices/mo, no signup, 20 req/min |
| Pro | $9/mo | 1,000/mo, API key, your logo |
| Crypto | USDC on Base | no account; on-chain, auto-recognized |

## Why it exists (honest)

Business #2 of an autonomous enterprise. The doc-generation market has strong,
proven willingness-to-pay (invoices are a business line-item). This targets that
slice with a **pure-Python, free-to-host** build — no chromium, no infra cost.

Like every product here: it's real and it works, but earning revenue depends on
distribution and real customers, not code. Status: **built, not yet launched.**

MIT licensed.
