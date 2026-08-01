#!/usr/bin/env python3
import re
import urllib.request

html = urllib.request.urlopen(
    urllib.request.Request("https://americacustomboxes.com/", headers={"User-Agent": "ACB/1.0", "Cache-Control": "no-cache"}),
    timeout=60,
).read().decode("utf-8", "replace")

# header / first 25k
head = html[:25000]
print("=== FIRST 800 chars of body ===")
bi = html.lower().find("<body")
print(html[bi : bi + 800])

# elementor header
for pat in ["elementor-location-header", "site-header", "masthead", "hfe-header", "data-elementor-type=\"header\""]:
    print(pat, html.count(pat))

# CSS links count
css = re.findall(r'<link[^>]+stylesheet[^>]+>', html, re.I)
print("stylesheet links", len(css))
broken_css = [c for c in css if "href=\"\"" in c or "href=''" in c]
print("empty href css", len(broken_css))

# visible script text in body (leaked)
if "window.acbQuoteFormNonce" in html[:50000]:
    print("WARNING: nonce script appears early in HTML (before footer?)")
    print(html.find("window.acbQuoteFormNonce"))

# check for unescaped script breaking layout in content
for m in re.finditer(r"<script[^>]*>window\.acbQuoteFormNonce", html):
    print("nonce script at index", m.start(), "of", len(html))

# snippet errors in html
for err in ["acb-quote-form-globals", "Code Snippets", "Parse error"]:
    print(err, html.count(err))
