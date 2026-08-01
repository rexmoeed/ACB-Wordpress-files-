#!/usr/bin/env python3
"""Verify all live WooCommerce products: content, ACF sections, SEO meta, gallery."""
from __future__ import annotations

import base64
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

LIVE = "https://americacustomboxes.com"
USER = "admin"
APP_PASSWORD = "XFxg 7dCD 7FE9 7K3z W6mN 5FIh"
ROOT = Path(__file__).parent

ACF_META_KEYS = (
    "acb_why_choose",
    "acb_popular_styles",
    "acb_customization",
    "acb_sustainability",
    "acb_faq",
    "acb_quick_specs",
)
YOAST_KEYS = ("_yoast_wpseo_title", "_yoast_wpseo_metadesc", "_yoast_wpseo_focuskw")


def auth_header() -> dict[str, str]:
    token = base64.b64encode(f"{USER}:{APP_PASSWORD}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def get_json(path: str) -> dict | list:
    req = urllib.request.Request(f"{LIVE}{path}", headers=auth_header())
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode())


def fetch_all_wc_products() -> list[dict]:
    out: list[dict] = []
    page = 1
    while True:
        batch = get_json(f"/wp-json/wc/v3/products?per_page=100&page={page}&status=publish")
        if not batch:
            break
        out.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return out


def meta_map(product_id: int) -> dict[str, str]:
    try:
        row = get_json(f"/wp-json/wp/v2/product/{product_id}?context=edit")
    except urllib.error.HTTPError:
        return {}
    meta = row.get("meta") or {}
    if isinstance(meta, list):
        # Some WP versions return meta as list of {key,value}
        return {m.get("key", ""): m.get("value", "") for m in meta if isinstance(m, dict)}
    return {k: v for k, v in meta.items() if isinstance(v, (str, int, float))}


def has_acf_value(val) -> bool:
    if val is None or val == "" or val == 0:
        return False
    if isinstance(val, str):
        s = val.strip()
        if not s or s in ("0", "a:0:{}", "[]"):
            return False
        if s.startswith("a:") and "i:0" not in s and len(s) < 20:
            return False
        return len(s) > 2
    return bool(val)


def gallery_count(p: dict) -> int:
    imgs = p.get("images") or []
    return max(0, len(imgs) - 1)


def short_desc_ok(p: dict) -> bool:
    t = re.sub(r"<[^>]+>", "", p.get("short_description") or "").strip()
    return len(t) >= 40


def audit_product(p: dict) -> dict:
    pid = p["id"]
    meta = meta_map(pid)
    yoast = {k: (meta.get(k) or "").strip() for k in YOAST_KEYS}
    seo_ok = all(len(yoast[k]) > 0 for k in YOAST_KEYS)
    acf_present = {}
    for key in ACF_META_KEYS:
        acf_present[key] = has_acf_value(meta.get(key))
    acf_core_ok = acf_present["acb_why_choose"] and acf_present["acb_faq"]
    acf_full_ok = all(acf_present.values())
    gc = gallery_count(p)
    return {
        "id": pid,
        "name": p["name"],
        "slug": p["slug"],
        "short_desc_ok": short_desc_ok(p),
        "seo_ok": seo_ok,
        "seo_title": yoast["_yoast_wpseo_title"],
        "acf": acf_present,
        "acf_core_ok": acf_core_ok,
        "acf_full_ok": acf_full_ok,
        "gallery": gc,
        "gallery_ok": gc >= 3,
        "complete": short_desc_ok(p) and seo_ok and acf_core_ok and gc >= 3,
    }


def main() -> None:
    products = fetch_all_wc_products()
    rows = [audit_product(p) for p in products]
    complete = [r for r in rows if r["complete"]]
    incomplete = [r for r in rows if not r["complete"]]

    print(f"TOTAL_PUBLISHED={len(rows)}")
    print(f"COMPLETE={len(complete)}")
    print(f"INCOMPLETE={len(incomplete)}")

    def count_fail(key_fn):
        return sum(1 for r in rows if not key_fn(r))

    print(f"MISSING_SHORT_DESC={count_fail(lambda r: r['short_desc_ok'])}")
    print(f"MISSING_SEO={count_fail(lambda r: r['seo_ok'])}")
    print(f"MISSING_ACF_CORE={count_fail(lambda r: r['acf_core_ok'])}")
    print(f"MISSING_ACF_FULL={count_fail(lambda r: r['acf_full_ok'])}")
    print(f"GALLERY_LT3={count_fail(lambda r: r['gallery_ok'])}")

    print("\n--- INCOMPLETE PRODUCTS ---")
    for r in sorted(incomplete, key=lambda x: x["name"].lower()):
        issues = []
        if not r["short_desc_ok"]:
            issues.append("short_desc")
        if not r["seo_ok"]:
            issues.append("seo")
        if not r["acf_core_ok"]:
            issues.append("acf_core")
        elif not r["acf_full_ok"]:
            issues.append("acf_partial")
        if not r["gallery_ok"]:
            issues.append(f"gallery={r['gallery']}")
        print(f"{r['slug']}|{';'.join(issues)}")

    report = {
        "total": len(rows),
        "complete": len(complete),
        "incomplete": len(incomplete),
        "rows": rows,
    }
    out = ROOT / "acb_live_products_content_audit.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nREPORT={out}")


if __name__ == "__main__":
    main()
