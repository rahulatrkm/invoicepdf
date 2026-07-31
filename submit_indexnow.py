"""Submit InvoicePDF URLs to search engines via IndexNow — no account required.

IndexNow (https://www.indexnow.org/) is a sanctioned protocol supported by Bing
and Yandex (and read by others): host a key file at the site root, then POST the
list of URLs you want crawled. This is the one legitimate way to actively ask
search engines to index a brand-new site without owning a Search Console
property. Pure standard library.

    python submit_indexnow.py
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

HOST = "invoicepdf-hqz7.onrender.com"
KEY = "928163aed2542d1be9ba9f30cd94d1dc"
KEY_LOCATION = f"https://{HOST}/{KEY}.txt"

URLS = [
    f"https://{HOST}/",
    f"https://{HOST}/invoice-pdf-api-json.html",
    f"https://{HOST}/generate-invoice-pdf-python.html",
    f"https://{HOST}/invoice-pdf-without-headless-browser.html",
    f"https://{HOST}/html-to-pdf-api.html",
    f"https://{HOST}/generate-receipt-pdf.html",
    f"https://{HOST}/sitemap.xml",
]

ENDPOINTS = [
    "https://api.indexnow.org/indexnow",
    "https://www.bing.com/indexnow",
]


def submit(endpoint: str) -> int:
    payload = json.dumps(
        {"host": HOST, "key": KEY, "keyLocation": KEY_LOCATION, "urlList": URLS}
    ).encode()
    req = urllib.request.Request(
        endpoint,
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print(f"{endpoint} -> {r.status} {r.reason}")
            return 0
    except urllib.error.HTTPError as exc:
        # 200/202 are success; IndexNow returns 202 "accepted" most often.
        print(f"{endpoint} -> {exc.code} {exc.reason}: {exc.read().decode()[:200]}")
        return 0 if exc.code in (200, 202) else 1


def main() -> int:
    rc = 0
    for ep in ENDPOINTS:
        rc |= submit(ep)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
