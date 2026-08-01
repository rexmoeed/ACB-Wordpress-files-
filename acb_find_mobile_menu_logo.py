#!/usr/bin/env python3
import base64
import json
import re
import urllib.request

LIVE = "https://americacustomboxes.com"
auth = {
    "Authorization": "Basic "
    + base64.b64encode(b"admin:XFxg 7dCD 7FE9 7K3z W6mN 5FIh").decode()
}

# Find Fixly + main site logos in HTML
html = urllib.request.urlopen(
    urllib.request.Request(LIVE + "/", headers={"User-Agent": "Mozilla/5.0"}),
    timeout=60,
).read().decode("utf-8", "replace")
print("fixly in html", "Fixly" in html or "fixly" in html.lower())
for pat in [r"elementskit-nav-logo[^>]*>.*?src=\"([^\"]+)\"", r"Fixly[^\"']*"]:
    m = re.search(pat, html, re.I | re.S)
    if m:
        print("match", m.group(0)[:150] if m.lastindex is None else m.group(1))

req = urllib.request.Request(
    LIVE + "/wp-json/wp/v2/elementor_library/106?context=edit",
    headers=auth,
)
try:
    post = json.loads(urllib.request.urlopen(req, timeout=60).read())
    meta = post.get("meta") or {}
    if isinstance(meta, list):
        meta = {x["key"]: x["value"] for x in meta}
    raw = meta.get("_elementor_data") or ""
    if isinstance(raw, list):
        raw = raw[0] if raw else ""
    print("_elementor_data len", len(str(raw)))
    if "Fixly" in str(raw):
        print("Fixly found in elementor data")
        for m in re.finditer(r"Fixly[^\"\\]*", str(raw)):
            print(" ", m.group(0)[:80])
except urllib.error.HTTPError as e:
    print("REST elementor_library", e.code, e.read()[:200])
