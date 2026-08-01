#!/usr/bin/env python3
import base64
import json
import urllib.request

LIVE = "https://americacustomboxes.com"
auth = {"Authorization": "Basic " + base64.b64encode(b"admin:XFxg 7dCD 7FE9 7K3z W6mN 5FIh").decode()}


def get_snippets():
    req = urllib.request.Request(f"{LIVE}/wp-json/code-snippets/v1/snippets?per_page=100", headers=auth)
    return json.loads(urllib.request.urlopen(req, timeout=60).read())


def get_snippet(sid):
    req = urllib.request.Request(f"{LIVE}/wp-json/code-snippets/v1/snippets/{sid}", headers=auth)
    return json.loads(urllib.request.urlopen(req, timeout=60).read())


def main():
    for s in sorted(get_snippets(), key=lambda x: x["id"]):
        act = "ON" if s.get("active") else "off"
        print(f"{s['id']:3} {act:3} pri={s.get('priority', '?'):>3} {s.get('name')}")
    for sid in (14, 15, 9, 19):
        code = get_snippet(sid).get("code") or ""
        print(f"\n--- snippet {sid} guards ---")
        for g in ("is_front_page", "is_product", "is_product_taxonomy", "wp_footer", "wp_head", "elementor-page-78"):
            print(f"  {g}: {g in code}")


if __name__ == "__main__":
    main()
