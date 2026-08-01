#!/usr/bin/env python3
"""Quick front-end SEO check for all product categories."""
import base64
import concurrent.futures
import json
import re
import urllib.request
from pathlib import Path

LIVE = "https://americacustomboxes.com"
AUTH = {"Authorization": "Basic " + base64.b64encode(b"admin:XFxg 7dCD 7FE9 7K3z W6mN 5FIh").decode()}
ROOT = Path(__file__).parent


def fetch_cats():
    out = []
    page = 1
    while True:
        req = urllib.request.Request(
            f"{LIVE}/wp-json/wc/v3/products/categories?per_page=100&page={page}", headers=AUTH
        )
        batch = json.loads(urllib.request.urlopen(req, timeout=60).read())
        if not batch:
            break
        out.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return out


def check(slug: str) -> dict:
    url = f"{LIVE}/product-category/{slug}/"
    req = urllib.request.Request(url, headers={"User-Agent": "ACB/1.0"})
    try:
        html = urllib.request.urlopen(req, timeout=45).read().decode("utf-8", errors="replace")
    except Exception as exc:
        return {"slug": slug, "ok": False, "error": str(exc)}
    m_t = re.search(r"<title>([^<]+)</title>", html, re.I)
    m_d = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', html, re.I)
    title = m_t.group(1).strip() if m_t else ""
    desc = m_d.group(1).strip() if m_d else ""
    ok = len(title) > 15 and len(desc) > 40
    return {"slug": slug, "ok": ok, "title": title[:90], "desc_len": len(desc), "error": ""}


def main():
    cats = [c for c in fetch_cats() if c["slug"] != "uncategorized"]
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        rows = list(ex.map(lambda c: check(c["slug"]), cats))
    ok = [r for r in rows if r["ok"]]
    bad = [r for r in rows if not r["ok"]]
    print(f"CATEGORIES={len(rows)} SEO_OK={len(ok)} ISSUES={len(bad)}")
    for r in sorted(bad, key=lambda x: x["slug"]):
        print(f"  {r['slug']}: title={r.get('title','')[:60]} desc_len={r.get('desc_len',0)} err={r.get('error')}")
    (ROOT / "acb_category_frontend_seo.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
