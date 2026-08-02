"""Tests for the InvoicePDF SEO generator — offline, temp dir."""

from __future__ import annotations

from invoicepdf.seo import build, pages


def test_builds_pages_and_sitemap(tmp_path) -> None:
    written = build(out_dir=tmp_path)
    names = {p.name for p in written}
    for page in pages():
        assert page.slug in names
    assert "sitemap.xml" in names
    assert "robots.txt" in names


def test_pages_have_canonical_and_cta(tmp_path) -> None:
    build(out_dir=tmp_path)
    for page in pages():
        html = (tmp_path / page.slug).read_text(encoding="utf-8")
        assert "rel=\"canonical\"" in html
        assert "/sample" in html  # live CTA
        assert page.title in html


def test_pages_interlinked(tmp_path) -> None:
    build(out_dir=tmp_path)
    all_pages = pages()
    for page in all_pages:
        html = (tmp_path / page.slug).read_text(encoding="utf-8")
        for other in all_pages:
            if other.slug != page.slug:
                assert f'href="/{other.slug}"' in html


def test_sitemap_lists_pages(tmp_path) -> None:
    build(out_dir=tmp_path)
    sitemap = (tmp_path / "sitemap.xml").read_text(encoding="utf-8")
    for page in pages():
        assert page.slug in sitemap
