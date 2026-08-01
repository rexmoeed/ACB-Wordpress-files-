#!/usr/bin/env python3
"""Audit category archive SEO on live (HTML + structured JSON)."""
import base64
import json
import re
import urllib.request
from pathlib import Path

LIVE = "https://americacustomboxes.com"
USER = "admin"
APP_PASSWORD = "XFxg 7dCD 7FE9 7K3z W6mN 5FIh"
ROOT = Path(__file__).parent

DOC_SLUGS = [
    "tuck-boxes", "bakery-boxes", "candle-boxes", "mailer-boxes", "popcorn-boxes",
    "event-boxes", "pet-boxes", "cosmetics", "food", "product-boxes", "pod-boxes",
    "pharmaceutical-boxes",
]


def auth():
    return {"Authorization": "Basic " + base64.b64encode(f"{USER}:{APP_PASSWORD}".encode()).decode()}


def get(path):
    req = urllib.request.Request(f"{LIVE}{path}", headers=auth())
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def check_url(path: str) -> dict:
    url = LIVE + path
    req = urllib.request.Request(url, headers={"User-Agent": "ACB-SEO-Audit/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        html = r.read().decode("utf-8", errors="replace")
    title = ""
    m = re.search(r"<title>([^<]+)</title>", html, re.I)
    if m:
        title = m.group(1).strip()
    desc = ""
    m = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', html, re.I)
    if m:
        desc = m.group(1).strip()
    # Yoast sometimes uses og:description
    if not desc:
        m = re.search(r'<meta\s+property="og:description"\s+content="([^"]*)"', html, re.I)
        if m:
            desc = m.group(1).strip()
    kw = ""
    m = re.search(r'<meta\s+name="keywords"\s+content="([^"]*)"', html, re.I)
    if m:
        kw = m.group(1).strip()
    has_yoast = "yoast" in html.lower() or "wpseo" in html.lower()
    return {"title": title, "desc": desc, "keywords_meta": kw, "has_yoast": has_yoast}


def main():
    structured = json.loads((ROOT / "acb_archive_structured.json").read_text(encoding="utf-8-sig"))
    cats = get("/wp-json/wc/v3/products/categories?per_page=100")
    by_slug = {c["slug"]: c for c in cats}

    print("slug|expected_title|live_title|desc_ok|focuskw_in_json")
    issues = []
    for slug in DOC_SLUGS:
        if slug not in by_slug:
            issues.append((slug, "no_category"))
            continue
        cat = by_slug[slug]
        parent = by_slug.get(next((c["id"] for c in cats if c["slug"] == "hot-products"), 0))
        # build URL
        if cat.get("parent") == 23:
            path = f"/product-category/hot-products/{slug}/"
        else:
            path = f"/product-category/{slug}/"
        live = check_url(path)
        exp = structured.get(slug, {}).get("meta", {})
        exp_title = exp.get("title", "")
        exp_desc = exp.get("description", "")
        exp_kw = exp.get("focuskw", "")
        title_match = exp_title.lower() in live["title"].lower() or live["title"].lower() in exp_title.lower()
        desc_match = exp_desc[:50].lower() in live["desc"].lower() if live["desc"] and exp_desc else False
        if not title_match or not desc_match or len(live["desc"]) < 30:
            issues.append((slug, live, exp))
        print(
            f"{slug}|{exp_title[:50]}|{live['title'][:50]}|"
            f"{'Y' if desc_match else 'N'}|{exp_kw}"
        )

    print(f"\nISSUES={len(issues)}")
    for item in issues:
        print(item[0], item[1] if len(item) == 2 else "title/desc mismatch")

    # Check snippet 16 exists
    try:
        sn = get("/wp-json/code-snippets/v1/snippets/16")
        print(f"\nSnippet16 active={sn.get('active')} name={sn.get('name')}")
    except Exception as e:
        print("Snippet16:", e)


if __name__ == "__main__":
    main()
