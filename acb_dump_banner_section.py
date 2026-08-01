#!/usr/bin/env python3
import re
import urllib.request

html = urllib.request.urlopen(
    urllib.request.Request(
        "https://americacustomboxes.com/?nocache=icons1",
        headers={"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"},
    ),
    timeout=60,
).read().decode("utf-8", "replace")

# banner block
i = html.find("acb-banner-section")
print("banner idx", i)
print(html[i : i + 2500])
print("\n====\n")

# search icon-related strings
for pat in [
    r"Customer Support",
    r"Turnaround",
    r"Color printing",
    r"Design Support",
    r"3d Line",
    r"3D",
    r"Free Flat",
    r"icon-list",
    r"qi-icon",
]:
    m = re.search(pat, html, re.I)
    print(pat, "->", m.start() if m else None)

# Find Free Design Support surrounding
j = html.find("Free Design Support")
print("\nFree Design Support context:\n", html[j - 800 : j + 1200])
