#!/usr/bin/env python3
import re
import urllib.request

url = "https://americacustomboxes.com/product-category/hot-products/tuck-boxes/"
html = urllib.request.urlopen(url, timeout=60).read().decode("utf-8", errors="replace")

m = re.search(r"<title>([^<]+)</title>", html)
print("TITLE:", m.group(1) if m else "N/A")
m = re.search(r'name="description"\s+content="([^"]+)"', html)
print("META DESC:", (m.group(1)[:120] + "...") if m else "N/A")

checks = [
    "acb-pc-intro",
    "acb-pc-why-list",
    "acb-pc-styles",
    "acb-pc-style-card",
    "acb-pc-custom-grid",
    "acb-pc-sustain-text",
    "acb-faq-section",
    "acb-archive-mobile-css",
    "Why Choose Custom Tuck",
    "Popular Styles",
    "Customization Options",
    "Sustainable Packaging",
    "Frequently Asked Questions",
]
for c in checks:
    print(f"{c}: {'YES' if c in html else 'NO'}")
