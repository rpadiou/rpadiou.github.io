#!/usr/bin/env python3
"""Regenerate sitemap.xml from the public HTML pages; lastmod = date of the last commit touching each page."""
from sitelib import ROOT, page_url, public_pages, last_commit_date

pages = public_pages()
# Home first, then alphabetical by URL
entries = sorted(((page_url(p), last_commit_date(p)) for p in pages), key=lambda e: (e[0] != "https://rpadiou.github.io/", e[0]))
xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for url, date in entries:
    xml.append(f"  <url>\n    <loc>{url}</loc>\n    <lastmod>{date}</lastmod>\n  </url>")
xml.append("</urlset>\n")
(ROOT / "sitemap.xml").write_text("\n".join(xml), encoding="utf-8")
print(f"sitemap.xml: {len(entries)} pages")
