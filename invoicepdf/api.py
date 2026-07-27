"""InvoicePDF HTTP API — stdlib server + a WSGI app for free deployment.

Endpoints:
* ``GET  /``          → landing page
* ``GET  /healthz``   → ``{"status":"ok"}``
* ``GET  /sample``    → a sample invoice PDF (so visitors see output instantly)
* ``POST /invoice``   → JSON invoice in, PDF out (``application/pdf``)

Only dependency is ``fpdf2``. The WSGI ``app`` runs on Azure App Service / any
gunicorn host; the stdlib ``serve()`` runs locally.
"""

from __future__ import annotations

import json
import time
from collections import defaultdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from invoicepdf.core import InvoiceError, invoice_from_json

_WEB_DIR = Path(__file__).resolve().parent.parent / "web"

_RATE_LIMIT = 20
_RATE_WINDOW_S = 60.0
_hits: dict[str, list[float]] = defaultdict(list)

_SAMPLE = {
    "number": "INV-2026-001",
    "currency": "USD",
    "date": "2026-07-27",
    "due_date": "2026-08-10",
    "seller_name": "Your Company LLC",
    "seller_details": "123 Main St\nsupport@yourco.com",
    "buyer_name": "Acme Corp",
    "buyer_details": "500 Market St",
    "items": [
        {"description": "Consulting (hours)", "quantity": 8, "unit_price": 120},
        {"description": "Software license", "quantity": 1, "unit_price": 299},
    ],
    "tax_rate_percent": 10,
    "notes": "Thank you for your business!",
}


def _rate_ok(ip: str) -> bool:
    now = time.monotonic()
    window = _hits[ip]
    window[:] = [t for t in window if now - t < _RATE_WINDOW_S]
    if len(window) >= _RATE_LIMIT:
        return False
    window.append(now)
    return True


# --- stdlib server -------------------------------------------------------
class Handler(BaseHTTPRequestHandler):
    server_version = "InvoicePDF/1.0"

    def _json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _pdf(self, data: bytes) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "application/pdf")
        self.send_header("Content-Disposition", "inline; filename=invoice.pdf")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _file(self, name: str, ctype: str) -> None:
        path = _WEB_DIR / name
        if not path.exists():
            self._json({"error": "not found"}, 404)
            return
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        route = urlparse(self.path).path
        if route in ("/", "/index.html"):
            self._file("index.html", "text/html; charset=utf-8")
        elif route == "/healthz":
            self._json({"status": "ok"})
        elif route == "/sample":
            self._pdf(invoice_from_json(_SAMPLE))
        else:
            self._json({"error": "not found"}, 404)

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/invoice":
            self._json({"error": "not found"}, 404)
            return
        if not _rate_ok(self.client_address[0]):
            self._json({"error": "rate limit exceeded — grab an API key"}, 429)
            return
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(raw.decode("utf-8"))
            pdf = invoice_from_json(data)
        except (json.JSONDecodeError, InvoiceError, KeyError, TypeError) as exc:
            self._json({"error": str(exc)}, 400)
            return
        self._pdf(pdf)

    def log_message(self, *args: object) -> None:
        return


def serve(host: str = "0.0.0.0", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"InvoicePDF API on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


# --- WSGI app (for gunicorn / Azure App Service) -------------------------
def app(environ, start_response):
    """Minimal WSGI mirror of the routes above."""
    method = environ.get("REQUEST_METHOD", "GET")
    path = environ.get("PATH_INFO", "/")

    def respond(status, ctype, body, extra=None):
        headers = [("Content-Type", ctype), ("Content-Length", str(len(body))),
                   ("Access-Control-Allow-Origin", "*")]
        if extra:
            headers.extend(extra)
        start_response(status, headers)
        return [body]

    if method == "GET" and path in ("/", "/index.html"):
        p = _WEB_DIR / "index.html"
        if p.exists():
            return respond("200 OK", "text/html; charset=utf-8", p.read_bytes())
    if method == "GET" and path == "/healthz":
        return respond("200 OK", "application/json", b'{"status": "ok"}')
    if method == "GET" and path == "/sample":
        return respond("200 OK", "application/pdf", invoice_from_json(_SAMPLE),
                       [("Content-Disposition", "inline; filename=sample.pdf")])
    if method == "POST" and path == "/invoice":
        try:
            length = int(environ.get("CONTENT_LENGTH", "0") or "0")
            raw = environ["wsgi.input"].read(length) if length else b"{}"
            data = json.loads(raw.decode("utf-8"))
            pdf = invoice_from_json(data)
        except (json.JSONDecodeError, InvoiceError, KeyError, TypeError, ValueError) as exc:
            return respond("400 Bad Request", "application/json",
                           json.dumps({"error": str(exc)}).encode())
        return respond("200 OK", "application/pdf", pdf,
                       [("Content-Disposition", "inline; filename=invoice.pdf")])

    # Static SEO pages, sitemap, robots (generated into web/ at startup).
    if method == "GET" and path == "/sitemap.xml":
        p = _WEB_DIR / "sitemap.xml"
        if p.exists():
            return respond("200 OK", "application/xml", p.read_bytes())
    if method == "GET" and path == "/robots.txt":
        p = _WEB_DIR / "robots.txt"
        if p.exists():
            return respond("200 OK", "text/plain; charset=utf-8", p.read_bytes())
    if method == "GET" and path.endswith(".html") and "/" not in path[1:]:
        p = _WEB_DIR / path.lstrip("/")
        if p.exists():
            return respond("200 OK", "text/html; charset=utf-8", p.read_bytes())

    return respond("404 Not Found", "application/json", b'{"error": "not found"}')


# query-string helper kept for symmetry / future use
def _q(environ) -> dict:
    return parse_qs(environ.get("QUERY_STRING", ""))


if __name__ == "__main__":  # pragma: no cover
    import os

    serve(port=int(os.environ.get("PORT", "8000")))
