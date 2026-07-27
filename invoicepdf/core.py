"""InvoicePDF core — turn structured JSON into a clean professional invoice PDF.

Pure Python on top of ``fpdf2`` (no headless browser, no system libraries), so it
deploys free anywhere — the same constraint that makes OGCheck cheap to run.

Money is handled as **integer minor units** (paise/cents) throughout, so totals
are exact — no floating-point drift on financial documents. The renderer targets
the highest-willingness-to-pay slice of the doc-generation market: invoices and
receipts that businesses actually pay to automate.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal

from fpdf import FPDF

# Currencies with 0 minor-unit decimals (rendering only).
_ZERO_DECIMAL = {"JPY", "KRW", "VND", "CLP", "ISK"}


class InvoiceError(ValueError):
    """Raised when invoice input is invalid."""


def _minor_exponent(currency: str) -> int:
    return 0 if currency in _ZERO_DECIMAL else 2


def _to_minor(amount: str | float, currency: str) -> int:
    exp = _minor_exponent(currency)
    quantum = Decimal(1).scaleb(-exp)
    scaled = Decimal(str(amount)).quantize(quantum, rounding=ROUND_HALF_EVEN) * (10**exp)
    return int(scaled)


def _fmt_money(minor: int, currency: str) -> str:
    exp = _minor_exponent(currency)
    major = Decimal(minor) / (10**exp)
    return f"{major:,.{exp}f} {currency}"


@dataclass
class LineItem:
    description: str
    quantity: Decimal
    unit_price_minor: int  # in the invoice currency's minor units

    @property
    def amount_minor(self) -> int:
        # quantity may be fractional (e.g. hours); round the line total to minor units.
        total = (Decimal(self.unit_price_minor) * self.quantity).quantize(
            Decimal(1), rounding=ROUND_HALF_EVEN
        )
        return int(total)


@dataclass
class Invoice:
    """A validated invoice ready to render."""

    number: str
    currency: str
    seller_name: str
    buyer_name: str
    items: list[LineItem]
    seller_details: str = ""
    buyer_details: str = ""
    date: str = ""
    due_date: str = ""
    tax_rate_percent: Decimal = Decimal(0)
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.number.strip():
            raise InvoiceError("invoice 'number' is required")
        if not (len(self.currency) == 3 and self.currency.isupper()):
            raise InvoiceError("'currency' must be a 3-letter ISO 4217 code")
        if not self.seller_name.strip() or not self.buyer_name.strip():
            raise InvoiceError("'seller_name' and 'buyer_name' are required")
        if not self.items:
            raise InvoiceError("at least one line item is required")
        if self.tax_rate_percent < 0:
            raise InvoiceError("tax_rate_percent must not be negative")

    # --- Totals (exact) ---------------------------------------------------
    @property
    def subtotal_minor(self) -> int:
        return sum(item.amount_minor for item in self.items)

    @property
    def tax_minor(self) -> int:
        tax = (Decimal(self.subtotal_minor) * self.tax_rate_percent / 100).quantize(
            Decimal(1), rounding=ROUND_HALF_EVEN
        )
        return int(tax)

    @property
    def total_minor(self) -> int:
        return self.subtotal_minor + self.tax_minor

    # --- Construction from JSON ------------------------------------------
    @classmethod
    def from_dict(cls, data: dict) -> Invoice:
        if not isinstance(data, dict):
            raise InvoiceError("invoice body must be a JSON object")
        currency = str(data.get("currency", "USD")).upper()
        raw_items = data.get("items")
        if not isinstance(raw_items, list) or not raw_items:
            raise InvoiceError("'items' must be a non-empty list")
        items: list[LineItem] = []
        for i, it in enumerate(raw_items):
            try:
                items.append(
                    LineItem(
                        description=str(it["description"]),
                        quantity=Decimal(str(it.get("quantity", 1))),
                        unit_price_minor=_to_minor(it["unit_price"], currency),
                    )
                )
            except (KeyError, TypeError, ArithmeticError) as exc:
                raise InvoiceError(f"item {i} is invalid: {exc}") from exc
        return cls(
            number=str(data.get("number", "")),
            currency=currency,
            seller_name=str(data.get("seller_name", "")),
            buyer_name=str(data.get("buyer_name", "")),
            items=items,
            seller_details=str(data.get("seller_details", "")),
            buyer_details=str(data.get("buyer_details", "")),
            date=str(data.get("date", "")),
            due_date=str(data.get("due_date", "")),
            tax_rate_percent=Decimal(str(data.get("tax_rate_percent", 0))),
            notes=str(data.get("notes", "")),
        )


def render_pdf(invoice: Invoice) -> bytes:
    """Render the invoice to PDF bytes (A4). Pure Python, no external services."""
    pdf = FPDF(format="A4", unit="mm")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    ink = (17, 24, 39)
    muted = (100, 116, 139)

    # Header
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*ink)
    pdf.cell(0, 12, "INVOICE", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*muted)
    pdf.cell(0, 6, f"#{invoice.number}", ln=True)
    if invoice.date:
        pdf.cell(0, 6, f"Date: {invoice.date}", ln=True)
    if invoice.due_date:
        pdf.cell(0, 6, f"Due: {invoice.due_date}", ln=True)
    pdf.ln(4)

    # Seller / buyer
    pdf.set_text_color(*ink)
    y = pdf.get_y()
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(90, 6, "From", ln=False)
    pdf.cell(0, 6, "Bill to", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(90, 5, f"{invoice.seller_name}\n{invoice.seller_details}".strip(), align="L")
    y2 = pdf.get_y()
    pdf.set_xy(pdf.l_margin + 90, y + 6)
    pdf.multi_cell(0, 5, f"{invoice.buyer_name}\n{invoice.buyer_details}".strip(), align="L")
    pdf.set_y(max(y2, pdf.get_y()) + 4)

    # Items table
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(241, 245, 249)
    pdf.cell(95, 8, "Description", border=0, fill=True)
    pdf.cell(20, 8, "Qty", border=0, fill=True, align="R")
    pdf.cell(30, 8, "Unit", border=0, fill=True, align="R")
    pdf.cell(0, 8, "Amount", border=0, fill=True, align="R", ln=True)
    pdf.set_font("Helvetica", "", 10)
    for item in invoice.items:
        pdf.cell(95, 7, item.description[:60])
        qty = item.quantity.normalize()
        pdf.cell(20, 7, f"{qty}", align="R")
        pdf.cell(30, 7, _fmt_money(item.unit_price_minor, invoice.currency), align="R")
        pdf.cell(0, 7, _fmt_money(item.amount_minor, invoice.currency), align="R", ln=True)

    pdf.ln(2)
    # Totals
    def _total_row(label: str, minor: int, bold: bool = False) -> None:
        pdf.set_font("Helvetica", "B" if bold else "", 11 if bold else 10)
        pdf.cell(145, 7, "", ln=False)
        pdf.cell(0, 7, f"{label}: {_fmt_money(minor, invoice.currency)}", align="R", ln=True)

    _total_row("Subtotal", invoice.subtotal_minor)
    if invoice.tax_rate_percent > 0:
        _total_row(f"Tax ({invoice.tax_rate_percent.normalize()}%)", invoice.tax_minor)
    _total_row("Total", invoice.total_minor, bold=True)

    if invoice.notes:
        pdf.ln(6)
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(*muted)
        pdf.multi_cell(0, 5, invoice.notes)

    out = pdf.output()
    return bytes(out)


def invoice_from_json(data: dict) -> bytes:
    """Validate JSON and return the rendered invoice PDF bytes."""
    return render_pdf(Invoice.from_dict(data))


__all__ = ["Invoice", "InvoiceError", "LineItem", "invoice_from_json", "render_pdf"]
