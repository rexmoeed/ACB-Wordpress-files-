#!/usr/bin/env python3
import base64
import json
import urllib.request

auth = base64.b64encode(b"admin:XFxg 7dCD 7FE9 7K3z W6mN 5FIh").decode()
headers = {"Authorization": "Basic " + auth}

req = urllib.request.Request(
    "https://americacustomboxes.com/wp-json/code-snippets/v1/snippets",
    headers=headers,
)
snippets = json.loads(urllib.request.urlopen(req).read().decode())
for s in snippets:
    title = s.get("name") or s.get("title") or ""
    if any(k in title.lower() for k in ("acb", "product", "mobile", "single")):
        print("MATCH", s.get("id"), title, "active", s.get("active"))

print("\nSearching all snippet names:")
for s in snippets:
    print(s.get("id"), s.get("name"), s.get("active"))

# elementor custom code locations - try plugins endpoint
for path in (
    "/wp-json/wp/v2/plugins",
    "/wp-json/wp/v2/elementor_snippet?search=mobile",
    "/wp-json/wp/v2/elementor_snippet?search=acb",
):
    try:
        req = urllib.request.Request(
            "https://americacustomboxes.com" + path,
            headers=headers,
        )
        data = json.loads(urllib.request.urlopen(req).read().decode())
        print("\n", path, "count", len(data) if isinstance(data, list) else type(data))
        if isinstance(data, list):
            for item in data[:20]:
                if isinstance(item, dict):
                    title = item.get("title", {})
                    if isinstance(title, dict):
                        title = title.get("rendered", "")
                    print(" ", item.get("id"), title)
    except Exception as exc:
        print(path, "ERR", exc)
