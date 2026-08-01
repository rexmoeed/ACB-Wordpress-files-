#!/usr/bin/env python3
import re, urllib.request
html = urllib.request.urlopen(
    urllib.request.Request(
        "https://americacustomboxes.com/?nocache=logo",
        headers={"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"},
    ),
    timeout=60,
).read().decode("utf-8", "replace")
for m in re.finditer(r"elementskit-nav-logo[^>]*>[\s\S]*?</a>", html):
    print(m.group(0)[:400])
    print("---")
print("all Fixly urls", len(re.findall(r"Fixly", html)))
