"""InvoicePDF static SEO page generator — pure standard library, no deps.

Renders genuinely-helpful landing pages targeting the high-commercial-intent
terms people search when they need to generate documents ("html to pdf api",
"invoice pdf api", "generate receipt pdf"). Each page has real content plus a
live "try it" call to action, so it earns the visit and converts.

Run: ``python -m invoicepdf.seo`` → writes HTML + sitemap.xml into ``web/``.
"""

from __future__ import annotations

import html
import os
from dataclasses import dataclass, field
from pathlib import Path

SITE_URL = os.environ.get("INVOICEPDF_SITE_URL", "https://invoicepdf-app.azurewebsites.net").rstrip("/")
_WEB_DIR = Path(__file__).resolve().parent.parent / "web"


@dataclass(frozen=True)
class Page:
    slug: str
    title: str
    description: str
    intro: str
    sections: list[tuple[str, str]] = field(default_factory=list)
    keywords: str = ""


def _related(pages: list[Page], current: Page) -> str:
    items = [
        f'<li><a href="/{p.slug}">{html.escape(p.title)}</a></li>'
        for p in pages
        if p.slug != current.slug
    ]
    return "<ul>" + "".join(items) + "</ul>"


def _render(page: Page, pages: list[Page]) -> str:
    canonical = f"{SITE_URL}/{page.slug}"
    body = "".join(f"<h2>{html.escape(h)}</h2>\n{b}\n" for h, b in page.sections)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{html.escape(page.title)} · InvoicePDF</title>
  <meta name="description" content="{html.escape(page.description)}" />
  <meta name="keywords" content="{html.escape(page.keywords)}" />
  <link rel="canonical" href="{canonical}" />
  <meta property="og:title" content="{html.escape(page.title)}" />
  <meta property="og:description" content="{html.escape(page.description)}" />
  <meta property="og:type" content="article" />
  <meta property="og:url" content="{canonical}" />
  <meta name="twitter:card" content="summary_large_image" />
  <style>
    body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
            color:#0f172a; background:#faf5ff; line-height:1.65; }}
    .wrap {{ max-width:720px; margin:0 auto; padding:40px 20px 64px; }}
    h1 {{ font-size:2rem; line-height:1.2; }}
    h2 {{ margin-top:30px; font-size:1.25rem; }}
    a {{ color:#7c3aed; }}
    code {{ background:#f3e8ff; padding:2px 6px; border-radius:6px; font-size:.9em; }}
    pre {{ background:#0f172a; color:#e2e8f0; padding:14px; border-radius:10px; overflow:auto; font-size:.82rem; }}
    .cta {{ background:#fff; border:1px solid #e9d5ff; border-radius:14px; padding:20px; margin:26px 0; }}
    .btn {{ background:#7c3aed; color:#fff; text-decoration:none; padding:11px 18px; border-radius:10px; font-weight:600; display:inline-block; }}
    nav.crumb {{ font-size:.85rem; color:#64748b; margin-bottom:16px; }}
    .related {{ margin-top:44px; border-top:1px solid #e9d5ff; padding-top:20px; }}
    footer {{ color:#64748b; font-size:.85rem; margin-top:40px; }}
  </style>
</head>
<body>
  <div class="wrap">
    <nav class="crumb"><a href="/">InvoicePDF</a> · guide</nav>
    <h1>{html.escape(page.title)}</h1>
    <p>{page.intro}</p>

    <div class="cta">
      <strong>Try it now — free, no signup:</strong>
      <p style="margin:10px 0 0"><a class="btn" href="/">Open the live playground →</a>
        &nbsp; <a href="/sample">see a sample PDF</a></p>
    </div>

    {body}

    <div class="related">
      <h2>Related guides</h2>
      {_related(pages, page)}
      <p><a href="/">← Back to InvoicePDF</a></p>
    </div>
    <footer>InvoicePDF — generate invoice/receipt PDFs from JSON. Built by an autonomous enterprise.</footer>
  </div>
</body>
</html>
"""


def pages() -> list[Page]:
    return [
        Page(
            slug="html-to-pdf-api.html",
            title="HTML to PDF API — the simple way (no headless browser)",
            description=(
                "Looking for an HTML-to-PDF or document API? Generate invoice and receipt "
                "PDFs from JSON in one request — no headless Chromium, exact money math, free tier."
            ),
            keywords="html to pdf api, pdf generation api, json to pdf, invoice pdf api",
            intro=(
                "Most 'HTML to PDF' APIs spin up headless Chromium — heavy, slow, and painful to "
                "host. For structured documents like invoices and receipts you don't need a browser "
                "at all. InvoicePDF takes <strong>JSON</strong> and returns a clean PDF in one call."
            ),
            sections=[
                (
                    "One request, a PDF back",
                    "<pre>curl -X POST " + SITE_URL + "/invoice \\\n"
                    "  -H 'Content-Type: application/json' \\\n"
                    "  -d '{\"number\":\"INV-1\",\"currency\":\"USD\",\"seller_name\":\"Me\","
                    "\"buyer_name\":\"You\",\"items\":[{\"description\":\"Work\",\"quantity\":1,"
                    "\"unit_price\":100}]}' \\\n  --output invoice.pdf</pre>",
                ),
                (
                    "Why no headless browser?",
                    "<p>Chromium rendering is great for arbitrary web pages, but it's overkill for a "
                    "document with a known structure. Skipping it means <strong>faster responses, no "
                    "cold starts, and free hosting</strong> (pure Python, no system libraries).</p>",
                ),
            ],
        ),
        Page(
            slug="invoice-api.html",
            title="Invoice API — generate invoice PDFs programmatically",
            description=(
                "A simple invoice API: POST JSON with line items, tax and totals, get a professional "
                "invoice PDF. Exact money math, multi-currency, free tier, no signup to try."
            ),
            keywords="invoice api, invoice pdf api, generate invoice pdf, billing api",
            intro=(
                "Need to generate invoices from your app or billing system? InvoicePDF is a focused "
                "<strong>invoice API</strong>: send line items, tax rate and party details as JSON, "
                "get back a clean, professional PDF."
            ),
            sections=[
                (
                    "Exact money — no floating-point drift",
                    "<p>Amounts are handled as integer minor units (cents), so "
                    "<code>$27.00 + 10% tax</code> is exactly <code>$29.70</code>, never "
                    "<code>$29.700000001</code>. Multi-currency, including zero-decimal (JPY).</p>",
                ),
                (
                    "What you send",
                    "<p><code>number</code>, <code>currency</code>, <code>seller_name</code>, "
                    "<code>buyer_name</code>, <code>items[]</code> (description, quantity, "
                    "unit_price), optional <code>tax_rate_percent</code>, <code>notes</code>, "
                    "<code>due_date</code>. That's it.</p>",
                ),
            ],
        ),
        Page(
            slug="generate-receipt-pdf.html",
            title="Generate a receipt PDF from JSON",
            description=(
                "Turn a JSON payload into a clean receipt PDF in one API call. Free tier, exact "
                "totals, multi-currency, no headless browser required."
            ),
            keywords="generate receipt pdf, receipt api, receipt pdf generator, json to pdf",
            intro=(
                "Receipts are just invoices by another name — a few line items, a total, some party "
                "details. InvoicePDF generates a clean receipt PDF from JSON with the same one-call "
                "API, so you can email or store it instantly."
            ),
            sections=[
                (
                    "Same API, receipt output",
                    "<p>Set your line items and total; the generated PDF works equally well as a "
                    "receipt. Free to try at the <a href='/'>live playground</a>.</p>",
                ),
                (
                    "Store nothing, return bytes",
                    "<p>The API is stateless — it returns the PDF bytes directly, so there's no "
                    "storage to manage and nothing to clean up.</p>",
                ),
            ],
        ),
    ]


def build(out_dir: Path | None = None) -> list[Path]:
    out = out_dir or _WEB_DIR
    out.mkdir(parents=True, exist_ok=True)
    all_pages = pages()
    written: list[Path] = []
    for page in all_pages:
        p = out / page.slug
        p.write_text(_render(page, all_pages), encoding="utf-8")
        written.append(p)

    urls = [f"{SITE_URL}/"] + [f"{SITE_URL}/{p.slug}" for p in all_pages]
    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{u}</loc></url>\n" for u in urls)
        + "</urlset>\n"
    )
    sm = out / "sitemap.xml"
    sm.write_text(sitemap, encoding="utf-8")
    written.append(sm)

    robots = out / "robots.txt"
    robots.write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8")
    written.append(robots)
    return written


if __name__ == "__main__":  # pragma: no cover
    for p in build():
        print(f"wrote {p.relative_to(_WEB_DIR.parent)}")


__all__ = ["SITE_URL", "Page", "build", "pages"]
