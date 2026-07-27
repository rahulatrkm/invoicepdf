"""InvoicePDF — a real, low-dependency invoice/receipt PDF generation API.

POST structured JSON, get back a clean professional invoice PDF. Pure Python
(only ``fpdf2``), so it deploys free anywhere — no headless browser, no system
libraries. Targets the highest-willingness-to-pay slice of doc generation:
businesses that pay to automate invoices and receipts.
"""

from __future__ import annotations

from invoicepdf.core import Invoice, InvoiceError, invoice_from_json, render_pdf

__version__ = "1.0.0"

__all__ = ["Invoice", "InvoiceError", "__version__", "invoice_from_json", "render_pdf"]
