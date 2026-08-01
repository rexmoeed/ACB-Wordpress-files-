#!/usr/bin/env python3
import base64, json, urllib.request
LIVE = "https://americacustomboxes.com"
auth = {"Authorization": "Basic "+base64.b64encode(b"admin:XFxg 7dCD 7FE9 7K3z W6mN 5FIh").decode()}
post = json.loads(urllib.request.urlopen(urllib.request.Request(LIVE+"/wp-json/wp/v2/elementor_library/106?context=edit",headers=auth),timeout=60).read())
meta = post.get("meta") or {}
if isinstance(meta, list):
    meta = {x["key"]: x.get("value") for x in meta}
raw = meta.get("_elementor_data","")
s = raw if isinstance(raw,str) else json.dumps(raw)
i = s.find("Fixly")
print("Fixly idx", i)
print(s[max(0,i-200):i+300] if i>=0 else "no fixly")
i2 = s.find("Acb-logo")
print("acb idx", i2)
print(s[max(0,i2-100):i2+200] if i2>=0 else "no acb")
