"""Publish the InvoicePDF launch article to dev.to via the official API.

Same legitimate pattern as OGCheck's publisher: the OWNER supplies their dev.to
API key; this posts one honest article via dev.to's sanctioned Articles API.
Idempotent (updates an existing draft/article by title). Pure standard library.

    DEVTO_API_KEY=<key> python publish_devto.py            # draft
    DEVTO_API_KEY=<key> python publish_devto.py --publish  # live
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request

LIVE_URL = "https://invoicepdf-hqz7.onrender.com"
REPO_URL = "https://github.com/rahulatrkm/invoicepdf"

BODY = f"""\
## Generating a PDF shouldn't require a headless browser

Every time I needed to generate an invoice or receipt PDF, the options were:
wrestle a low-level PDF library, fight a templating engine, or spin up headless
Chromium (slow, heavy, breaks on fonts, painful to host). For a *document*, that
felt absurd.

So I built [InvoicePDF]({LIVE_URL}): **POST JSON, get a clean invoice PDF back.**
That's the whole thing.

```bash
curl -X POST {LIVE_URL}/invoice \\
  -H "Content-Type: application/json" \\
  -d '{{
    "number": "INV-2026-001",
    "currency": "USD",
    "seller_name": "Your Company LLC",
    "buyer_name": "Acme Corp",
    "items": [
      {{ "description": "Consulting (hours)", "quantity": 8, "unit_price": 120 }},
      {{ "description": "Software license", "quantity": 1, "unit_price": 299 }}
    ],
    "tax_rate_percent": 10,
    "notes": "Thank you!"
  }}' --output invoice.pdf
```

## Why pure Python (no chromium)

It's built on `fpdf2` — a pure-Python PDF library — so there's **no headless
browser and no system dependencies.** That means it starts instantly, uses
almost no memory, and deploys on a free tier like a static app. For structured
documents (invoices, receipts, statements), you don't need a browser; you need
correct layout and correct math.

## The money math is exact

Financial documents can't have floating-point drift. InvoicePDF does all money
as **integer minor units** (cents/paise) internally, so `$27.00 subtotal + 10%
tax` is exactly `$29.70` — never `$29.700000001`. It handles multiple currencies
(including zero-decimal ones like JPY), fractional quantities (e.g. hours), tax,
notes, and due dates.

## Try it / use it

- **Live playground** (edit JSON, get a PDF): {LIVE_URL}
- **Sample PDF**: {LIVE_URL}/sample
- **Open source (MIT)**: [{REPO_URL}]({REPO_URL})

Free tier is 100 invoices/mo, no signup. If you generate a lot, there's a cheap
paid tier.

What would make this actually useful in your stack — logo/branding, a hosted
template editor, webhooks? Genuinely curious — feedback welcome.
"""

ARTICLE = {
    "article": {
        "title": "I made an invoice PDF API that doesn't need a headless browser",
        "published": False,
        "tags": ["python", "webdev", "api", "showdev"],
        "canonical_url": REPO_URL,
        "description": (
            "POST JSON, get a clean invoice PDF back. Pure Python (fpdf2), no headless "
            "browser, exact money math, free to host and free to try."
        ),
        "body_markdown": BODY,
    }
}

# --- Article 2: a how-to targeting "generate invoice pdf" searchers ----------
BODY_HOWTO = f"""\
## How to generate an invoice PDF (without the usual pain)

If you've tried to generate an invoice or receipt PDF programmatically, you know
the options are all annoying: low-level PDF drawing, HTML-to-PDF via headless
Chromium (heavy, slow, breaks on fonts), or a bloated reporting library. For a
document, that's overkill.

Here are two clean ways — a few lines of Python, or a single API call.

## Option A — one API call (no dependencies)

[InvoicePDF]({LIVE_URL}) takes JSON and returns a PDF. From any language:

```bash
curl -X POST {LIVE_URL}/invoice \\
  -H "Content-Type: application/json" \\
  -d '{{"number":"INV-1","currency":"USD","seller_name":"Me LLC",
       "buyer_name":"Acme Corp",
       "items":[{{"description":"Consulting","quantity":8,"unit_price":120}}],
       "tax_rate_percent":10}}' \\
  --output invoice.pdf
```

That's it — `application/pdf` comes back. Free tier, no signup to try. There's a
live playground at {LIVE_URL} where you can edit the JSON and see the PDF.

## Option B — pure Python with fpdf2

If you'd rather keep it in-process, `fpdf2` is pure Python (no system libs):

```python
from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_font("Helvetica", "B", 20)
pdf.cell(0, 12, "INVOICE", ln=True)
pdf.set_font("Helvetica", size=11)
pdf.cell(0, 8, "Consulting  8 x $120.00 = $960.00", ln=True)
pdf.output("invoice.pdf")
```

## The one thing people get wrong: money math

Do **not** use floats for money. `0.1 + 0.2 != 0.3` in floating point, and on an
invoice that becomes `$29.700000001`. Store amounts as **integer minor units**
(cents), do the math in integers, and format at the end. InvoicePDF does this
internally so totals are always exact.

## Try it

