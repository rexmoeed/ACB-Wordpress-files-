#!/usr/bin/env python3
import re
from pathlib import Path
import urllib.request

html = urllib.request.urlopen(
    urllib.request.Request(
        "https://americacustomboxes.com/?nocache=icons3",
        headers={"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"},
    ),
    timeout=60,
).read().decode("utf-8", "replace")

out = Path(r"e:\America Custom Boxes\acb_home_features_css_extract.txt")
chunks = []

# Find inline style near acb-features (the widget style is usually right before the div)
j = html.find('class="acb-features"')
chunk = html[max(0, j - 2500) : j + 900]
chunks.append("=== BEFORE FEATURES ===\n" + chunk)

# Find banner widget HTML
k = html.find('class="acb-banner-section"')
if k < 0:
    # might be in style only - find HTML with acb-slider-track
    k = html.find("acb-slider-track")
chunks.append("\n\n=== BANNER AREA ===\n" + html[max(0, k - 800) : k + 1800])

out.write_text("\n".join(chunks), encoding="utf-8")
print("wrote", out, "len", out.stat().st_size)
