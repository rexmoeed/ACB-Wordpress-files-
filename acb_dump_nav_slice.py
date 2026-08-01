#!/usr/bin/env python3
import base64, json, urllib.request

LIVE = "https://americacustomboxes.com"
auth = {"Authorization": "Basic " + base64.b64encode(b"admin:XFxg 7dCD 7FE9 7K3z W6mN 5FIh").decode()}
post = json.loads(
    urllib.request.urlopen(
        urllib.request.Request(LIVE + "/wp-json/wp/v2/elementor_library/106?context=edit", headers=auth),
        timeout=60,
    ).read()
)
meta = post.get("meta") or {}
if isinstance(meta, list):
    meta = {x["key"]: x.get("value") for x in meta}
s = meta.get("_elementor_data", "")
if not isinstance(s, str):
    s = json.dumps(s)

print(s[9500:10500])
print("---")
print(s[11300:12300])
