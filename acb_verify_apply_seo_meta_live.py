#!/usr/bin/env python3
"""Verify Yoast meta title/description on live categories + products; apply from Documents folder."""
from __future__ import annotations

import base64
import concurrent.futures
import importlib.util
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
LIVE = "https://americacustomboxes.com"
USER = "admin"
APP_PASSWORD = "XFxg 7dCD 7FE9 7K3z W6mN 5FIh"

DOCS_DIR = Path(r"D:\Downloads\ACB Data\Documents")
PRODUCT_DOCS = [
    DOCS_DIR / "ACB_Product_Copy_Master_Catalog.docx",
    DOCS_DIR / "ACB_Remaining_Products_Catalogue.docx",
    DOCS_DIR / "ACB_Remaining_Products_Catalogue (1).docx",
    DOCS_DIR / "ACB_Remaining_Products_Catalogue (2).docx",
]
CATEGORY_DOCS = [
    DOCS_DIR / "ACB-Category-Pages-Batch1.docx",
    DOCS_DIR / "ACB-Category-Pages-Batch2.docx",
    DOCS_DIR / "ACB-Category-Pages-Batch3.docx",
    DOCS_DIR / "ACB-Category-Pages-Batch4.docx",
]

YOAST_PRODUCT_KEYS = (
    "_yoast_wpseo_title",
    "_yoast_wpseo_metadesc",
    "_yoast_wpseo_focuskw",
)
YOAST_TERM_KEYS = ("wpseo_title", "wpseo_desc", "wpseo_focuskw")


def auth_header(content_json: bool = False) -> dict[str, str]:
    token = base64.b64encode(f"{USER}:{APP_PASSWORD}".encode()).decode()
    h = {"Authorization": f"Basic {token}"}
    if content_json:
        h["Content-Type"] = "application/json"
    return h


def api(method: str, path: str, payload: dict | None = None) -> dict | list:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{LIVE}{path}", data=data, headers=auth_header(content_json=payload is not None), method=method
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body) if body else {}


def meta_dict(raw) -> dict[str, str]:
    if not raw:
        return {}
    if isinstance(raw, list):
        return {str(m.get("key", "")): str(m.get("value") or "") for m in raw if isinstance(m, dict)}
    if isinstance(raw, dict):
        return {str(k): str(v or "") for k, v in raw.items()}
    return {}


