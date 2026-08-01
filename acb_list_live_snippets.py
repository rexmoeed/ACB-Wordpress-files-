#!/usr/bin/env python3
import base64
import json
import urllib.request

LIVE = "https://americacustomboxes.com"
auth = {"Authorization": "Basic " + base64.b64encode(b"admin:XFxg 7dCD 7FE9 7K3z W6mN 5FIh").decode()}
req = urllib.request.Request(f"{LIVE}/wp-json/code-snippets/v1/snippets?per_page=100", headers=auth)
snips = json.loads(urllib.request.urlopen(req, timeout=60).read())
for s in sorted(snips, key=lambda x: x.get("id", 0)):
    if not s.get("active"):
        continue
    code = s.get("code") or ""
    print(f"id={s['id']} pri={s.get('priority')} {s.get('name')[:50]} len={len(code)}")
    if s["id"] == 19:
        print("--- snippet 19 start ---")
        print(code[:600])
        print("--- has wp_footer?", "wp_footer" in code)