- Live: {LIVE_URL} · Sample: {LIVE_URL}/sample
- Open source (MIT): [{REPO_URL}]({REPO_URL})

What would make it genuinely useful in your stack — logos, templates, webhooks?
Feedback welcome.
"""

# --- Article 3: targets "generate invoice pdf without a headless browser" ----
BODY_NOBROWSER = f"""\
## You probably don't need Chromium to make a PDF

The default advice for "generate a PDF" is HTML-to-PDF via headless Chromium
(Puppeteer/Playwright). For arbitrary web pages, fine. For a **document** with a
known layout — an invoice, a receipt, a statement — it's the wrong tool:

- ~300MB of Chromium to ship and keep patched
- system libraries that break on minimal/serverless images
- seconds of cold-start on the first request
- `--no-sandbox` foot-guns and memory tuning

For structured documents you need correct layout and correct math, not a
browser.

## The lighter approach: render straight from data

[InvoicePDF]({LIVE_URL}) takes JSON and returns a PDF — no browser involved:

```bash
curl -X POST {LIVE_URL}/invoice \\
  -H "Content-Type: application/json" \\
  -d '{{"number":"INV-1","currency":"USD","seller_name":"Me LLC",
       "buyer_name":"Acme Corp",
       "items":[{{"description":"Consulting","quantity":8,"unit_price":120}}],
       "tax_rate_percent":10}}' \\
  --output invoice.pdf
```

Under the hood it's `fpdf2` — pure Python, no system deps — so it starts
instantly, sips memory, and hosts on a free tier like a static app.

## Bonus: get the money math right

Never use floats for money (`0.1 + 0.2 != 0.3`). Keep amounts as **integer minor
units** (cents) and format at the very end, so `$27.00 + 10% tax` is exactly
`$29.70`. InvoicePDF does this internally.

## Try it

- Live playground: {LIVE_URL}
- Sample PDF: {LIVE_URL}/sample
- Open source (MIT): [{REPO_URL}]({REPO_URL})

If you've been reaching for headless Chromium to make invoices, this is a much
lighter path. Feedback welcome.
"""

ARTICLES = {
    "launch": ARTICLE,
    "howto": {
        "article": {
            "title": "How to generate an invoice PDF in Python (2 clean ways)",
            "published": False,
            "tags": ["python", "tutorial", "webdev", "api"],
            "canonical_url": f"{LIVE_URL}/",
            "description": (
                "Two clean ways to generate invoice/receipt PDFs — a one-line API call, or "
                "pure-Python fpdf2 — plus the money-math mistake to avoid."
            ),
            "body_markdown": BODY_HOWTO,
        }
    },
    "nobrowser": {
        "article": {
            "title": "Generate invoice PDFs without a headless browser",
            "published": False,
            "tags": ["python", "webdev", "serverless", "api"],
            "canonical_url": f"{LIVE_URL}/invoice-pdf-without-headless-browser.html",
            "description": (
                "Puppeteer/Chromium is overkill for document PDFs. Generate invoice and receipt "
                "PDFs from JSON with no headless browser — faster, no cold starts, free to host."
            ),
            "body_markdown": BODY_NOBROWSER,
        }
    },
}


def _find_existing(api_key: str, title: str) -> dict | None:
    for state in ("unpublished", "published"):
        req = urllib.request.Request(
            f"https://dev.to/api/articles/me/{state}?per_page=30",
            headers={"api-key": api_key, "User-Agent": "invoicepdf-publisher/1.0"},
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            for art in json.loads(r.read().decode()):
                if art.get("title") == title:
                    return art
    return None


def publish(api_key: str, *, go_live: bool, which: str = "launch") -> dict:
    article = ARTICLES[which]
    article["article"]["published"] = go_live
    existing = _find_existing(api_key, article["article"]["title"])
    data = json.dumps(article).encode()
    if existing is not None:
        req = urllib.request.Request(
            f"https://dev.to/api/articles/{existing['id']}",
            data=data,
            method="PUT",
            headers={"Content-Type": "application/json", "api-key": api_key,
                     "User-Agent": "invoicepdf-publisher/1.0"},
        )
    else:
        req = urllib.request.Request(
            "https://dev.to/api/articles",
            data=data,
            method="POST",
            headers={"Content-Type": "application/json", "api-key": api_key,
                     "User-Agent": "invoicepdf-publisher/1.0"},
        )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def main() -> int:
    key = os.environ.get("DEVTO_API_KEY")
    if not key:
        print("Set DEVTO_API_KEY (https://dev.to/settings/extensions).", file=sys.stderr)
        return 1
    go_live = "--publish" in sys.argv
    which = sys.argv[sys.argv.index("--article") + 1] if "--article" in sys.argv else "launch"
    if which not in ARTICLES:
        print(f"unknown article '{which}'; choose from {list(ARTICLES)}", file=sys.stderr)
        return 1
    try:
        result = publish(key, go_live=go_live, which=which)
    except urllib.error.HTTPError as exc:
        print(f"dev.to API error {exc.code}: {exc.read().decode()}", file=sys.stderr)
        return 2
    print(f"{'PUBLISHED' if go_live else 'DRAFT'}: {result.get('url')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
