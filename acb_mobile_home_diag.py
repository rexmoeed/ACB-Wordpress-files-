#!/usr/bin/env python3
import re
import urllib.request

LIVE = "https://americacustomboxes.com/"
html = urllib.request.urlopen(
    urllib.request.Request(LIVE, headers={"User-Agent": "Mozilla/5.0 (iPhone)", "Cache-Control": "no-cache"}),
    timeout=60,
).read().decode("utf-8", "replace")

print("viewport", "viewport" in html.lower())
for link in re.findall(r'href="([^"]+\.css[^"]*)"', html):
    if "post-106" in link or "post-78" in link or "header" in link:
        print("css", link.split("/")[-1][:80])

# inline styles with 100vw or min-width
for pat in [r"100vw", r"overflow-x", r"min-width:\s*[0-9]{4}px"]:
    print(pat, len(re.findall(pat, html, re.I)))

# acb snippets style ids
for sid in ["acb-mobile-menu-logo", "acb-single-product", "acb-archive", "acb-hamburger"]:
    print(sid, sid in html)
