#!/usr/bin/env python3
"""Full audit of all live WooCommerce categories vs archive doc content."""
import base64
import json
import re
import urllib.request
from pathlib import Path

LIVE = "https://americacustomboxes.com"
USER = "admin"
APP_PASSWORD = "XFxg 7dCD 7FE9 7K3z W6mN 5FIh"
ROOT = Path(__file__).parent


def api(path: str):
    token = base64.b64encode(f"{USER}:{APP_PASSWORD}".encode()).decode()
    req = urllib.request.Request(
        f"{LIVE}{path}",
        headers={"Authorization": f"Basic {token}"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode())


def classify_desc(desc: str) -> str:
    if not desc or not desc.strip():
        return "empty"
    if "<!--acb-archive-v2-->" in desc:
        return "styled_v2"
    if "acb-archive-v2" in desc or '"intro"' in desc:
        return "partial_json"
    return "plain"


def main() -> None:
    structured_path = ROOT / "acb_archive_structured.json"
    structured = {}
    if structured_path.exists():
        structured = json.loads(structured_path.read_text(encoding="utf-8"))

    cats = api("/wp-json/wc/v3/products/categories?per_page=100")
    by_id = {c["id"]: c for c in cats}

    def parent_name(pid: int) -> str:
        if not pid:
            return "—"
        p = by_id.get(pid)
        return p["name"] if p else f"id:{pid}"

    rows = []
    for c in sorted(cats, key=lambda x: (x.get("parent", 0), x["name"].lower())):
        slug = c["slug"]
        desc = c.get("description") or ""
        kind = classify_desc(desc)
        in_docs = slug in structured
        doc_ready = "yes" if in_docs else ("no" if slug not in structured else "yes")
        product_count = c.get("count", 0)
        rows.append(
            {
                "id": c["id"],
                "name": c["name"],
                "slug": slug,
                "parent": parent_name(c.get("parent", 0)),
                "products": product_count,
                "content": kind,
                "in_4_docs_json": in_docs,
            }
        )

    styled = [r for r in rows if r["content"] == "styled_v2"]
    empty = [r for r in rows if r["content"] == "empty" and r["slug"] not in ("uncategorized",)]
    plain = [r for r in rows if r["content"] == "plain"]
    docs_not_on_live = [s for s in structured if s not in {r["slug"] for r in rows}]

    print("ALL LIVE PRODUCT CATEGORIES\n")
    print(f"{'Slug':<22} {'Name':<24} {'Parent':<14} {'Prods':>5}  {'Content':<12} {'In docs':<8}")
    print("-" * 95)
    for r in rows:
        if r["slug"] in ("uncategorized",):
            continue
        docs = "YES" if r["in_4_docs_json"] else "—"
        print(
            f"{r['slug']:<22} {r['name'][:23]:<24} {r['parent'][:13]:<14} {r['products']:>5}  {r['content']:<12} {docs:<8}"
        )

    print("\n--- SUMMARY ---")
    print(f"Total categories (excl. uncategorized): {len(rows) - 1}")
    print(f"Styled archive content (v2): {len(styled)}")
    print(f"Empty description: {len([r for r in empty if r['slug'] not in ('hot-products', 'by-industry')])}")
    print(f"Plain/other text: {len(plain)}")
    print(f"Doc JSON ready but NO live slug: {len(docs_not_on_live)} -> {', '.join(docs_not_on_live)}")

    print("\n--- STYLED (OK) ---")
    for r in styled:
        print(f"  {r['slug']} ({r['products']} products)")

    print("\n--- EMPTY (needs content) ---")
    skip_parents = {"hot-products", "by-industry"}
    for r in empty:
        if r["slug"] in skip_parents:
            continue
        note = "DOC READY — deploy when mapped" if r["in_4_docs_json"] else "NOT in 4 category docs"
        print(f"  {r['slug']:<22} parent={r['parent']:<12} products={r['products']}  [{note}]")

    if docs_not_on_live:
        print("\n--- IN DOCS BUT NO LIVE CATEGORY ---")
        for s in docs_not_on_live:
            m = structured[s].get("meta", {})
            print(f"  {s}: title={m.get('title', '')[:60]}...")

    out = ROOT / "acb_all_categories_audit.json"
    out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"\nSaved: {out}")


if __name__ == "__main__":
    main()
