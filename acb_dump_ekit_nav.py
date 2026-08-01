#!/usr/bin/env python3
import base64, json, re, urllib.request

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

wts = sorted(set(re.findall(r'"widgetType":"([^"]+)"', s)))
print("widgets:", wts)

for needle in ["ekit-nav-menu", "elementskit", "nav_menu_logo", "ekit_nav_menu_logo", "mobile_menu_logo"]:
    i = s.find(needle)
    print(needle, "at", i)

# dump settings containing logo
for m in re.finditer(r'"settings":\{[^{}]*logo[^{}]*\}', s, re.I):
    print("small:", m.group(0)[:500])

# broader: find Fixly or http:// or nav logo url keys
for m in re.finditer(r'"ekit_nav_menu_logo[^"]*"[^}]{0,1200}', s):
    print("--- ekit_nav_menu_logo block ---")
    print(m.group(0)[:1200])

for m in re.finditer(r'"url":"http[^"]*"', s):
    u = m.group(0)
    if "Acb" in u or "Fixly" in u or "americacustomboxes" in u:
        print(u)
