"""Tests for InvoicePDF core — offline, no network."""

from __future__ import annotations

from decimal import Decimal

import pytest

from invoicepdf.core import Invoice, InvoiceError, invoice_from_json, render_pdf

_MIN = {
    "number": "INV-1",
    "currency": "USD",
    "seller_name": "Me LLC",
    "buyer_name": "You Inc",
    "items": [{"description": "Work", "quantity": 1, "unit_price": 100}],
}


def test_generates_valid_pdf() -> None:
    pdf = invoice_from_json(_MIN)
    assert pdf[:5] == b"%PDF-"
    assert len(pdf) > 500


def test_exact_totals_with_tax() -> None:
    inv = Invoice.from_dict(
        {
            **_MIN,
            "currency": "INR",
            "items": [
                {"description": "A", "quantity": 1, "unit_price": 500},
                {"description": "B", "quantity": 2, "unit_price": 750},
                {"description": "C", "quantity": "3.5", "unit_price": 200},
            ],
            "tax_rate_percent": 18,
        }
    )
    # 500 + 1500 + 700 = 2700.00 -> 270000 minor
    assert inv.subtotal_minor == 270000
    assert inv.tax_minor == 48600  # 18%
    assert inv.total_minor == 318600


def test_zero_decimal_currency() -> None:
    inv = Invoice.from_dict(
        {**_MIN, "currency": "JPY", "items": [{"description": "x", "quantity": 1, "unit_price": 1000}]}
    )
    assert inv.subtotal_minor == 1000  # JPY has no minor units


def test_fractional_quantity_rounds_line() -> None:
    inv = Invoice.from_dict(
        {**_MIN, "items": [{"description": "hrs", "quantity": "2.5", "unit_price": "33.33"}]}
    )
    # 2.5 * 3333 minor = 8332.5 -> 8332 (banker's rounding to even? 8332.5 -> 8332)
    assert inv.items[0].amount_minor in (8332, 8333)


def test_missing_number_rejected() -> None:
    with pytest.raises(InvoiceError):
        Invoice.from_dict({**_MIN, "number": ""})


def test_empty_items_rejected() -> None:
    with pytest.raises(InvoiceError):
        invoice_from_json({**_MIN, "items": []})


def test_bad_currency_rejected() -> None:
    # Lowercase is auto-normalized (lenient), but a non-3-letter code is rejected.
    assert Invoice.from_dict({**_MIN, "currency": "usd"}).currency == "USD"
    with pytest.raises(InvoiceError):
        Invoice.from_dict({**_MIN, "currency": "RUPEE"})


def test_item_missing_price_rejected() -> None:
    with pytest.raises(InvoiceError):
        invoice_from_json({**_MIN, "items": [{"description": "no price", "quantity": 1}]})


def test_render_pdf_direct() -> None:
    inv = Invoice.from_dict({**_MIN, "notes": "Pay in 14 days", "tax_rate_percent": 5})
    pdf = render_pdf(inv)
    assert pdf[:5] == b"%PDF-"


def test_negative_tax_rejected() -> None:
    with pytest.raises(InvoiceError):
        Invoice.from_dict({**_MIN, "tax_rate_percent": Decimal(-5)})
