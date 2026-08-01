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

DOC_SLUGS = {
    "tuck-boxes", "bakery-boxes", "candle-boxes", "mailer-boxes", "popcorn-boxes",
    "event-boxes", "pet-boxes", "cosmetics", "food", "product-boxes", "pod-boxes",
    "pharmaceutical-boxes",
}


def content_status(desc: str) -> str:
    if "<!--acb-archive-v2-->" in (desc or ""):
        return "yes"
    if (desc or "").strip():
        return "partial"
    return "no"


def print_tree(parent_slug: str, title: str) -> None:
    pid = next(c["id"] for c in cats if c["slug"] == parent_slug)
    subs = sorted([c for c in cats if c.get("parent") == pid], key=lambda x: x["name"].lower())
    print(f"\n## {title}\n")
    print("| # | Category | Slug | Products | Archive content | In 4 category docs |")
    print("|---|----------|------|----------|-----------------|-------------------|")
    for i, c in enumerate(subs, 1):
        st = content_status(c.get("description") or "")
        content = "Yes" if st == "yes" else ("Plain" if st == "partial" else "No")
        in_doc = "Yes" if c["slug"] in DOC_SLUGS else "No"
        name = c["name"].replace("&amp;", "&")
        print(f"| {i} | {name} | `{c['slug']}` | {c['count']} | {content} | {in_doc} |")
    yes = sum(1 for c in subs if content_status(c.get("description") or "") == "yes")
    print(f"\n**Total sub-categories:** {len(subs)} · **With styled content:** {yes} · **Without:** {len(subs) - yes}")


print_tree("hot-products", "Hot Products")
print_tree("by-industry", "By Industry")