def normalize(s: str) -> str:
    import html as html_mod

    s = html_mod.unescape(s or "")
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def load_archive_module():
    spec = importlib.util.spec_from_file_location("acb_parse_archive", ROOT / "acb_parse_and_deploy_archive.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    return mod


def load_product_module():
    spec = importlib.util.spec_from_file_location("acb_import_products", ROOT / "acb_import_products.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    return mod


def parse_category_meta_from_documents(archive_mod, product_mod) -> dict[str, dict]:
    docs: dict[str, list[str]] = {}
    for path in CATEGORY_DOCS:
        if not path.exists():
            continue
        docs[path.name] = product_mod.extract_paragraphs(str(path))
    if not docs:
        structured_path = ROOT / "acb_archive_structured.json"
        return json.loads(structured_path.read_text(encoding="utf-8-sig"))
    return archive_mod.extract_all_categories(docs)


def parse_products_from_documents(product_mod) -> tuple[dict[str, dict], dict[str, dict]]:
    by_name: dict[str, dict] = {}
    by_slug: dict[str, dict] = {}
    for path in PRODUCT_DOCS:
        if not path.exists():
            continue
        for p in product_mod.parse_products_from_doc(str(path)):
            key = normalize(p["name"])
            if key not in by_name:
                by_name[key] = p
            slug = (p.get("slug") or "").strip()
            if slug and slug not in by_slug:
                by_slug[slug] = p
    return by_name, by_slug


def fetch_all_categories() -> list[dict]:
    out: list[dict] = []
    page = 1
    while True:
        batch = api("GET", f"/wp-json/wc/v3/products/categories?per_page=100&page={page}")
        if not batch:
            break
        out.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return out


def fetch_all_products() -> list[dict]:
    out: list[dict] = []
    page = 1
    while True:
        batch = api("GET", f"/wp-json/wc/v3/products?per_page=100&page={page}&status=publish")
        if not batch:
            break
        out.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return out


def fetch_term_yoast(cat_id: int) -> dict[str, str]:
    try:
        row = api("GET", f"/wp-json/wp/v2/product_cat/{cat_id}?context=edit")
    except urllib.error.HTTPError:
        return {}
    meta = meta_dict(row.get("meta"))
    return {k: meta.get(k, "").strip() for k in YOAST_TERM_KEYS}


def scrape_product_seo(slug: str) -> dict[str, str]:
    url = f"{LIVE}/product/{slug}/"
    req = urllib.request.Request(url, headers={"User-Agent": "ACB-SEO-Audit/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception as exc:
        return {"error": str(exc), "title": "", "description": ""}
    m_title = re.search(r"<title>([^<]+)</title>", html, re.I)
    m_desc = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', html, re.I)
    title = (m_title.group(1).strip() if m_title else "").replace(" - America Custom Boxes", "").strip()
    desc = m_desc.group(1).strip() if m_desc else ""
    return {"title": title, "description": desc, "error": ""}


def match_product_to_doc(p: dict, by_name: dict, by_slug: dict, product_mod) -> dict | None:
    fake = {"post_title": p["name"], "post_name": p["slug"]}
    return product_mod.find_doc_for_db_product(fake, by_name, by_slug)


def seo_missing(title: str, desc: str) -> bool:
    return len((title or "").strip()) < 8 or len((desc or "").strip()) < 30


def build_seo_snippet_16(archive_mod, structured: dict) -> str:
    return archive_mod.build_seo_snippet(structured) if hasattr(archive_mod, "build_seo_snippet") else ""


def build_category_term_sync_snippet(structured: dict, option_key: str) -> str:
    payload = {}
    for slug, data in structured.items():
        m = data.get("meta", {})
        payload[slug] = {
            "wpseo_title": m.get("title", ""),
            "wpseo_desc": m.get("description", ""),
            "wpseo_focuskw": m.get("focuskw", ""),
        }
    b64 = base64.b64encode(json.dumps(payload, ensure_ascii=False).encode("utf-8")).decode("ascii")
    return f"""add_action( 'init', static function () {{
\tif ( get_option( '{option_key}' ) ) {{
\t\treturn;
\t}}
\t$raw = base64_decode( '{b64}' );
\t$map = json_decode( $raw, true );
\tif ( ! is_array( $map ) ) {{
\t\treturn;
\t}}
\tforeach ( $map as $slug => $meta ) {{
\t\t$term = get_term_by( 'slug', $slug, 'product_cat' );
\t\tif ( ! $term instanceof WP_Term ) {{
\t\t\tcontinue;
\t\t}}
\t\tforeach ( $meta as $key => $val ) {{
\t\t\tif ( is_string( $val ) && $val !== '' ) {{
\t\t\t\tupdate_term_meta( (int) $term->term_id, $key, $val );
\t\t\t}}
\t\t}}
\t}}
\tupdate_option( '{option_key}', 1, false );
}}, 20 );"""


def build_product_yoast_sync_snippet(product_map: dict[str, dict], option_key: str) -> str:
    """product_map: slug -> {title, description, focuskw}"""
    b64 = base64.b64encode(json.dumps(product_map, ensure_ascii=False).encode("utf-8")).decode("ascii")
    return f"""add_action( 'init', static function () {{
\tif ( get_option( '{option_key}' ) ) {{
\t\treturn;
\t}}
\t$raw = base64_decode( '{b64}' );
\t$map = json_decode( $raw, true );
\tif ( ! is_array( $map ) ) {{
\t\treturn;
\t}}
\tforeach ( $map as $slug => $meta ) {{
\t\t$post = get_page_by_path( $slug, OBJECT, 'product' );
\t\tif ( ! $post instanceof WP_Post ) {{
\t\t\tcontinue;
\t\t}}
\t\t$id = (int) $post->ID;
\t\tif ( ! empty( $meta['title'] ) ) {{
\t\t\tupdate_post_meta( $id, '_yoast_wpseo_title', $meta['title'] );
\t\t}}
\t\tif ( ! empty( $meta['description'] ) ) {{
\t\t\tupdate_post_meta( $id, '_yoast_wpseo_metadesc', $meta['description'] );
\t\t}}
\t\tif ( ! empty( $meta['focuskw'] ) ) {{
\t\t\tupdate_post_meta( $id, '_yoast_wpseo_focuskw', $meta['focuskw'] );
\t\t}}
\t}}
\tupdate_option( '{option_key}', 1, false );
}}, 20 );"""


def upsert_snippet(name: str, code: str, desc: str, priority: int = 21) -> int:
    snippets = api("GET", "/wp-json/code-snippets/v1/snippets?per_page=100")
    existing = next((s for s in snippets if s.get("name") == name), None)
    payload = {
        "name": name,
        "desc": desc,
        "code": code,
        "scope": "global",
        "active": True,
        "priority": priority,
    }
    if existing:
        api("PUT", f"/wp-json/code-snippets/v1/snippets/{existing['id']}", payload)
        return int(existing["id"])
    created = api("POST", "/wp-json/code-snippets/v1/snippets", payload)
    return int(created["id"])


def trigger_front_page() -> None:
    try:
        urllib.request.urlopen(f"{LIVE}/", timeout=30)
    except urllib.error.URLError:
        pass


def main() -> int:
    apply = "--apply" in sys.argv
    product_mod = load_product_module()
    archive_mod = load_archive_module()

    structured = parse_category_meta_from_documents(archive_mod, product_mod)
    (ROOT / "acb_archive_structured.json").write_text(
        json.dumps(structured, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    by_name, by_slug = parse_products_from_documents(product_mod)
    live_cats = fetch_all_categories()
    live_products = fetch_all_products()
    live_cat_by_slug = {c["slug"]: c for c in live_cats}

    cat_audit: list[dict] = []
    cats_to_fix: list[str] = []
    for c in sorted(live_cats, key=lambda x: x["name"].lower()):
        slug = c["slug"]
        if slug == "uncategorized":
            continue
        doc = structured.get(slug)
        yoast = fetch_term_yoast(c["id"])
        live_title = yoast.get("wpseo_title", "")
        live_desc = yoast.get("wpseo_desc", "")
        doc_title = (doc or {}).get("meta", {}).get("title", "") if doc else ""
        doc_desc = (doc or {}).get("meta", {}).get("description", "") if doc else ""
        missing = seo_missing(live_title, live_desc)
        mismatch = doc and (
            (doc_title and live_title and doc_title.strip() != live_title.strip())
            or (doc_desc and live_desc and doc_desc.strip() != live_desc.strip())
        )
        if doc and (missing or mismatch or not live_title or not live_desc):
            cats_to_fix.append(slug)
        cat_audit.append(
            {
                "slug": slug,
                "id": c["id"],
                "has_doc": bool(doc),
                "live_title": live_title,
                "live_desc_len": len(live_desc),
                "doc_title": doc_title,
                "missing_live": missing,
                "needs_apply": slug in cats_to_fix,
            }
        )

    product_audit: list[dict] = []
    products_to_sync: dict[str, dict] = {}
    matched = 0
    no_doc = 0

    def audit_one(p: dict) -> dict:
        doc_p = match_product_to_doc(p, by_name, by_slug, product_mod)
        seo = scrape_product_seo(p["slug"])
        doc_title = (doc_p or {}).get("meta_title", "") if doc_p else ""
        doc_desc = (doc_p or {}).get("meta_description", "") if doc_p else ""
        live_title = seo.get("title", "")
        live_desc = seo.get("description", "")
        missing = seo_missing(live_title, live_desc)
        needs = bool(
            doc_p
            and doc_title
            and doc_desc
            and (
                missing
                or not live_title
                or not live_desc
            )
        )
        return {
            "id": p["id"],
            "slug": p["slug"],
            "name": p["name"],
            "has_doc": bool(doc_p),
            "live_title": live_title[:120],
            "live_desc_len": len(live_desc),
            "doc_title": doc_title[:120],
            "missing_live": missing,
            "needs_apply": needs,
            "doc_p": doc_p,
            "error": seo.get("error", ""),
        }

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
        product_audit = list(ex.map(audit_one, live_products))

    for row in product_audit:
        if row["has_doc"]:
            matched += 1
        else:
            no_doc += 1
        if row["has_doc"] and row.get("doc_p"):
            dp = row["doc_p"]
            products_to_sync[row["slug"]] = {
                "title": dp.get("meta_title", ""),
                "description": dp.get("meta_description", ""),
                "focuskw": dp.get("focus_keyword", ""),
            }

    # Strip doc_p from audit output
    for row in product_audit:
        row.pop("doc_p", None)

    report = {
        "apply_mode": apply,
        "documents_dir": str(DOCS_DIR),
        "categories": {
            "live_total": len(cat_audit),
            "with_doc_meta": sum(1 for r in cat_audit if r["has_doc"]),
            "needs_apply": len(cats_to_fix),
            "missing_live_seo": sum(1 for r in cat_audit if r["missing_live"]),
            "no_doc_source": [r["slug"] for r in cat_audit if not r["has_doc"]],
        },
        "products": {
            "live_total": len(product_audit),
            "matched_doc": matched,
            "no_doc_match": no_doc,
            "needs_apply_front_end": sum(1 for r in product_audit if r["needs_apply"]),
            "yoast_post_meta_sync": len(products_to_sync),
            "missing_live_seo": sum(1 for r in product_audit if r["missing_live"]),
            "no_doc_match_slugs": [r["slug"] for r in product_audit if not r["has_doc"]][:50],
        },
        "category_rows": cat_audit,
        "product_rows": product_audit,
    }

    deploy_result: dict = {}
    if apply:
        # Categories: REST term meta + snippet #16 + one-time term sync v4
        from acb_deploy_category_yoast_meta import build_seo_snippet, build_term_meta_snippet

        rest_ok, rest_fail = [], []
        for slug in structured:
            if slug not in live_cat_by_slug:
                rest_fail.append(slug)
                continue
            m = structured[slug]["meta"]
            cat_id = live_cat_by_slug[slug]["id"]
            meta_payload = {
                "wpseo_title": m.get("title", ""),
                "wpseo_desc": m.get("description", ""),
                "wpseo_focuskw": m.get("focuskw", ""),
            }
            try:
                api("POST", f"/wp-json/wp/v2/product_cat/{cat_id}", {"meta": meta_payload})
                rest_ok.append(slug)
            except urllib.error.HTTPError as exc:
                rest_fail.append(f"{slug}:{exc.code}")

        seo16 = api("GET", "/wp-json/code-snippets/v1/snippets/16")
        api(
            "PUT",
            "/wp-json/code-snippets/v1/snippets/16",
            {
                "name": seo16.get("name", "ACB Archive Yoast SEO Meta"),
                "code": build_seo_snippet(structured),
                "scope": "global",
                "active": True,
                "priority": 20,
            },
        )

        sync_code = build_term_meta_snippet(structured).replace(
            "acb_yoast_terms_synced_v3", "acb_yoast_terms_synced_v4"
        )
        sync_id = upsert_snippet(
            "ACB Yoast Category Term Meta Sync",
            sync_code,
            "One-time wpseo_* term meta from category docs (v4).",
            priority=19,
        )

        # Products: one-time post meta sync
        prod_sync_id = None
        if products_to_sync:
            # Force re-run by new option key each apply batch
            opt = "acb_yoast_products_synced_v2"
            prod_code = build_product_yoast_sync_snippet(products_to_sync, opt)
            prod_sync_id = upsert_snippet(
                "ACB Yoast Product Meta Sync",
                prod_code,
                f"One-time Yoast product meta for {len(products_to_sync)} products from catalog docs.",
                priority=22,
            )

        trigger_front_page()
        try:
            urllib.request.urlopen(f"{LIVE}/product-category/tuck-boxes/", timeout=30)
        except urllib.error.URLError:
            pass

        deploy_result = {
            "category_rest_ok": rest_ok,
            "category_rest_fail": rest_fail,
            "snippet_16_updated": True,
            "category_sync_snippet_id": sync_id,
            "product_sync_count": len(products_to_sync),
            "product_sync_snippet_id": prod_sync_id,
        }
        report["deploy"] = deploy_result

    out_path = ROOT / "acb_seo_meta_verify_report.json"
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print("=== SEO META VERIFY ===")
    print(f"Categories live: {report['categories']['live_total']}")
    print(f"  With doc meta: {report['categories']['with_doc_meta']}")
    print(f"  Missing live SEO: {report['categories']['missing_live_seo']}")
    print(f"  Need apply (doc): {report['categories']['needs_apply']}")
    print(f"Products live: {report['products']['live_total']}")
    print(f"  Matched catalog doc: {report['products']['matched_doc']}")
    print(f"  Yoast DB sync queued (docs): {report['products']['yoast_post_meta_sync']}")
    print(f"  Missing front-end SEO: {report['products']['missing_live_seo']}")
    if apply:
        print("APPLY:", json.dumps(deploy_result, indent=2))
    else:
        print("Dry run only. Re-run with --apply to push meta to live.")
    print(f"Full report: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
