#!/usr/bin/env python3
"""Create missing doc-mapped categories on live + deploy all 12 archive contents (no duplication)."""
from __future__ import annotations

import base64
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

LIVE = "https://americacustomboxes.com"
USER = "admin"
APP_PASSWORD = "XFxg 7dCD 7FE9 7K3z W6mN 5FIh"
ROOT = Path(__file__).parent
HOT_PRODUCTS_PARENT = 23

# One live slug per doc category — matches acb_archive_structured.json keys
CREATE_IF_MISSING = {
    "cosmetics": "Cosmetics",
    "food": "Food Boxes",
    "product-boxes": "Product Boxes",
    "pod-boxes": "POD Boxes",
    "pharmaceutical-boxes": "Pharmaceutical Boxes",
}

# By Industry menu slugs — same Batch2 copy as Hot Products siblings
BY_INDUSTRY_ALIAS = {
    "bakery": "bakery-boxes",
    "candles": "candle-boxes",
}


def auth_header() -> dict[str, str]:
    token = base64.b64encode(f"{USER}:{APP_PASSWORD}".encode()).decode()
    return {"Authorization": f"Basic {token}", "Content-Type": "application/json"}


def api(method: str, path: str, payload: dict | None = None) -> dict | list:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{LIVE}{path}", data=data, headers=auth_header(), method=method
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"{method} {path} ({exc.code}): {exc.read().decode()}") from exc


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
            lines.append(f"\t\t'{k}' => '{v.replace(chr(39), chr(92)+chr(39))}',")
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
}}, 20 );"""


def main() -> int:
    structured = json.loads((ROOT / "acb_archive_structured.json").read_text(encoding="utf-8-sig"))
    cats = api("GET", "/wp-json/wc/v3/products/categories?per_page=100")
    live = {c["slug"]: c for c in cats}

    created = []
    for slug, name in CREATE_IF_MISSING.items():
        if slug in live:
            continue
        row = api(
            "POST",
            "/wp-json/wc/v3/products/categories",
            {"name": name, "slug": slug, "parent": HOT_PRODUCTS_PARENT},
        )
        live[slug] = row
        created.append(slug)
        print(f"Created category {slug} id={row['id']}")

    deployed, skipped = [], []
    for slug, data in sorted(structured.items()):
        if slug not in live:
            skipped.append(slug)
            continue
        wrapped = (
            "<!--acb-archive-v2-->"
            + json.dumps(data, ensure_ascii=False, separators=(",", ":"))
            + "<!--/acb-archive-v2-->"
        )
        cat_id = live[slug]["id"]
        api(
            "POST",
            f"/wp-json/wp/v2/product_cat/{cat_id}",
            {
                "description": wrapped,
                "meta": {
                    "wpseo_title": data["meta"]["title"],
                    "wpseo_metadesc": data["meta"]["description"],
                    "wpseo_focuskw": data["meta"]["focuskw"],
                },
            },
        )
        deployed.append(slug)
        print(f"Deployed content+SEO: {slug}")

    for target, source in BY_INDUSTRY_ALIAS.items():
        if source not in structured or target not in live:
            print(f"Skip alias {target} <- {source}")
            continue
        data = structured[source]
        wrapped = (
            "<!--acb-archive-v2-->"
            + json.dumps(data, ensure_ascii=False, separators=(",", ":"))
            + "<!--/acb-archive-v2-->"
        )
        cat_id = live[target]["id"]
        api(
            "POST",
            f"/wp-json/wp/v2/product_cat/{cat_id}",
            {
                "description": wrapped,
                "meta": {
                    "wpseo_title": data["meta"]["title"],
                    "wpseo_metadesc": data["meta"]["description"],
                    "wpseo_focuskw": data["meta"]["focuskw"],
                },
            },
        )
        deployed.append(f"{target}<= {source}")
        print(f"Deployed alias content+SEO: {target} <= {source}")

    seo_structured = dict(structured)
    for target, source in BY_INDUSTRY_ALIAS.items():
        if source in structured:
            seo_structured[target] = structured[source]

    seo16 = api("GET", "/wp-json/code-snippets/v1/snippets/16")
    api(
        "PUT",
        "/wp-json/code-snippets/v1/snippets/16",
        {
            "name": seo16.get("name", "ACB Archive Yoast SEO Meta"),
            "code": build_seo_snippet(seo_structured),
            "scope": "global",
            "active": True,
            "priority": 20,
        },
    )
    print("Updated snippet #16 SEO map")

    try:
        urllib.request.urlopen(f"{LIVE}/?litespeed_purge=all", timeout=30)
    except urllib.error.URLError:
        pass

    report = {
        "created_categories": created,
        "deployed_doc_categories": deployed,
        "skipped": skipped,
        "doc_total": len(structured),
    }
    (ROOT / "acb_fix_status_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if not skipped else 1


if __name__ == "__main__":
    sys.exit(main())
