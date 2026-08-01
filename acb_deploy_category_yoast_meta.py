#!/usr/bin/env python3
"""Deploy Yoast term meta for all 12 doc categories + refresh snippet #16 from JSON."""
from __future__ import annotations

import base64
import json
import urllib.error
import urllib.request
from pathlib import Path

LIVE = "https://americacustomboxes.com"
USER = "admin"
APP_PASSWORD = "XFxg 7dCD 7FE9 7K3z W6mN 5FIh"
ROOT = Path(__file__).parent

# Yoast taxonomy term meta (admin UI reads these)
YOAST_TERM_KEYS = {
    "title": "wpseo_title",
    "description": "wpseo_desc",
    "focuskw": "wpseo_focuskw",
}


def auth_header() -> dict[str, str]:
    token = base64.b64encode(f"{USER}:{APP_PASSWORD}".encode()).decode()
    return {"Authorization": f"Basic {token}", "Content-Type": "application/json"}


def api(method: str, path: str, payload: dict | None = None) -> dict | list:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(f"{LIVE}{path}", data=data, headers=auth_header(), method=method)
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body) if body else {}


def build_seo_snippet(structured: dict) -> str:
    titles, descs, kws = {}, {}, {}
    for slug, data in structured.items():
        m = data.get("meta", {})
        if m.get("title"):
            titles[slug] = m["title"]
        if m.get("description"):
            descs[slug] = m["description"]
        if m.get("focuskw"):
            kws[slug] = m["focuskw"]

    def php_array(d: dict[str, str]) -> str:
        lines = ["array("]
        for k, v in sorted(d.items()):
            esc = v.replace("\\", "\\\\").replace("'", "\\'")
            lines.append(f"\t\t'{k}' => '{esc}',")
        lines.append("\t)")
        return "\n".join(lines)

    return f"""add_filter( 'wpseo_title', static function ( $title ) {{
\tif ( ! is_product_taxonomy() ) return $title;
\t$term = get_queried_object();
\tif ( ! $term instanceof WP_Term ) return $title;
\t$map = {php_array(titles)};
\treturn $map[ $term->slug ] ?? $title;
}}, 20 );

add_filter( 'wpseo_metadesc', static function ( $desc ) {{
\tif ( ! is_product_taxonomy() ) return $desc;
\t$term = get_queried_object();
\tif ( ! $term instanceof WP_Term ) return $desc;
\t$map = {php_array(descs)};
\treturn $map[ $term->slug ] ?? $desc;
}}, 20 );

add_filter( 'wpseo_focuskw', static function ( $kw ) {{
\tif ( ! is_product_taxonomy() ) return $kw;
\t$term = get_queried_object();
\tif ( ! $term instanceof WP_Term ) return $kw;
\t$map = {php_array(kws)};
\treturn $map[ $term->slug ] ?? $kw;
}}, 20 );

add_filter( 'wpseo_opengraph_title', static function ( $title ) {{
\tif ( ! is_product_taxonomy() ) return $title;
\t$term = get_queried_object();
\tif ( ! $term instanceof WP_Term ) return $title;
\t$map = {php_array(titles)};
\treturn $map[ $term->slug ] ?? $title;
}}, 20 );

add_filter( 'wpseo_opengraph_desc', static function ( $desc ) {{
\tif ( ! is_product_taxonomy() ) return $desc;
\t$term = get_queried_object();
\tif ( ! $term instanceof WP_Term ) return $desc;
\t$map = {php_array(descs)};
\treturn $map[ $term->slug ] ?? $desc;
}}, 20 );"""


def build_term_meta_snippet(structured: dict) -> str:
    """One-time sync Yoast term meta into wp_termmeta (Yoast admin UI)."""
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
\tif ( get_option( 'acb_yoast_terms_synced_v3' ) ) {{
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
\tupdate_option( 'acb_yoast_terms_synced_v3', 1, false );
}}, 20 );"""


def main() -> int:
    structured = json.loads((ROOT / "acb_archive_structured.json").read_text(encoding="utf-8-sig"))
    cats = api("GET", "/wp-json/wc/v3/products/categories?per_page=100")
    live = {c["slug"]: c for c in cats}

    rest_ok, rest_fail = [], []
    for slug, data in sorted(structured.items()):
        if slug not in live:
            rest_fail.append(slug)
            continue
        m = data["meta"]
        cat_id = live[slug]["id"]
        meta_payload = {
            YOAST_TERM_KEYS["title"]: m.get("title", ""),
            YOAST_TERM_KEYS["description"]: m.get("description", ""),
            YOAST_TERM_KEYS["focuskw"]: m.get("focuskw", ""),
        }
        try:
            api("POST", f"/wp-json/wp/v2/product_cat/{cat_id}", {"meta": meta_payload})
            rest_ok.append(slug)
        except urllib.error.HTTPError as exc:
            rest_fail.append(f"{slug}:REST:{exc.code}")

    # Snippet #16 — front-end Yoast filters
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

    # Snippet #19 — one-time term meta sync for Yoast admin UI
    snippets = api("GET", "/wp-json/code-snippets/v1/snippets?per_page=100")
    existing = next((s for s in snippets if s.get("name") == "ACB Yoast Category Term Meta Sync"), None)
    sync_code = build_term_meta_snippet(structured)
    payload = {
        "name": "ACB Yoast Category Term Meta Sync",
        "desc": "Writes wpseo_title, wpseo_desc, wpseo_focuskw to product_cat term meta (Yoast admin).",
        "code": sync_code,
        "scope": "global",
        "active": True,
        "priority": 19,
    }
    if existing:
        api("PUT", f"/wp-json/code-snippets/v1/snippets/{existing['id']}", payload)
        sync_id = existing["id"]
    else:
        created = api("POST", "/wp-json/code-snippets/v1/snippets", payload)
        sync_id = created["id"]

    # Trigger front-end request to run init hook (load homepage)
    try:
        urllib.request.urlopen(f"{LIVE}/", timeout=30)
    except urllib.error.URLError:
        pass

    try:
        urllib.request.urlopen(f"{LIVE}/?litespeed_purge=all", timeout=30)
    except urllib.error.URLError:
        pass

    report = {
        "rest_meta_updated": rest_ok,
        "rest_or_missing_fail": rest_fail,
        "snippet_16": True,
        "snippet_sync_id": sync_id,
        "categories_in_docs": list(structured.keys()),
    }
    (ROOT / "acb_category_seo_deploy_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
