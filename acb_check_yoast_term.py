#!/usr/bin/env python3
import base64, json, urllib.request
LIVE = "https://americacustomboxes.com"
auth = {"Authorization": "Basic " + base64.b64encode(b"admin:XFxg 7dCD 7FE9 7K3z W6mN 5FIh").decode()}
req = urllib.request.Request(f"{LIVE}/wp-json/wp/v2/product_cat/39?context=edit", headers=auth)
d = json.loads(urllib.request.urlopen(req, timeout=60).read())
meta = d.get("meta") or {}
if isinstance(meta, list):
    meta = {m["key"]: m.get("value") for m in meta if isinstance(m, dict)}
for k in sorted(meta):
    if "wpseo" in k.lower() or "yoast" in k.lower():
        print(k, "=>", str(meta[k])[:100])
req2 = urllib.request.Request(f"{LIVE}/wp-json/code-snippets/v1/snippets/16", headers=auth)
code = json.loads(urllib.request.urlopen(req2).read()).get("code", "")
for slug in ["cosmetics", "food", "product-boxes", "pod-boxes", "pharmaceutical-boxes"]:
    print(slug, "in snippet16:", f"'{slug}'" in code)
