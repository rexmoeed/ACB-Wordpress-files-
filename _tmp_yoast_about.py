import base64
import importlib.util
import json
import urllib.request

spec = importlib.util.spec_from_file_location("d", r"e:\America Custom Boxes\acb_deploy_about_us.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
auth = base64.b64encode(f"{m.USER}:{m.APP_PASSWORD}".encode()).decode()
h = {"Authorization": f"Basic {auth}"}
r = urllib.request.urlopen(
    urllib.request.Request(
        f"{m.LIVE}/wp-json/wp/v2/pages/{m.ABOUT_PAGE_ID}?context=edit", headers=h
    ),
    timeout=60,
)
page = json.loads(r.read())
meta = page.get("meta") or {}
print("yoast title meta key in response:", "yoast" in str(meta).lower())
for k in sorted(meta.keys()):
    if "yoast" in k.lower() or "wpseo" in k.lower():
        print(k, ":", (meta[k] or "")[:120])
