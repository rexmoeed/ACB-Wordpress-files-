#!/usr/bin/env python3
import base64, json, re, urllib.request

LIVE = "https://americacustomboxes.com"
auth = {"Authorization": "Basic " + base64.b64encode(b"admin:XFxg 7dCD 7FE9 7K3z W6mN 5FIh").decode()}

CORRECT = "https://americacustomboxes.com/wp-content/uploads/2026/07/Acb-logo-landscape.webp"

html = urllib.request.urlopen(
    urllib.request.Request(LIVE + "/", headers={"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"}),
    timeout=60,
).read().decode("utf-8", "replace")

print("=== HTML issues ===")
print("broken http://Acb", "http://Acb-logo" in html)
print("Fixly count", html.count("Fixly"))
m = re.search(r'elementskit-nav-logo"[^>]*>.*?<img[^>]+>', html, re.S)
print("nav logo img:", (m.group(0)[:200] if m else "not found"))

post = json.loads(
    urllib.request.urlopen(
        urllib.request.Request(LIVE + "/wp-json/wp/v2/elementor_library/106?context=edit", headers=auth),
        timeout=60,
    ).read()
)
meta = post.get("meta") or {}
if isinstance(meta, list):
    meta = {x["key"]: x.get("value") for x in meta}
raw = meta.get("_elementor_data", "")
s = raw if isinstance(raw, str) else json.dumps(raw)
print("\n=== elementor data ===")
print("len", len(s))
for bad in ["http://Acb-logo", "Fixly", "Acb-logo-landscape.webp"]:
    print(bad, s.count(bad))
