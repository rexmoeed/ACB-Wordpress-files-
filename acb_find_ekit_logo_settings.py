#!/usr/bin/env python3
import base64, json, re, urllib.request
LIVE = "https://americacustomboxes.com"
auth = {"Authorization": "Basic "+base64.b64encode(b"admin:XFxg 7dCD 7FE9 7K3z W6mN 5FIh").decode()}
post = json.loads(urllib.request.urlopen(urllib.request.Request(LIVE+"/wp-json/wp/v2/elementor_library/106?context=edit",headers=auth),timeout=60).read())
meta = post.get("meta") or {}
if isinstance(meta, list):
    meta = {x["key"]: x.get("value") for x in meta}
raw = meta.get("_elementor_data","")
s = raw if isinstance(raw,str) else json.dumps(raw)
# find nav menu / logo related
for pat in ["nav_logo", "ekit_nav", "elementskit", "Fixly", "Acb-logo", "http://Acb"]:
    print(pat, s.count(pat))
for m in re.finditer(r'"ekit[^"]*logo[^"]*"[^}]{0,800}', s, re.I):
    print("---")
    print(m.group(0)[:800])
