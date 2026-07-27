"""WSGI entrypoint for Azure App Service / gunicorn.

Exposes the InvoicePDF WSGI ``app``. Start command:
    gunicorn --bind=0.0.0.0:8000 wsgi:app
"""

from __future__ import annotations

import contextlib

from invoicepdf.api import app

# Generate SEO pages + sitemap into web/ at startup (idempotent).
with contextlib.suppress(Exception):  # pragma: no cover - deployment convenience
    from invoicepdf.seo import build

    build()

__all__ = ["app"]
