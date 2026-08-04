"""What the deployed API refuses.

Two things were true of the WSGI app that actually runs in production, and of
neither of the stdlib server's equivalents:

* it had no rate limit at all — the twenty-per-minute limit lived only in the
  development server's request handler, so the deployed service was unbounded;
* it passed Content-Length straight to read(), so `Content-Length: 1073741824`
  asked the process for a gigabyte before looking at a single byte.

Both are exercised here against the real WSGI callable rather than the handler,
because the difference between the two is exactly where the hole was.
"""

from __future__ import annotations

import io
import json

import pytest

from invoicepdf import api

GOOD = {
    "number": "INV-1",
    "currency": "USD",
    "seller_name": "Seller",
    "buyer_name": "Buyer",
    "items": [{"description": "Work", "quantity": 1, "unit_price": 100}],
}


def call(body: bytes, *, declared: str | None = None, ip: str = "203.0.113.5",
         forwarded: str | None = None):
    env = {
        "REQUEST_METHOD": "POST",
        "PATH_INFO": "/invoice",
        "CONTENT_LENGTH": str(len(body)) if declared is None else declared,
        "wsgi.input": io.BytesIO(body),
        "REMOTE_ADDR": ip,
    }
    if forwarded is not None:
        env["HTTP_X_FORWARDED_FOR"] = forwarded
    captured = {}

    def start(status, headers):
        captured["status"] = int(status.split()[0])

    payload = b"".join(api.app(env, start))
    return captured["status"], payload


@pytest.fixture(autouse=True)
def _clear_limits():
    api._hits.clear()
    yield
    api._hits.clear()


def test_a_normal_invoice_still_works():
    status, body = call(json.dumps(GOOD).encode())
    assert status == 200
    assert body.startswith(b"%PDF"), body[:40]


def test_an_enormous_declared_length_is_refused_without_reading_it():
    # The body is tiny; the header lies. Nothing should try to allocate a GB.
    status, body = call(b"{}", declared=str(1024 ** 3))
    assert status == 413, body
    assert b"too large" in body


def test_a_genuinely_large_body_is_refused():
    huge = json.dumps({**GOOD, "notes": "x" * (300 * 1024)}).encode()
    status, _ = call(huge)
    assert status == 413


def test_a_body_at_the_limit_is_still_read():
    padding = "y" * (api._MAX_BODY_BYTES - len(json.dumps(GOOD).encode()) - 20)
    ok = json.dumps({**GOOD, "notes": padding}).encode()
    assert len(ok) <= api._MAX_BODY_BYTES
    status, _ = call(ok)
    assert status == 200


def test_a_nonsense_content_length_is_refused_not_crashed():
    for bad in ("banana", "-1", "9" * 40):
        status, _ = call(b"{}", declared=bad)
        assert status == 413, bad


def test_the_deployed_path_is_rate_limited():
    # This is the whole point: the limit existed only in the dev server.
    seen = [call(json.dumps(GOOD).encode())[0] for _ in range(api._RATE_LIMIT + 5)]
    assert 429 in seen, "the production path accepted unlimited requests"
    assert seen[0] == 200, "it must not start by refusing everyone"


def test_the_limit_cannot_be_shaken_off_with_a_header():
    # The proxy appends to X-Forwarded-For, so its first entry is caller-chosen.
    seen = [
        call(json.dumps(GOOD).encode(), ip="10.0.0.1",
             forwarded=f"1.2.3.{i}, 203.0.113.9")[0]
        for i in range(api._RATE_LIMIT + 5)
    ]
    assert 429 in seen, "a caller could mint a fresh bucket per request"


def test_separate_callers_are_not_lumped_together():
    seen = [
        call(json.dumps(GOOD).encode(), ip="10.0.0.1",
             forwarded=f"198.51.100.{i}")[0]
        for i in range(api._RATE_LIMIT + 5)
    ]
    assert 429 not in seen, "distinct callers shared one bucket"
