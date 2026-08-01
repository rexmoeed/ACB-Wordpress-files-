#!/usr/bin/env python3
import base64
import json
import urllib.request

LIVE = "https://americacustomboxes.com"
auth = base64.b64encode(b"admin:XFxg 7dCD 7FE9 7K3z W6mN 5FIh").decode()
req = urllib.request.Request(
    f"{LIVE}/wp-json/wc/v3/products/categories?per_page=100",
    headers={"Authorization": "Basic " + auth},
)
cats = json.loads(urllib.request.urlopen(req, timeout=60).read())
by_id = {c["id"]: c for c in cats}
by_industry_id = next((c["id"] for c in cats if c["slug"] == "by-industry"), None)

print("=== BY INDUSTRY (parent) ===")
parent = by_id.get(by_industry_id, {})
d = parent.get("description") or ""
print(f"by-industry | products={parent.get('count',0)} | {'styled' if 'acb-archive-v2' in d else 'NO content'}")

print("\n=== BY INDUSTRY sub-categories ===")
subs = [c for c in cats if c.get("parent") == by_industry_id]
subs.sort(key=lambda x: x["slug"])
has, no = [], []
for c in subs:
    desc = c.get("description") or ""
    if "<!--acb-archive-v2-->" in desc:
        st = "HAS styled content"
        has.append(c)
    elif desc.strip():
        st = "plain text only"
        no.append(c)
    else:
        st = "NO content"
        no.append(c)
    print(f"{c['slug']:20} | {c['name'][:30]:30} | products={c['count']:3} | {st}")

print(f"\nSummary: {len(subs)} sub-categories, {len(has)} with styled content, {len(no)} without")
