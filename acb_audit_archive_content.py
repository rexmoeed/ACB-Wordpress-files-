#!/usr/bin/env python3
"""Audit live category archive content vs acb_archive_structured.json."""
import base64
import json
import urllib.request
from pathlib import Path

LIVE = "https://americacustomboxes.com"
USER = "admin"
APP_PASSWORD = "XFxg 7dCD 7FE9 7K3z W6mN 5FIh"
ROOT = Path(__file__).parent


def api(path: str) -> list | dict:
    token = base64.b64encode(f"{USER}:{APP_PASSWORD}".encode()).decode()
    req = urllib.request.Request(
        f"{LIVE}{path}",
        headers={"Authorization": f"Basic {token}"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode())


def main() -> None:
    structured = json.loads((ROOT / "acb_archive_structured.json").read_text(encoding="utf-8"))
    doc_slugs = sorted(structured.keys())

    cats = api("/wp-json/wc/v3/products/categories?per_page=100")
    by_slug = {c["slug"]: c for c in cats}

    has_v2 = []
    plain_or_empty = []
    for c in sorted(cats, key=lambda x: (x.get("parent", 0), x["slug"])):
        slug = c["slug"]
        desc = c.get("description") or ""
        if "<!--acb-archive-v2-->" in desc:
            has_v2.append(slug)
        elif slug not in ("uncategorized", "hot-products", "by-industry") and c.get("count", 0) >= 0:
            if desc.strip():
                plain_or_empty.append((slug, "plain_text", len(desc)))
            else:
                plain_or_empty.append((slug, "empty", 0))

    print("=== DOCS: categories in acb_archive_structured.json (12 expected) ===")
    for s in doc_slugs:
        live = "YES" if s in by_slug else "NO LIVE SLUG"
        deployed = "DEPLOYED" if s in has_v2 else "NOT DEPLOYED"
        print(f"  {s:20} live={live:12} {deployed}")

    print("\n=== LIVE: categories WITH styled archive content (v2) ===")
    for s in sorted(has_v2):
        print(f"  + {s}")

    print("\n=== LIVE: product categories MISSING styled content ===")
    skip = {"uncategorized", "hot-products", "by-industry"}
    for slug, kind, n in sorted(plain_or_empty, key=lambda x: x[0]):
        if slug in skip:
            continue
        parent = by_slug[slug].get("parent", 0)
        print(f"  - {slug:25} ({kind}, desc_len={n}, parent_id={parent})")

    print("\n=== DOC categories with NO matching live slug ===")
    for s in doc_slugs:
        if s not in by_slug:
            print(f"  ! {s} (content ready in JSON, needs category or slug map)")

    # Doc slug vs live slug mapping notes
    doc_to_live = {
        "cosmetics": None,
        "food": None,
        "product-boxes": None,
        "pod-boxes": None,
        "pharmaceutical-boxes": None,
    }
    for s in doc_to_live:
        if s in structured and s not in has_v2:
            print(f"\n  Map needed: doc `{s}` -> create or assign live category")


if __name__ == "__main__":
    main()
