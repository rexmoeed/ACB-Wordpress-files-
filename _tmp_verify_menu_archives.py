#!/usr/bin/env python3
import base64
import json
import re
import urllib.request

LIVE = "https://americacustomboxes.com"
USER = "admin"
APP_PASSWORD = "XFxg 7dCD 7FE9 7K3z W6mN 5FIh"

CHECK = [
    ("CBD Boxes", "cbd-boxes", "Hot Products"),
    ("Tuck Boxes", "tuck-boxes", "Hot Products"),
    ("Labels & Stickers", "labels-stickers", "Hot Products"),
    ("Bakery Boxes", "bakery-boxes", "Hot Products"),
    ("Stand-Up Pouches", "stand-up-pouches", "Hot Products"),
    ("Display Boxes", "display-boxes", "Hot Products"),
    ("Kraft Boxes", "kraft-boxes", "Hot Products"),
    ("Mailer Boxes", "mailer-boxes", "Hot Products"),
    ("Candle Boxes", "candle-boxes", "Hot Products"),
    ("Bakery", "bakery", "By Industry"),
    ("Candles", "candles", "By Industry"),
    ("CBD", "cbd", "By Industry"),
]


def main() -> None:
    auth = base64.b64encode(f"{USER}:{APP_PASSWORD}".encode()).decode()
    h = {"Authorization": f"Basic {auth}"}
    cats = json.loads(
        urllib.request.urlopen(
            urllib.request.Request(
                f"{LIVE}/wp-json/wc/v3/products/categories?per_page=100", headers=h
            ),
            timeout=120,
        ).read()
    )
    by_slug = {c["slug"]: c for c in cats}

    ok = []
    missing = []

    print("MENU CATEGORY          SLUG                 ARCHIVE TEXT (product category page)")
    print("-" * 78)
    for label, slug, menu in CHECK:
        c = by_slug.get(slug)
        if not c:
            print(f"{label:22} {slug:20} CATEGORY NOT FOUND")
            missing.append((label, slug, menu, "no category"))
            continue
        desc = c.get("description") or ""
        has_v2 = "<!--acb-archive-v2-->" in desc
        url = f"{LIVE}/product-category/{slug}/"
        html = urllib.request.urlopen(
            urllib.request.Request(
                url, headers={"User-Agent": "acb-verify", "Cache-Control": "no-cache"}
            ),
            timeout=90,
        ).read().decode("utf-8", "replace")
        front = "acb-ar2-intro" in html or "acb-archive-v2" in html

        if has_v2 and front:
            status = "LAGA HUA (intro/FAQ block live)"
            ok.append(slug)
        elif has_v2 and not front:
            status = "WC mein hai, front par nahi dikh raha — check cache/template"
            missing.append((label, slug, menu, status))
        else:
            status = "MISSING — archive text nahi"
            missing.append((label, slug, menu, status))

        print(f"{label:22} {slug:20} {status}  [{menu}]")

    print("\n--- SUMMARY ---")
    print(f"OK ({len(ok)}): {', '.join(ok) if ok else '—'}")
    print(f"Missing / issue ({len(missing)}):")
    for label, slug, menu, reason in missing:
        print(f"  • {label} ({slug}) — {menu} — {reason}")


if __name__ == "__main__":
    main()
