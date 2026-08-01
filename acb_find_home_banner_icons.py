#!/usr/bin/env python3
import re
import urllib.request

html = urllib.request.urlopen(
    urllib.request.Request(
        "https://americacustomboxes.com/",
        headers={"User-Agent": "Mozilla/5.0 iPhone", "Cache-Control": "no-cache"},
    ),
    timeout=60,
).read().decode("utf-8", "replace")

# Find banner + trust/support icons area
needles = [
    "Best Customer Support",
    "Quick Turnaround",
    "Free Box Color",
    "Free Design Support",
    "Free Flat",
    "acb-banner",
    "ELEVATE YOUR",
]
for n in needles:
    print(n, "=>", html.find(n))

idx = html.find("Best Customer Support")
print("\n--- context ---")
print(html[max(0, idx - 1200) : idx + 800])
