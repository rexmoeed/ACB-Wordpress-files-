#!/usr/bin/env python3
"""Front-end verify all products: ACF sections visible, Yoast meta in HTML, WC short desc + gallery."""
from __future__ import annotations

import base64
import concurrent.futures
import json
import re
import urllib.request
from pathlib import Path

LIVE = "https://americacustomboxes.com"
USER = "admin"
APP_PASSWORD = "XFxg 7dCD 7FE9 7K3z W6mN 5FIh"
ROOT = Path(__file__).parent


def auth_header() -> dict[str, str]:
    token = base64.b64encode(f"{USER}:{APP_PASSWORD}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def get_json(path: str):
    req = urllib.request.Request(f"{LIVE}{path}", headers=auth_header())
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode())


def fetch_all_products() -> list[dict]:
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


def check_html(slug: str) -> dict:
    url = f"{LIVE}/product/{slug}/"
    req = urllib.request.Request(url, headers={"User-Agent": "ACB-Audit/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception as exc:
        return {"slug": slug, "error": str(exc), "ok": False}

    why = "acb-pc-why-list" in html or "acb-pc-why-item" in html
    faq = "acb-faq-section" in html or "acb-pc-faq" in html
    styles = "acb-pc-style-card" in html or "acb-pc-custom-grid" in html
    m_desc = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', html, re.I)
    desc_ok = bool(m_desc and len(m_desc.group(1).strip()) > 40)
    m_title = re.search(r"<title>([^<]+)</title>", html, re.I)
    title = m_title.group(1).strip() if m_title else ""
    title_ok = len(title) > 10 and "404" not in title
    content_ok = why and faq and styles
    ok = content_ok and desc_ok and title_ok
    return {
        "slug": slug,
        "ok": ok,
        "why": why,
        "faq": faq,
        "styles": styles,
        "meta_desc": desc_ok,
        "title_ok": title_ok,
        "title": title[:100],
        "error": None,
    }


def main() -> None:
    products = fetch_all_products()
    slugs = [p["slug"] for p in products]
    wc_by_slug = {p["slug"]: p for p in products}

    results: list[dict] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        for r in ex.map(check_html, slugs):
            p = wc_by_slug[r["slug"]]
            short = re.sub(r"<[^>]+>", "", p.get("short_description") or "").strip()
            gallery = max(0, len(p.get("images") or []) - 1)
            r["short_desc_ok"] = len(short) >= 40
            r["gallery"] = gallery
            r["gallery_ok"] = gallery >= 3
            r["full_ok"] = r["ok"] and r["short_desc_ok"] and r["gallery_ok"]
            results.append(r)

    full_ok = [r for r in results if r.get("full_ok")]
    bad = [r for r in results if not r.get("full_ok")]

    print(f"TOTAL={len(results)}")
    print(f"FULL_OK={len(full_ok)}")
    print(f"ISSUES={len(bad)}")

    for label, fn in [
        ("no_why_faq_styles", lambda r: not r.get("ok")),
        ("no_short_desc", lambda r: not r.get("short_desc_ok")),
        ("gallery_lt3", lambda r: not r.get("gallery_ok")),
        ("fetch_error", lambda r: r.get("error")),
    ]:
        n = sum(1 for r in results if fn(r))
        print(f"{label}={n}")

    print("\n--- PRODUCTS WITH ISSUES ---")
    for r in sorted(bad, key=lambda x: x["slug"]):
        if r.get("error"):
            print(f"{r['slug']}|error:{r['error'][:60]}")
            continue
        issues = []
        if not r.get("why"):
            issues.append("no_why")
        if not r.get("faq"):
            issues.append("no_faq")
        if not r.get("styles"):
            issues.append("no_styles")
        if not r.get("meta_desc"):
            issues.append("no_meta_desc")
        if not r.get("short_desc_ok"):
            issues.append("short_desc")
        if not r.get("gallery_ok"):
            issues.append(f"gallery={r.get('gallery')}")
        print(f"{r['slug']}|{','.join(issues)}")

    report = {"total": len(results), "full_ok": len(full_ok), "results": results}
    out = ROOT / "acb_live_products_frontend_audit.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nREPORT={out}")


if __name__ == "__main__":
    main()
