#!/usr/bin/env python3
import re
import urllib.request
from pathlib import Path

html = urllib.request.urlopen(
    urllib.request.Request(
        "https://americacustomboxes.com/",
        headers={"User-Agent": "Mozilla/5.0 iPhone", "Cache-Control": "no-cache"},
    ),
    timeout=60,
).read().decode("utf-8", "replace")

# Header block
m = re.search(
    r'<header[^>]*elementor-106[\s\S]*?</header>',
    html,
    re.I,
)
Path(r"e:\America Custom Boxes\acb_header_mobile_extract.html").write_text(
    m.group(0) if m else "NO HEADER", encoding="utf-8"
)
print("header len", len(m.group(0) if m else ""))

# key element ids from earlier knowledge
for eid in ["11fe0bb7", "11e4942c", "71b40442", "117f122f", "18bf67d5", "5544ec35", "1958a58", "178f3901"]:
    print(eid, html.count(f"elementor-element-{eid}"))
