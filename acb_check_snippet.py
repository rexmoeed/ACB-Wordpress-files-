#!/usr/bin/env python3
import base64
import json
import urllib.request

auth = base64.b64encode(b"admin:XFxg 7dCD 7FE9 7K3z W6mN 5FIh").decode()
headers = {"Authorization": "Basic " + auth}


def get(path):
    req = urllib.request.Request("https://americacustomboxes.com" + path, headers=headers)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


for ctx in ("view", "edit"):
    data = get(f"/wp-json/wp/v2/elementor_snippet/2054?context={ctx}")
    code = data.get("meta", {}).get("_elementor_code", "")
    print(f"context={ctx} code_len={len(code)} modified={data.get('modified')}")
    if code:
        print(code[:300].replace("\n", " "))
        print("...")
        if "grid-template-areas" in code:
            print("CONTAINS GRID")
        if "flex-direction:column" in code:
            print("CONTAINS OLD FLEX")

print("\n=== ALL SNIPPETS ===")
snippets = get("/wp-json/wp/v2/elementor_snippet?per_page=100&context=edit")
for s in snippets:
    code = s.get("meta", {}).get("_elementor_code", "") or ""
    print(
        s["id"],
        s.get("title", {}).get("rendered", ""),
        "len=" + str(len(code)),
        s.get("meta", {}).get("_elementor_location", ""),
    )
