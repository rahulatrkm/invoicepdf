"""WSGI entrypoint for Azure App Service / gunicorn.

Exposes the InvoicePDF WSGI ``app``. Start command:
    gunicorn --bind=0.0.0.0:8000 wsgi:app
"""

from __future__ import annotations

from invoicepdf.api import app

__all__ = ["app"]
